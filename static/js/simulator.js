document.addEventListener('DOMContentLoaded', function () {
    const startBtn       = document.getElementById('start-btn');
    const resetBtn       = document.getElementById('reset-btn');
    const downloadBtn    = document.getElementById('download-btn');
    const consoleEl      = document.getElementById('console');
    const attemptsEl     = document.getElementById('attempts');
    const simStatusEl    = document.getElementById('sim-status');
    const targetStatusEl = document.getElementById('target-status');
    const attackStatusEl = document.getElementById('attack-status');
    const formErrorEl    = document.getElementById('form-error');
    const summaryPanel   = document.getElementById('summary-panel');
    const summaryGrid    = document.getElementById('summary-grid');
    const reportPanel    = document.getElementById('report-panel');

    const targetAppInput     = document.getElementById('target-app');
    const targetUrlInput     = document.getElementById('target-url');
    const targetAccountInput = document.getElementById('target-account');

    let isRunning = false;
    let currentAttemptCard = null;

    startBtn.addEventListener('click', startSimulation);
    resetBtn.addEventListener('click', resetSimulator);
    downloadBtn.addEventListener('click', downloadReport);

    /* ── validation ── */

    function validateUrl(url) {
        try {
            const p = new URL(url);
            if (p.hostname !== '127.0.0.1' && p.hostname !== 'localhost')
                return 'Only 127.0.0.1 or localhost are permitted';
            if (parseInt(p.port, 10) !== 5000)
                return 'Only port 5000 is permitted';
            return null;
        } catch (e) { return 'Invalid URL format'; }
    }

    function validateEmail(email) {
        return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
    }

    /* ── start simulation ── */

    function startSimulation() {
        if (isRunning) return;
        formErrorEl.textContent = '';

        const app  = targetAppInput.value.trim();
        const url  = targetUrlInput.value.trim();
        const acct = targetAccountInput.value.trim();

        if (!app || !url || !acct) {
            formErrorEl.textContent = 'All target configuration fields are required.';
            return;
        }
        if (!validateEmail(acct)) {
            formErrorEl.textContent = 'Please enter a valid email address for the target account.';
            return;
        }
        const urlErr = validateUrl(url);
        if (urlErr) { formErrorEl.textContent = urlErr; return; }

        isRunning = true;
        startBtn.disabled = true;
        setInputState(true);
        summaryPanel.style.display = 'none';
        reportPanel.style.display  = 'none';
        consoleEl.innerHTML = '';
        currentAttemptCard = null;

        simStatusEl.textContent    = 'RUNNING';
        simStatusEl.className      = 'card-value status-running';
        attackStatusEl.textContent = 'RUNNING';
        attackStatusEl.style.color = '#ffaa00';

        appendLine('SIMULATION STARTED', 'heading');
        appendLine('Initializing authorized local simulation...', 'info');
        appendLine('Preparing controlled login attempt...', 'info');

        fetch('/api/start', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ target_app: app, target_url: url, target_email: acct })
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(err => { throw new Error(err.error || 'Server error'); });
            }
            const reader  = response.body.getReader();
            const decoder = new TextDecoder();
            function read() {
                reader.read().then(({ done, value }) => {
                    if (done) { finishSimulation(); return; }
                    decoder.decode(value).split('\n').forEach(line => {
                        if (line.startsWith('data: ')) {
                            try { handleEvent(JSON.parse(line.substring(6))); }
                            catch (e) { /* ignore */ }
                        }
                    });
                    read();
                });
            }
            read();
        })
        .catch(error => {
            appendLine(`ERROR: ${error.message}`, 'error');
            finishSimulation();
        });
    }

    /* ── event router ── */

    function handleEvent(ev) {
        switch (ev.type) {
            case 'PRECHECK_LOCKED':      renderPrecheckLocked(ev.data);   break;
            case 'PRE_SIMULATION_STATE': renderPreSimState(ev.data);      break;
            case 'ATTEMPT_PREPARING':    renderPreparing(ev.attempt);     break;
            case 'ATTEMPT_SENDING':      renderSending(ev.attempt);       break;
            case 'ATTEMPT_ANALYZING':    renderAnalyzing(ev.attempt);     break;
            case 'ATTEMPT_RESULT':       renderResult(ev.data);           break;
            case 'ATTEMPT_WAITING':      renderWaiting(ev);               break;
            case 'SIMULATION_SUMMARY':   renderSummary(ev);               break;
        }
    }

    /* ── pre-check: account already locked ── */

    function renderPrecheckLocked(d) {
        appendLine('', '');
        const block = document.createElement('div');
        block.className = 'attempt-block precheck-block';
        block.innerHTML = `
            <div class="attempt-header locked-heading">PRE-EXISTING ACCOUNT LOCK DETECTED</div>
            <div class="attempt-sep">${'\u2500'.repeat(40)}</div>
            <div class="attempt-row"><span class="ak">Target Account</span><span class="av">${esc(d.target_account)}</span></div>
            <div class="attempt-row"><span class="ak">Account State</span><span class="av state-locked">ALREADY LOCKED</span></div>
            <div class="attempt-row"><span class="ak">Simulation State</span><span class="av state-stopped">STOPPED</span></div>
            <div class="attempt-result">
                <div class="result-label">Message:</div>
                <div class="result-text">${esc(d.message)}</div>
            </div>
            <div class="attempt-result">
                <div class="result-label">Simulation cannot continue until the account becomes available.</div>
            </div>
            <div class="attempt-row"><span class="ak">Attempts Executed</span><span class="av">0</span></div>
        `;
        consoleEl.appendChild(block);
        scrollToBottom();
        targetStatusEl.textContent = 'LOCKED';
        targetStatusEl.style.color = '#ff3366';
        attackStatusEl.textContent = 'COMPLETED';
        attackStatusEl.style.color = '#ff3366';
    }

    /* ── pre-simulation state warning ── */

    function renderPreSimState(d) {
        appendLine('', '');
        const block = document.createElement('div');
        block.className = 'attempt-block presim-block';
        block.innerHTML = `
            <div class="attempt-header presim-heading">PRE-SIMULATION ACCOUNT STATE</div>
            <div class="attempt-sep">${'\u2500'.repeat(40)}</div>
            <div class="attempt-row"><span class="ak">Account State</span><span class="av state-active">ACTIVE</span></div>
            <div class="attempt-row"><span class="ak">Previous Consecutive Failed Attempts</span><span class="av warn-value">${d.previous_failed_attempts}</span></div>
            <div class="attempt-result">
                <div class="result-label">Warning:</div>
                <div class="result-text warn-text">${esc(d.warning)}</div>
            </div>
        `;
        consoleEl.appendChild(block);
        scrollToBottom();
    }

    /* ── Phase 1: PREPARING ── */

    function renderPreparing(num) {
        attemptsEl.textContent = `${num} / 3`;
        appendLine('', '');
        appendLine('\u2500'.repeat(40), 'sep');
        appendLine(`ATTEMPT ${num} / 3`, 'heading');
        appendLine('\u2500'.repeat(40), 'sep');
        appendLine('Preparing attempt...', 'preparing');

        const card = document.createElement('div');
        card.className = 'attempt-block attempt-phase';
        card.id = `attempt-card-${num}`;
        card.innerHTML = `
            <div class="attempt-header">ATTEMPT ${num} / 3</div>
            <div class="attempt-sep">${'\u2500'.repeat(40)}</div>
            <div class="phase-msg preparing-msg">Preparing attempt\u2026</div>
        `;
        consoleEl.appendChild(card);
        currentAttemptCard = card;
        scrollToBottom();
    }

    /* ── Phase 2: SENDING ── */

    function renderSending(num) {
        appendLine('Sending controlled login request...', 'sending');
        if (currentAttemptCard) {
            currentAttemptCard.className = 'attempt-block attempt-sending';
            currentAttemptCard.querySelector('.phase-msg').className = 'phase-msg sending-msg';
            currentAttemptCard.querySelector('.phase-msg').textContent =
                'Sending controlled login request\u2026';
        }
        scrollToBottom();
    }

    /* ── Phase 3: ANALYZING ── */

    function renderAnalyzing(num) {
        appendLine('Response received.', 'info');
        appendLine('Analyzing response...', 'analyzing');
        if (currentAttemptCard) {
            currentAttemptCard.className = 'attempt-block attempt-analyzing';
            currentAttemptCard.querySelector('.phase-msg').className = 'phase-msg analyzing-msg';
            currentAttemptCard.querySelector('.phase-msg').textContent =
                'Response received. Analyzing response\u2026';
        }
        scrollToBottom();
    }

    /* ── Phase 4: RESULT (full detail card) ── */

    function renderResult(d) {
        if (d.account_state === 'LOCKED') {
            targetStatusEl.textContent = 'LOCKED';
            targetStatusEl.style.color = '#ff3366';
            attackStatusEl.textContent = 'COMPLETED';
            attackStatusEl.style.color = '#ff3366';
        } else if (d.simulation_state === 'STOPPED') {
            attackStatusEl.textContent = 'COMPLETED';
            attackStatusEl.style.color = '#00ff88';
        }

        const sc = d.account_state === 'LOCKED' ? 'locked'
                 : d.simulation_state === 'STOPPED' ? 'stopped'
                 : 'active';

        const resultLines = d.result.split('\n').map(l => esc(l)).join('<br>');

        const fullHtml = `
            <div class="attempt-header">ATTEMPT ${d.attempt} / 3</div>
            <div class="attempt-sep">${'\u2500'.repeat(40)}</div>
            <div class="attempt-row"><span class="ak">Timestamp</span><span class="av">${esc(d.timestamp)}</span></div>
            <div class="attempt-row"><span class="ak">Target</span><span class="av">${esc(d.target_app)}</span></div>
            <div class="attempt-row"><span class="ak">Target URL</span><span class="av">${esc(d.target_url)}</span></div>
            <div class="attempt-row"><span class="ak">Target Account</span><span class="av">${esc(d.target_account)}</span></div>
            <div class="attempt-row"><span class="ak">Request Method</span><span class="av">${d.http_method}</span></div>
            <div class="attempt-row"><span class="ak">HTTP Status</span><span class="av">${d.http_status}</span></div>
            <div class="attempt-row"><span class="ak">Response Time</span><span class="av">${d.response_time_ms} ms</span></div>
            <div class="attempt-row"><span class="ak">Credential Result</span><span class="av result-invalid">INVALID</span></div>
            <div class="attempt-row"><span class="ak">Account State</span><span class="av state-${sc}">${d.account_state}</span></div>
            <div class="attempt-row"><span class="ak">Simulation State</span><span class="av">${d.simulation_state}</span></div>
            <div class="attempt-result">
                <div class="result-label">Result:</div>
                <div class="result-text">${resultLines}</div>
            </div>
            <div class="attempt-next">
                <div class="result-label">Next Action:</div>
                <div class="result-text">${esc(d.next_action)}</div>
            </div>
        `;

        if (currentAttemptCard) {
            currentAttemptCard.className = 'attempt-block';
            currentAttemptCard.innerHTML = fullHtml;
        } else {
            const b = document.createElement('div');
            b.className = 'attempt-block';
            b.innerHTML = fullHtml;
            consoleEl.appendChild(b);
        }
        currentAttemptCard = null;
        scrollToBottom();
    }

    /* ── Phase 5: WAITING between attempts ── */

    function renderWaiting(ev) {
        appendLine(
            `Waiting before next controlled attempt...`,
            'waiting'
        );
        scrollToBottom();
    }

    /* ── simulation summary ── */

    function renderSummary(s) {
        appendLine('', '');
        appendLine('SIMULATION COMPLETE', 'heading');

        summaryPanel.style.display = 'block';
        reportPanel.style.display  = 'block';

        const preFail = s.pre_sim_previous_failures;
        const lockAtt = s.lockout_on_attempt;

        const rows = [
            ['Account State Before Simulation', s.pre_sim_account_state || 'N/A'],
            ['Previous Failed Attempts',
             preFail !== undefined && preFail !== null ? String(preFail) : '0'],
            ['Simulation Start Time', s.start_time],
            ['Simulation End Time',   s.end_time],
            ['Duration',              s.duration],
            ['Simulator Attempts Executed', String(s.attempts_executed)],
            ['Failed Attempts',       String(s.failed_attempts)],
            ['Lockout Observed On Attempt', lockAtt ? String(lockAtt) : 'N/A'],
            ['Target Application',    s.target_app],
            ['Target URL',            s.target_url],
            ['Target Account',        s.target_account],
            ['Final Account State',   s.final_account_state],
            ['Simulation Status',     s.simulation_status],
        ];

        summaryGrid.innerHTML = rows.map(([k, v]) =>
            `<div class="summary-row"><span class="sk">${k}</span><span class="sv">${esc(String(v))}</span></div>`
        ).join('');

        scrollToBottom();
    }

    /* ── PDF download ── */
    function downloadReport() { window.open('/api/download-report', '_blank'); }

    /* ── utilities ── */

    function appendLine(text, cls) {
        const d = document.createElement('div');
        d.className = `console-line ${cls || ''}`;
        d.textContent = text;
        consoleEl.appendChild(d);
        scrollToBottom();
    }
    function scrollToBottom() { consoleEl.scrollTop = consoleEl.scrollHeight; }
    function esc(s) { const d = document.createElement('div'); d.textContent = s; return d.innerHTML; }

    function finishSimulation() {
        isRunning = false;
        simStatusEl.textContent = 'STOPPED';
        simStatusEl.className   = 'card-value status-stopped';
        if (attackStatusEl.textContent !== 'COMPLETED') {
            attackStatusEl.textContent = 'COMPLETED';
            attackStatusEl.style.color = '#00ff88';
        }
    }

    function setInputState(dis) {
        targetAppInput.disabled = dis;
        targetUrlInput.disabled = dis;
        targetAccountInput.disabled = dis;
    }

    function resetSimulator() {
        if (isRunning) return;
        consoleEl.innerHTML = '<div class="console-line">Awaiting simulation start...</div>';
        formErrorEl.textContent = '';
        attemptsEl.textContent  = '0 / 3';
        simStatusEl.textContent = 'READY';
        simStatusEl.className   = 'card-value status-ready';
        targetStatusEl.textContent = 'AVAILABLE';
        targetStatusEl.style.color = '#00d4ff';
        attackStatusEl.textContent = 'NOT STARTED';
        attackStatusEl.style.color = '#00d4ff';
        summaryPanel.style.display = 'none';
        reportPanel.style.display  = 'none';
        summaryGrid.innerHTML      = '';
        currentAttemptCard         = null;
        startBtn.disabled = false;
        setInputState(false);
    }
});
