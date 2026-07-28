import os
import re
import time
import io
import requests
from datetime import datetime
from urllib.parse import urlparse
import pytz
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

# ──────────────────────────────────────────────
# Timezone — Indian Standard Time
# ──────────────────────────────────────────────
IST = pytz.timezone("Asia/Kolkata")
TS_DISPLAY = "%d %b %Y, %I:%M:%S %p IST"
TS_FILENAME = "%Y-%m-%d_%H%M%S"

# ──────────────────────────────────────────────
# Safety constants
# ──────────────────────────────────────────────
ALLOWED_HOSTS = {"127.0.0.1", "localhost"}
ALLOWED_PORT = 5000
MAX_ATTEMPTS = 3

# Visual pacing delays (seconds)
DELAY_PREPARING = 1.0     # "Preparing attempt..." visible time
DELAY_ANALYZING = 1.0     # "Response received. Analyzing..." visible time
DELAY_BETWEEN = 2.0       # "Waiting before next attempt..." time

# Deliberately incorrect test passwords — never use or store the real password
TEST_PASSWORDS = ["wrongpass1", "wrongpass2", "wrongpass3"]


# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────

def _now_ist():
    return datetime.now(IST)


def _format_ist(dt):
    return dt.strftime(TS_DISPLAY)


def validate_target(target_url):
    """Validate the target URL against the hard-coded allowlist."""
    parsed = urlparse(target_url)
    hostname = parsed.hostname or ""
    port = parsed.port
    if hostname not in ALLOWED_HOSTS:
        raise ValueError(
            f"Blocked: hostname '{hostname}' is not in the allowlist "
            "(127.0.0.1 / localhost only)"
        )
    if port != ALLOWED_PORT:
        raise ValueError(
            f"Blocked: port {port} is not allowed (only port {ALLOWED_PORT})"
        )


def _determine_account_state(response_text):
    """Returns LOCKED if response indicates lockout, else ACTIVE."""
    text = response_text.lower()
    if "locked" in text or "temporarily" in text:
        return "LOCKED"
    return "ACTIVE"


# ──────────────────────────────────────────────
# Simulation
# ──────────────────────────────────────────────

