from flask import Flask, render_template, jsonify, Response, request, send_file
import json
import re
import io
from simulator import (
    run_simulation,
    validate_target,
    generate_pdf_report,
    save_pdf_report,
    MAX_ATTEMPTS,
)

app = Flask(__name__)

# Stores the most recently completed simulation results
_last_simulation = None


@app.route("/")
def index():
    """Render the simulator dashboard."""
    return render_template("index.html", max_attempts=MAX_ATTEMPTS)


@app.route("/api/config")
def get_config():
    """Return hard-coded safety configuration."""
    return jsonify(
        {
            "max_attempts": MAX_ATTEMPTS,
            "attack_type": "Brute Force Login Simulation",
            "allowed_hosts": ["127.0.0.1", "localhost"],
            "allowed_port": 5000,
        }
    )


@app.route("/api/start", methods=["POST"])
def start_simulation():
    """Start the brute force simulation.

    Expects JSON body:
        target_app   - display name of the target application
        target_url   - full URL of the login endpoint (validated server-side)
        target_email - account email to test against
    """
    global _last_simulation

    data = request.get_json(force=True)
    target_app = (data.get("target_app") or "").strip()
    target_url = (data.get("target_url") or "").strip()
    target_email = (data.get("target_email") or "").strip()

    # Reject missing fields
    if not target_url or not target_email or not target_app:
        return (
            jsonify({"error": "target_app, target_url and target_email are required"}),
            400,
        )

    # Email format validation
    if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", target_email):
        return jsonify({"error": "Invalid email format for target account"}), 400

    # Server-side URL allowlist enforcement
    try:
        validate_target(target_url)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 403

    # Clear previous results before new run
    _last_simulation = None

    def generate():
        global _last_simulation
        for event in run_simulation(target_url, target_app, target_email):
            yield f"data: {json.dumps(event)}\n\n"
        # After generator completes, store the summary for PDF generation
        _last_simulation = run_simulation._last_summary

    return Response(
        generate(),
        mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.route("/api/download-report", methods=["GET"])
def download_report():
    """Generate the PDF report, save a permanent copy, and serve the download."""
    if not _last_simulation:
        return jsonify({"error": "No completed simulation results available"}), 404

    try:
        pdf_bytes = generate_pdf_report(_last_simulation)
    except Exception as exc:
        return jsonify({"error": f"PDF generation failed: {str(exc)}"}), 500

    # Save a permanent copy to the project reports/ folder
    target_email = _last_simulation.get("target_account", "unknown")
    try:
        saved_path = save_pdf_report(pdf_bytes, target_email)
    except Exception:
        # Saving failure should not block the download
        saved_path = None

    # Return the PDF to the browser
    download_name = "brute_force_simulation_report.pdf"
    return send_file(
        io.BytesIO(pdf_bytes),
        mimetype="application/pdf",
        as_attachment=True,
        download_name=download_name,
    )


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=7000, debug=True)