def run_simulation(target_url, target_app, target_email):
    """Run controlled brute force simulation with phased visual pacing.

    Event types yielded (in order):
        ATTEMPT_PREPARING      — heading shown, "Preparing attempt..."
        ATTEMPT_SENDING        — "Sending controlled login request..."
        ATTEMPT_ANALYZING      — "Response received. Analyzing..."
        ATTEMPT_RESULT         — full detail card
        ATTEMPT_WAITING        — "Waiting before next controlled attempt..."
        SIMULATION_SUMMARY     — final summary
    """
    validate_target(target_url)
    start_time = _now_ist()
    attempts = []
    final_state = "ACTIVE"
    lockout_on_attempt = None
    pre_sim_account_state = "ACTIVE"
    pre_sim_previous_failures = 0

    # ══════════════════════════════════════════
    # MAIN ATTEMPT LOOP
    # ══════════════════════════════════════════
    for i in range(MAX_ATTEMPTS):
        attempt_num = i + 1

        # ── Phase 1: PREPARING ──
        yield {
            "type": "ATTEMPT_PREPARING",
            "attempt": attempt_num,
        }
        time.sleep(DELAY_PREPARING)

        # ── Phase 2: SENDING ──
        yield {
            "type": "ATTEMPT_SENDING",
            "attempt": attempt_num,
        }

        # The actual HTTP request happens HERE — not before, not during delays
        attempt_ts = _format_ist(_now_ist())
        t0 = time.time()
        try:
            response = requests.post(
                target_url,
                data={"email": target_email, "password": TEST_PASSWORDS[i]},
                timeout=5,
            )
            elapsed_ms = round((time.time() - t0) * 1000, 2)
            http_status = response.status_code
            account_state = _determine_account_state(response.text)
            is_locked = account_state == "LOCKED"
        except requests.exceptions.ConnectionError:
            elapsed_ms = round((time.time() - t0) * 1000, 2)
            http_status = None
            account_state = "UNKNOWN"
            is_locked = False
        except Exception:
            elapsed_ms = round((time.time() - t0) * 1000, 2)
            http_status = None
            account_state = "UNKNOWN"
            is_locked = False

        # ── Phase 3: ANALYZING ──
        yield {
            "type": "ATTEMPT_ANALYZING",
            "attempt": attempt_num,
        }
        time.sleep(DELAY_ANALYZING)

        # ── Phase 4: RESULT ──
        if is_locked:
            sim_state = "STOPPED"
            final_state = "LOCKED"
            lockout_on_attempt = attempt_num
        elif attempt_num == MAX_ATTEMPTS:
            sim_state = "STOPPED"
        else:
            sim_state = "CONTINUING"

        # Build human-readable result
        if is_locked:
            result_text = (
                f"Target application activated account lockout during "
                f"simulator Attempt {attempt_num}."
            )
            if pre_sim_previous_failures > 0:
                result_text += (
                    f"\nPrevious Failed Attempts Before Simulation: "
                    f"{pre_sim_previous_failures}"
                    f"\nFailed Attempts Sent During Current Simulation: "
                    f"{attempt_num}"
                    f"\nObserved Consecutive Failure Total: "
                    f"{pre_sim_previous_failures + attempt_num}"
                )
        elif http_status is not None:
            result_text = "Login attempt rejected by target application."
        else:
            result_text = "Connection to target failed."

        if is_locked or attempt_num == MAX_ATTEMPTS:
            next_action = (
                "Target account is locked. No further requests will be sent."
                if is_locked else
                "Maximum controlled attempts reached. "
                "No further requests will be sent."
            )
        else:
            next_action = (
                f"Preparing controlled attempt "
                f"{attempt_num + 1}/{MAX_ATTEMPTS}..."
            )

        record = {
            "attempt": attempt_num,
            "timestamp": attempt_ts,
            "target_app": target_app,
            "target_url": target_url,
            "target_account": target_email,
            "http_method": "POST",
            "http_status": http_status if http_status is not None else "N/A",
            "response_time_ms": elapsed_ms,
            "credential_result": "INVALID",
            "account_state": account_state,
            "simulation_state": sim_state,
            "result": result_text,
            "next_action": next_action,
        }
        attempts.append(record)

        yield {
            "type": "ATTEMPT_RESULT",
            "data": record,
        }

        if is_locked:
            break

        # ── Phase 5: WAITING (between attempts) ──
        if attempt_num < MAX_ATTEMPTS:
            yield {
                "type": "ATTEMPT_WAITING",
                "attempt": attempt_num,
                "next_attempt": attempt_num + 1,
            }
            time.sleep(DELAY_BETWEEN)

    # ══════════════════════════════════════════
    # SUMMARY
    # ══════════════════════════════════════════
    end_time = _now_ist()
    duration = end_time - start_time

    summary = {
        "type": "SIMULATION_SUMMARY",
        "start_time": _format_ist(start_time),
        "end_time": _format_ist(end_time),
        "duration": str(duration).split(".")[0],
        "attempts_executed": len(attempts),
        "failed_attempts": len(attempts),
        "target_app": target_app,
        "target_url": target_url,
        "target_account": target_email,
        "final_account_state": final_state,
        "simulation_status": "COMPLETED",
        "attempts": attempts,
        "pre_sim_account_state": pre_sim_account_state,
        "pre_sim_previous_failures": pre_sim_previous_failures,
        "lockout_on_attempt": lockout_on_attempt,
    }

    run_simulation._last_summary = summary
    yield summary


# ──────────────────────────────────────────────
# PDF Report Generation
# ──────────────────────────────────────────────

def _sanitize_email(email):
    return re.sub(r'[^a-zA-Z0-9]', '_', email)


def get_reports_dir():
    project_dir = os.path.dirname(os.path.abspath(__file__))
    reports_dir = os.path.join(project_dir, "reports")
    os.makedirs(reports_dir, exist_ok=True)
    return reports_dir


def generate_report_filename(target_email):
    safe_email = _sanitize_email(target_email)
    ts = _now_ist().strftime(TS_FILENAME)
    return f"brute_force_report_{safe_email}_{ts}_IST.pdf"


def generate_pdf_report(summary):
    """Generate a PDF report from completed simulation results."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=letter,
        rightMargin=0.75 * inch, leftMargin=0.75 * inch,
        topMargin=0.75 * inch, bottomMargin=0.75 * inch,
    )
    styles = getSampleStyleSheet()
    elements = []

    title_style = ParagraphStyle(
        "ReportTitle", parent=styles["Title"],
        fontSize=18, spaceAfter=6, alignment=1,
    )
    subtitle_style = ParagraphStyle(
        "Subtitle", parent=styles["Normal"],
        fontSize=10, textColor=colors.HexColor("#666666"),
        alignment=1, spaceAfter=20,
    )
    section_style = ParagraphStyle(
        "SectionHead", parent=styles["Heading2"],
        fontSize=13, textColor=colors.HexColor("#005577"),
        spaceBefore=18, spaceAfter=8,
    )
    body_style = styles["Normal"]

    elements.append(Paragraph("BRUTE FORCE SIMULATION REPORT", title_style))
    elements.append(Paragraph(
        f"Generated: {_format_ist(_now_ist())}", subtitle_style
    ))
    elements.append(Spacer(1, 0.25 * inch))

    # Section 1 — Simulation Information
    elements.append(Paragraph(
        "Section 1 &mdash; Simulation Information", section_style
    ))
    info_data = [
        ["Target Application", summary["target_app"]],
        ["Target URL", summary["target_url"]],
        ["Target Account", summary["target_account"]],
        ["Start Time", summary["start_time"]],
        ["End Time", summary["end_time"]],
        ["Duration", summary["duration"]],
        ["Maximum Allowed Attempts", str(MAX_ATTEMPTS)],
        ["Attempts Executed", str(summary["attempts_executed"])],
    ]
    elements.append(_make_table(info_data, [2.2 * inch, 4.3 * inch]))

    # Section 2 — Attempt Details
    elements.append(Paragraph(
        "Section 2 &mdash; Attempt Details", section_style
    ))
    for att in summary["attempts"]:
        elements.append(Paragraph(
            f"<b>Attempt {att['attempt']} / {MAX_ATTEMPTS}</b>", body_style
        ))
        att_data = [
            ["Timestamp", att["timestamp"]],
            ["HTTP Method", att["http_method"]],
            ["HTTP Status", str(att["http_status"])],
            ["Response Time", f"{att['response_time_ms']} ms"],
            ["Credential Result", att["credential_result"]],
            ["Account State", att["account_state"]],
            ["Simulation State", att["simulation_state"]],
            ["Result", att["result"].replace("\n", "<br/>")],
        ]
        elements.append(_make_table(att_data, [1.8 * inch, 4.7 * inch]))
        elements.append(Spacer(1, 0.15 * inch))

    if not summary["attempts"]:
        elements.append(Paragraph(
            "<i>No attempts were executed (account was already locked).</i>",
            body_style,
        ))
        elements.append(Spacer(1, 0.15 * inch))

    # Section 3 — Final Summary (includes pre-simulation state)
    elements.append(Paragraph(
        "Section 3 &mdash; Final Summary", section_style
    ))
    pre_fail = summary.get("pre_sim_previous_failures", 0)
    lock_attempt = summary.get("lockout_on_attempt")
    summary_data = [
        ["Account State Before Simulation",
         str(summary.get("pre_sim_account_state", "N/A"))],
        ["Previous Failed Attempts",
         str(pre_fail) if pre_fail != "N/A" else "N/A"],
        ["Simulator Attempts Executed", str(summary["attempts_executed"])],
        ["Failed Attempts", str(summary["failed_attempts"])],
        ["Lockout Observed On Attempt",
         str(lock_attempt) if lock_attempt else "N/A"],
        ["Final Account State", summary["final_account_state"]],
        ["Simulation Status", summary["simulation_status"]],
    ]
    elements.append(_make_table(summary_data, [2.2 * inch, 4.3 * inch]))

    # Section 4 — Safety Statement
    elements.append(Spacer(1, 0.3 * inch))
    elements.append(Paragraph(
        "Section 4 &mdash; Safety Statement", section_style
    ))
    elements.append(Paragraph(
        "This report was generated by the Brute Force Simulator for an "
        "authorized local cybersecurity testing environment.",
        body_style,
    ))

    doc.build(elements)
    return buf.getvalue()


def save_pdf_report(pdf_bytes, target_email):
    reports_dir = get_reports_dir()
    filename = generate_report_filename(target_email)
    filepath = os.path.join(reports_dir, filename)
    with open(filepath, "wb") as f:
        f.write(pdf_bytes)
    return filepath


def _make_table(data, col_widths=None):
    table = Table(data, colWidths=col_widths)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#e8f0f8")),
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#1a1a1a")),
        ("FONTNAME", (0, 0), (-1, -1), "Courier"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1),
         [colors.white, colors.HexColor("#f5f9fc")]),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ]))
    return table
