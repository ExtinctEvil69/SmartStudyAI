/* ═══════════════════════════════════════════════════════════════════════════
   BrahmaVidya — Frontend Application
   ═══════════════════════════════════════════════════════════════════════════ */

// ── State ────────────────────────────────────────────────────────────────
const state = {
    currentTool: 'dashboard',
    neuroreadContent: '',
    edutubeTranscript: '',
    quizData: null,
    quizAnswers: {},
};

// ── Init ─────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    checkHealth();
    loadDashboard();
    mermaid.initialize({ startOnLoad: false, theme: 'dark', themeVariables: {
        darkMode: true, background: '#14141E', primaryColor: '#7C6CFF',
        primaryTextColor: '#E8E8F0', lineColor: '#6B6B82',
    }});
});

// ── Navigation ───────────────────────────────────────────────────────────
function switchTool(tool) {
    state.currentTool = tool;
    document.querySelectorAll('.tool-page').forEach(p => p.classList.remove('active'));
    document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));

    // Generic tools use the shared #page-generic shell, configured at runtime.
    let pageId = tool;
    if (tool.startsWith('generic:')) {
        pageId = 'generic';
        const toolId = tool.split(':')[1];
        renderGenericPage(toolId);
    }

    const page = document.getElementById(`page-${pageId}`);
    const nav = document.querySelector(`.nav-item[data-tool="${tool}"]`);
    if (page) page.classList.add('active');
    if (nav) nav.classList.add('active');
    document.querySelector('.sidebar').classList.remove('open');
    if (tool === 'dashboard') loadDashboard();
}

// ── Health Check ─────────────────────────────────────────────────────────
async function checkHealth() {
    try {
        const res = await fetch('/api/health');
        const data = await res.json();
        const row = document.getElementById('statusRow');
        row.innerHTML = `
            <span class="status-pill ${data.ollama ? 'green' : 'red'}"><span class="dot"></span> Ollama</span>
            <span class="status-pill ${data.gemma ? 'green' : 'amber'}"><span class="dot"></span> Gemma</span>
        `;
    } catch {
        document.getElementById('statusRow').innerHTML =
            '<span class="status-pill red"><span class="dot"></span> Offline</span>';
    }
}

// ── Loading ──────────────────────────────────────────────────────────────
function showLoading(text = 'Processing...') {
    document.getElementById('loadingText').textContent = text;
    document.getElementById('loadingOverlay').classList.add('active');
}

function hideLoading() {
    document.getElementById('loadingOverlay').classList.remove('active');
}

// ── Markdown Rendering ──────────────────────────────────────────────────
function renderMarkdown(text) {
    if (typeof marked !== 'undefined') {
        return marked.parse(text || '');
    }
    return (text || '').replace(/\n/g, '<br>');
}

function resultCard(title, html, extra = '') {
    return `<div class="result-container">
        <h3>${title}</h3>
        <div class="result-content markdown-body">${html}</div>
        ${extra}
    </div>`;
}

// ── API Helper ───────────────────────────────────────────────────────────
async function api(path, body = null) {
    const opts = body
        ? { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) }
        : { method: 'GET' };
    const res = await fetch(path, opts);
    if (!res.ok) {
        const err = await res.text();
        throw new Error(err || `Request failed (${res.status})`);
    }
    return res.json();
}

// ═══════════════════════════════════════════════════════════════════════════
//  DASHBOARD
// ═══════════════════════════════════════════════════════════════════════════

async function loadDashboard() {
    try {
        const d = await api('/api/smriti/dashboard');

        document.getElementById('kpiStreak').textContent = d.streak || 0;
        document.getElementById('kpiEvents').textContent = d.total_events || 0;
        document.getElementById('kpiContent').textContent = d.content_count || 0;
        document.getElementById('kpiTools').textContent = Object.keys(d.tool_usage || {}).length;

        // Mastery bars
        const masteryEl = document.getElementById('masteryBars');
        if (d.mastery && d.mastery.length > 0) {
            masteryEl.innerHTML = d.mastery.slice(0, 8).map(m => {
                const pct = Math.round(m.score || 0);
                const color = pct >= 80 ? 'var(--green)' : pct >= 50 ? 'var(--amber)' : 'var(--coral)';
                return `<div class="mastery-bar">
                    <span class="topic">${m.topic}</span>
                    <div class="bar-track"><div class="bar-fill" style="width:${pct}%;background:${color}"></div></div>
                    <span class="score">${pct}%</span>
                </div>`;
            }).join('');
        } else {
            masteryEl.innerHTML = '<p style="color:var(--text-muted);font-size:0.82rem;">No mastery data yet. Complete quizzes to track progress.</p>';
        }

        // Recommendations
        const recsEl = document.getElementById('recommendations');
        if (d.recommendations && d.recommendations.length > 0) {
            recsEl.innerHTML = d.recommendations.map(r =>
                `<div class="recommendation">${renderMarkdown(r)}</div>`
            ).join('');
        }

        // Recent events
        const eventsEl = document.getElementById('recentEvents');
        if (d.recent_events && d.recent_events.length > 0) {
            eventsEl.innerHTML = d.recent_events.slice(0, 10).map(e => {
                const time = e.timestamp ? new Date(e.timestamp).toLocaleString() : '';
                return `<div class="event-item">
                    <div class="event-dot"></div>
                    <div class="event-info">
                        <div class="event-action"><strong>${e.tool}</strong> — ${e.action}: ${e.subject}</div>
                        <div class="event-meta">${time}</div>
                    </div>
                </div>`;
            }).join('');
        }

        // Profile
        if (d.profile) {
            if (d.profile.name) document.getElementById('profileName').value = d.profile.name;
            if (d.profile.preferred_style) document.getElementById('profileStyle').value = d.profile.preferred_style;
            if (d.profile.goals && d.profile.goals.length) document.getElementById('profileGoals').value = d.profile.goals.join(', ');
        }
    } catch (err) {
        console.error('Dashboard load error:', err);
    }
}

async function saveProfile() {
    const name = document.getElementById('profileName').value.trim();
    const style = document.getElementById('profileStyle').value;
    const goalsRaw = document.getElementById('profileGoals').value;
    const goals = goalsRaw ? goalsRaw.split(',').map(g => g.trim()).filter(Boolean) : [];
    try {
        await api('/api/smriti/profile', { name, preferred_style: style, goals });
        alert('Profile saved!');
    } catch (err) {
        alert('Error saving profile: ' + err.message);
    }
}

// ═══════════════════════════════════════════════════════════════════════════
//  NETSEEK
// ═══════════════════════════════════════════════════════════════════════════

async function runNetSeek() {
    const query = document.getElementById('netseekQuery').value.trim();
    if (!query) return alert('Enter a research query.');

    showLoading('Searching the web & synthesizing...');
    try {
        const data = await api('/api/netseek/search', {
            query,
            depth: document.getElementById('netseekDepth').value,
            output_format: document.getElementById('netseekFormat').value,
            additional_context: document.getElementById('netseekContext').value.trim(),
            max_results: 5,
        });

        let sourcesHtml = '';
        if (data.sources && data.sources.length > 0) {
            sourcesHtml = '<div class="divider"></div><h3 style="color:var(--accent-bright);font-size:0.95rem;margin-bottom:12px;">Sources</h3>' +
                data.sources.map(s => `<div class="source-card">
                    <span class="source-id">${s.source_id}</span>
                    <a href="${s.url}" target="_blank" rel="noopener">${s.title}</a>
                    <div class="snippet">${s.snippet || ''}</div>
                </div>`).join('');
        }

        document.getElementById('netseekResult').innerHTML = resultCard(
            `Research: ${data.query}`, renderMarkdown(data.result), sourcesHtml
        );

        // Store for cross-tool use
        state.neuroreadContent = data.result;
    } catch (err) {
        document.getElementById('netseekResult').innerHTML = `<div class="alert alert-error">Error: ${err.message}</div>`;
    } finally {
        hideLoading();
    }
}

// ═══════════════════════════════════════════════════════════════════════════
//  NEUROREAD
// ═══════════════════════════════════════════════════════════════════════════

async function uploadDocument() {
    const fileInput = document.getElementById('neuroreadFile');
    if (!fileInput.files.length) return alert('Select a file first.');

    showLoading('Extracting document text...');
    try {
        const formData = new FormData();
        formData.append('file', fileInput.files[0]);
        const res = await fetch('/api/neuroread/upload', { method: 'POST', body: formData });
        if (!res.ok) throw new Error(await res.text());
        const data = await res.json();

        state.neuroreadContent = data.text;
        document.getElementById('neuroreadContent').value = data.text.substring(0, 5000);
        document.getElementById('neuroreadStatus').innerHTML =
            `<div class="alert alert-success">Loaded "${data.filename}" — ${data.char_count.toLocaleString()} characters</div>`;
    } catch (err) {
        document.getElementById('neuroreadStatus').innerHTML =
            `<div class="alert alert-error">Error: ${err.message}</div>`;
    } finally {
        hideLoading();
    }
}

async function askNeuroRead() {
    const question = document.getElementById('neuroreadQuestion').value.trim();
    const context = document.getElementById('neuroreadContent').value.trim() || state.neuroreadContent;
    if (!question) return alert('Enter a question.');
    if (!context) return alert('Upload a document or paste content first.');

    showLoading('Analyzing document...');
    try {
        const data = await api('/api/neuroread/ask', {
            question,
            context,
            mode: document.getElementById('neuroreadMode').value,
        });
        document.getElementById('neuroreadResult').innerHTML = resultCard(
            `Answer (${data.mode})`, renderMarkdown(data.answer)
        );
    } catch (err) {
        document.getElementById('neuroreadResult').innerHTML =
            `<div class="alert alert-error">Error: ${err.message}</div>`;
    } finally {
        hideLoading();
    }
}

// ═══════════════════════════════════════════════════════════════════════════
//  EDUTUBE
// ═══════════════════════════════════════════════════════════════════════════

function switchEdutubeTab(tab) {
    const tabs = document.querySelectorAll('#edutubeTabs .tab');
    tabs.forEach(t => t.classList.remove('active'));
    if (tab === 'url') {
        tabs[0].classList.add('active');
        document.getElementById('edutubeUrlTab').style.display = 'block';
        document.getElementById('edutubePasteTab').style.display = 'none';
    } else {
        tabs[1].classList.add('active');
        document.getElementById('edutubeUrlTab').style.display = 'none';
        document.getElementById('edutubePasteTab').style.display = 'block';
    }
}

async function fetchTranscript() {
    const url = document.getElementById('edutubeUrl').value.trim();
    if (!url) return alert('Enter a YouTube URL.');

    showLoading('Fetching transcript...');
    try {
        const data = await api('/api/edutube/fetch', { url });
        state.edutubeTranscript = data.transcript;
        document.getElementById('edutubeStatus').innerHTML =
            `<div class="alert alert-success">Loaded transcript — ${data.char_count.toLocaleString()} characters</div>`;
    } catch (err) {
        document.getElementById('edutubeStatus').innerHTML =
            `<div class="alert alert-error">Error: ${err.message}</div>`;
    } finally {
        hideLoading();
    }
}

async function generateEduTube() {
    const transcript = state.edutubeTranscript || document.getElementById('edutubeTranscript').value.trim();
    if (!transcript) return alert('Fetch a transcript or paste one first.');

    const outputType = document.getElementById('edutubeOutputType').value;
    showLoading(`Generating ${outputType.toLowerCase()}...`);
    try {
        const data = await api('/api/edutube/generate', {
            transcript,
            output_type: outputType,
            subject: document.getElementById('edutubeSubject').value.trim(),
            source_label: document.getElementById('edutubeUrl')?.value || 'Manual',
        });

        if (outputType === 'Flashcards' && data.result && data.result.cards) {
            let html = `<div class="result-container"><h3>Flashcards (${data.result.cards.length})</h3>`;
            data.result.cards.forEach((card, i) => {
                html += `<div class="flashcard" onclick="this.classList.toggle('flipped')">
                    <div class="front"><strong>Q${i+1}:</strong> ${card.front}</div>
                    <div class="back">${card.back}</div>
                </div>`;
            });
            html += '</div>';
            document.getElementById('edutubeResult').innerHTML = html;
        } else {
            document.getElementById('edutubeResult').innerHTML = resultCard(
                outputType, renderMarkdown(typeof data.result === 'string' ? data.result : JSON.stringify(data.result))
            );
        }

        // Cross-tool: store for quiz/mindmap
        if (typeof data.result === 'string') state.neuroreadContent = data.result;
    } catch (err) {
        document.getElementById('edutubeResult').innerHTML =
            `<div class="alert alert-error">Error: ${err.message}</div>`;
    } finally {
        hideLoading();
    }
}

// ═══════════════════════════════════════════════════════════════════════════
//  QUIZFORGE
// ═══════════════════════════════════════════════════════════════════════════

async function generateQuiz() {
    const content = document.getElementById('quizContent').value.trim() || state.neuroreadContent;
    if (!content) return alert('Provide study content or use another tool first.');

    showLoading('Generating quiz...');
    try {
        const data = await api('/api/quizforge/generate', {
            content,
            subject: document.getElementById('quizSubject').value.trim(),
            topic: document.getElementById('quizTopic').value.trim(),
            num_questions: parseInt(document.getElementById('quizCount').value),
            difficulty: document.getElementById('quizDifficulty').value,
        });

        if (data.error) throw new Error(data.error);
        state.quizData = data.quiz;
        state.quizAnswers = {};
        renderQuiz(data.quiz);
    } catch (err) {
        document.getElementById('quizArea').innerHTML =
            `<div class="alert alert-error">Error: ${err.message}</div>`;
    } finally {
        hideLoading();
    }
}

function renderQuiz(quiz) {
    if (!quiz || !quiz.questions) return;
    let html = `<div class="result-container"><h3>${quiz.quiz_title || 'Quiz'}</h3>`;

    quiz.questions.forEach((q, qi) => {
        html += `<div class="quiz-question" id="q-${qi}">
            <div class="q-number">Question ${qi + 1} · ${q.difficulty || 'medium'} · ${q.bloom_level || ''}</div>
            <div class="q-text">${q.question}</div>`;

        if (q.options) {
            q.options.forEach((opt, oi) => {
                html += `<div class="quiz-option" id="opt-${qi}-${oi}" onclick="selectOption(${qi}, ${oi}, '${opt.replace(/'/g, "\\'")}')">
                    <strong>${String.fromCharCode(65 + oi)}.</strong> ${opt}
                </div>`;
            });
        }

        html += `<div class="quiz-explanation" id="expl-${qi}">${q.explanation || ''}</div>`;
        html += `</div>`;
    });

    html += `<div style="margin-top:20px;"><button class="btn btn-primary" onclick="submitQuiz()">✅ Submit & Score</button></div>`;
    html += `</div>`;
    document.getElementById('quizArea').innerHTML = html;
}

function selectOption(qi, oi, value) {
    // Clear previous selection for this question
    document.querySelectorAll(`#q-${qi} .quiz-option`).forEach(el => el.classList.remove('selected'));
    document.getElementById(`opt-${qi}-${oi}`).classList.add('selected');
    state.quizAnswers[qi] = value;
}

async function submitQuiz() {
    if (!state.quizData) return;
    const questions = state.quizData.questions;
    let correct = 0;

    questions.forEach((q, qi) => {
        const userAnswer = state.quizAnswers[qi];
        const isCorrect = userAnswer === q.correct_answer;
        if (isCorrect) correct++;

        // Show correct/incorrect styling
        if (q.options) {
            q.options.forEach((opt, oi) => {
                const el = document.getElementById(`opt-${qi}-${oi}`);
                if (opt === q.correct_answer) el.classList.add('correct');
                else if (opt === userAnswer && !isCorrect) el.classList.add('incorrect');
            });
        }

        // Show explanation
        document.getElementById(`expl-${qi}`).classList.add('visible');
    });

    const total = questions.length;
    const pct = Math.round((correct / total) * 100);
    const topic = document.getElementById('quizTopic').value.trim() || document.getElementById('quizSubject').value.trim() || 'General';

    // Score with memory
    try {
        await api('/api/quizforge/score', { topic, score: pct, total, correct });
    } catch { /* ignore scoring errors */ }

    const color = pct >= 80 ? 'var(--green)' : pct >= 50 ? 'var(--amber)' : 'var(--coral)';
    const scoreHtml = `<div class="alert" style="background:rgba(124,108,255,0.08);border:1px solid rgba(124,108,255,0.2);margin-top:16px;">
        Score: <strong style="color:${color};font-size:1.2rem;">${correct}/${total} (${pct}%)</strong>
        ${pct >= 80 ? ' — Excellent!' : pct >= 50 ? ' — Good effort, keep going!' : ' — Review the material and try again.'}
    </div>`;

    document.getElementById('quizArea').insertAdjacentHTML('beforeend', scoreHtml);
}

// ═══════════════════════════════════════════════════════════════════════════
//  MINDMAPPER
// ═══════════════════════════════════════════════════════════════════════════

async function generateMindMap() {
    const content = document.getElementById('mindmapContent').value.trim() || state.neuroreadContent;
    if (!content) return alert('Provide content to map.');

    showLoading('Generating mind map...');
    try {
        const data = await api('/api/mindmapper/generate', {
            content,
            topic: document.getElementById('mindmapTopic').value.trim(),
            style: document.getElementById('mindmapStyle').value,
        });

        let html = `<div class="result-container"><h3>Mind Map</h3>
            <p style="color:var(--text-secondary);font-size:0.85rem;margin-bottom:16px;">${data.summary}</p>
            <div class="mindmap-container"><pre class="mermaid">${data.mermaid_code}</pre></div>
        </div>`;

        document.getElementById('mindmapResult').innerHTML = html;

        // Render mermaid
        try {
            await mermaid.run({ querySelector: '.mermaid' });
        } catch (e) {
            console.warn('Mermaid render error:', e);
            // Show raw code as fallback
            document.querySelector('.mindmap-container').innerHTML =
                `<pre style="color:var(--text-secondary);font-size:0.82rem;white-space:pre-wrap;">${data.mermaid_code}</pre>`;
        }
    } catch (err) {
        document.getElementById('mindmapResult').innerHTML =
            `<div class="alert alert-error">Error: ${err.message}</div>`;
    } finally {
        hideLoading();
    }
}

// ═══════════════════════════════════════════════════════════════════════════
//  PREPMASTER
// ═══════════════════════════════════════════════════════════════════════════

function switchPrepTab(tab) {
    const parent = document.querySelector('#page-prepmaster .tabs');
    parent.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    if (tab === 'plan') {
        parent.children[0].classList.add('active');
        document.getElementById('prepPlanTab').style.display = 'block';
        document.getElementById('prepGuideTab').style.display = 'none';
    } else {
        parent.children[1].classList.add('active');
        document.getElementById('prepPlanTab').style.display = 'none';
        document.getElementById('prepGuideTab').style.display = 'block';
    }
}

async function generateStudyPlan() {
    const content = document.getElementById('prepContent').value.trim() || state.neuroreadContent;
    if (!content) return alert('Provide study content.');

    showLoading('Generating study plan...');
    try {
        const data = await api('/api/prepmaster/plan', {
            content,
            goal: document.getElementById('prepGoal').value.trim(),
            duration_weeks: parseInt(document.getElementById('prepWeeks').value),
            hours_per_week: parseInt(document.getElementById('prepHours').value),
        });
        document.getElementById('prepResult').innerHTML = resultCard('Study Plan', renderMarkdown(data.plan));
    } catch (err) {
        document.getElementById('prepResult').innerHTML =
            `<div class="alert alert-error">Error: ${err.message}</div>`;
    } finally {
        hideLoading();
    }
}

async function generateStudyGuide() {
    const content = document.getElementById('guideContent').value.trim() || state.neuroreadContent;
    if (!content) return alert('Provide study content.');

    showLoading('Generating study guide...');
    try {
        const data = await api('/api/prepmaster/guide', { content });
        document.getElementById('prepResult').innerHTML = resultCard('Study Guide', renderMarkdown(data.guide));
    } catch (err) {
        document.getElementById('prepResult').innerHTML =
            `<div class="alert alert-error">Error: ${err.message}</div>`;
    } finally {
        hideLoading();
    }
}

// ═══════════════════════════════════════════════════════════════════════════
//  STUDYAGENT — Plan → Execute → Verify → Record
// ═══════════════════════════════════════════════════════════════════════════

const ACTION_ICONS = {
    research: '🔍',
    study_notes: '📝',
    key_concepts: '💡',
    summarize: '📋',
    quiz: '✅',
};

const agent = {
    goal: '',
    topic: '',
    rationale: '',
    plan: [],
    session: null,
    quizAnswers: {},
};

async function agentCreatePlan() {
    const goal = document.getElementById('agentGoal').value.trim();
    const topic = document.getElementById('agentTopic').value.trim();
    if (!goal || !topic) return alert('Provide both a goal and a topic.');

    agent.goal = goal;
    agent.topic = topic;
    document.getElementById('agentPlanArea').innerHTML = '';
    document.getElementById('agentExecArea').innerHTML = '';
    document.getElementById('agentQuizArea').innerHTML = '';
    document.getElementById('agentReportArea').innerHTML = '';

    showLoading('Exploring memory & planning...');
    try {
        const data = await api('/api/agent/plan', { goal, topic });
        agent.plan = data.plan || [];
        agent.rationale = data.rationale || '';
        renderPlan(data);
    } catch (err) {
        document.getElementById('agentPlanArea').innerHTML =
            `<div class="alert alert-error">Plan failed: ${err.message}</div>`;
    } finally {
        hideLoading();
    }
}

function renderPlan(data) {
    const masteryNote = data.mastery_before > 0
        ? `Prior mastery on <strong>${data.topic}</strong>: <strong style="color:var(--accent-bright);">${Math.round(data.mastery_before)}%</strong>`
        : `<strong>No prior mastery</strong> tracked for this topic — fresh start.`;

    const stepsHtml = (data.plan || []).map((s, i) => `
        <div class="glass-card" style="display:flex;gap:14px;align-items:flex-start;padding:14px 18px;margin-bottom:8px;">
            <div style="background:linear-gradient(135deg,#FFB84D,#FF9F2D);color:#fff;font-weight:700;
                        width:30px;height:30px;border-radius:8px;display:flex;align-items:center;
                        justify-content:center;flex-shrink:0;font-size:0.78rem;">${i + 1}</div>
            <div style="flex:1;">
                <div style="display:flex;gap:8px;align-items:center;margin-bottom:2px;">
                    <span style="font-size:1rem;">${ACTION_ICONS[s.action] || '⚙️'}</span>
                    <strong style="color:var(--accent-bright);font-size:0.88rem;">${s.action}</strong>
                </div>
                <div style="color:var(--text-secondary);font-size:0.82rem;line-height:1.5;">${s.goal}</div>
            </div>
        </div>`).join('');

    document.getElementById('agentPlanArea').innerHTML = `
        <div class="result-container">
            <h3>📋 Proposed Plan (${(data.plan || []).length} steps)</h3>
            <div class="alert alert-info" style="margin-bottom:14px;">${masteryNote}</div>
            ${data.rationale ? `<div style="color:var(--text-secondary);font-size:0.85rem;margin-bottom:14px;line-height:1.6;"><strong>Rationale:</strong> ${data.rationale}</div>` : ''}
            ${stepsHtml}
            <div style="display:flex;gap:10px;margin-top:16px;">
                <button class="btn btn-primary" onclick="agentExecutePlan()">▶️ Approve & Execute</button>
                <button class="btn btn-secondary" onclick="agentCreatePlan()">🔄 Replan</button>
            </div>
        </div>`;
}

async function agentExecutePlan() {
    if (!agent.plan.length) return;

    // Render execution shell with pending steps
    const stepShell = agent.plan.map((s, i) => `
        <div class="glass-card" id="agent-step-${i}" style="display:flex;gap:14px;align-items:flex-start;padding:16px 20px;margin-bottom:10px;">
            <div id="agent-step-status-${i}" style="background:var(--bg-card);color:var(--text-muted);font-weight:700;
                        width:30px;height:30px;border-radius:8px;display:flex;align-items:center;
                        justify-content:center;flex-shrink:0;font-size:0.78rem;">⋯</div>
            <div style="flex:1;">
                <div style="display:flex;gap:8px;align-items:center;margin-bottom:4px;">
                    <span style="font-size:1rem;">${ACTION_ICONS[s.action] || '⚙️'}</span>
                    <strong style="color:var(--accent-bright);font-size:0.88rem;">${s.action}</strong>
                    <span style="color:var(--text-muted);font-size:0.78rem;">— ${s.goal}</span>
                </div>
                <div id="agent-step-result-${i}" style="color:var(--text-muted);font-size:0.8rem;font-style:italic;">Queued…</div>
            </div>
        </div>`).join('');

    document.getElementById('agentExecArea').innerHTML = `
        <div class="result-container">
            <h3>⚙️ Execution Trace</h3>
            ${stepShell}
        </div>`;

    showLoading('Agent executing plan…');
    try {
        const data = await api('/api/agent/execute', {
            goal: agent.goal,
            topic: agent.topic,
            plan: agent.plan,
            rationale: agent.rationale,
        });
        agent.session = data;

        // Update each step UI with final results
        (data.plan || []).forEach((s, i) => {
            const statusEl = document.getElementById(`agent-step-status-${i}`);
            const resultEl = document.getElementById(`agent-step-result-${i}`);
            if (statusEl) {
                if (s.status === 'done') {
                    statusEl.style.background = 'rgba(45,212,191,0.15)';
                    statusEl.style.color = 'var(--green)';
                    statusEl.textContent = '✓';
                } else {
                    statusEl.style.background = 'rgba(255,107,138,0.15)';
                    statusEl.style.color = 'var(--coral)';
                    statusEl.textContent = '✗';
                }
            }
            if (resultEl) {
                resultEl.style.color = 'var(--text-secondary)';
                resultEl.style.fontStyle = 'normal';
                resultEl.textContent = s.result || '(no output)';
            }
        });

        // Show artifacts
        renderArtifacts(data.artifacts || {});

        // Show verification quiz if generated
        const quiz = (data.artifacts || {}).quiz;
        if (quiz && quiz.questions && quiz.questions.length) {
            renderAgentQuiz(quiz);
        }

        // Show final session report
        if (data.final_summary) {
            document.getElementById('agentReportArea').innerHTML = `
                <div class="result-container">
                    <h3>📜 Session Report</h3>
                    <div class="markdown-body">${renderMarkdown(data.final_summary)}</div>
                </div>`;
        }
    } catch (err) {
        document.getElementById('agentExecArea').insertAdjacentHTML('beforeend',
            `<div class="alert alert-error">Execution error: ${err.message}</div>`);
    } finally {
        hideLoading();
    }
}

function renderArtifacts(artifacts) {
    const blocks = [];
    if (artifacts.research) {
        blocks.push({ label: '🔍 Research Brief', body: artifacts.research });
    }
    if (artifacts.notes) {
        blocks.push({ label: '📝 Study Notes', body: artifacts.notes });
    }
    if (artifacts.concepts) {
        blocks.push({ label: '💡 Key Concepts', body: artifacts.concepts });
    }
    if (artifacts.summary) {
        blocks.push({ label: '📋 Summary', body: artifacts.summary });
    }
    if (!blocks.length) return;

    const expanders = blocks.map((b, i) => `
        <details ${i === 0 ? 'open' : ''} style="margin-bottom:10px;background:var(--bg-card);border:1px solid var(--border);border-radius:var(--radius-md);">
            <summary style="cursor:pointer;padding:14px 18px;color:var(--accent-bright);font-weight:600;font-size:0.9rem;list-style:none;">${b.label}</summary>
            <div style="padding:0 18px 16px;" class="markdown-body">${renderMarkdown(b.body)}</div>
        </details>`).join('');

    document.getElementById('agentExecArea').insertAdjacentHTML('beforeend', `
        <div class="result-container" style="margin-top:14px;">
            <h3>📦 Artifacts Produced</h3>
            ${expanders}
        </div>`);
}

function renderAgentQuiz(quiz) {
    agent.quizAnswers = {};
    let html = `<div class="result-container">
        <h3>✅ Verification Quiz: ${quiz.quiz_title || agent.topic}</h3>
        <p style="color:var(--text-muted);font-size:0.82rem;margin-bottom:14px;">Take the quiz — your score updates Vidya Smriti mastery.</p>`;

    quiz.questions.forEach((q, qi) => {
        html += `<div class="quiz-question" id="agent-q-${qi}">
            <div class="q-number">Question ${qi + 1} · ${q.difficulty || 'medium'} · ${q.bloom_level || ''}</div>
            <div class="q-text">${q.question}</div>`;
        (q.options || []).forEach((opt, oi) => {
            const safeOpt = opt.replace(/'/g, "\\'").replace(/"/g, '&quot;');
            html += `<div class="quiz-option" id="agent-opt-${qi}-${oi}" onclick="agentSelectOption(${qi}, ${oi}, '${safeOpt}')">
                <strong>${String.fromCharCode(65 + oi)}.</strong> ${opt}
            </div>`;
        });
        html += `<div class="quiz-explanation" id="agent-expl-${qi}">${q.explanation || ''}</div></div>`;
    });

    html += `<button class="btn btn-primary" style="margin-top:16px;" onclick="agentSubmitQuiz()">🎯 Submit & Update Mastery</button>
    </div>`;
    document.getElementById('agentQuizArea').innerHTML = html;
    agent.quizQuestions = quiz.questions;
}

function agentSelectOption(qi, oi, value) {
    document.querySelectorAll(`#agent-q-${qi} .quiz-option`).forEach(el => el.classList.remove('selected'));
    document.getElementById(`agent-opt-${qi}-${oi}`).classList.add('selected');
    agent.quizAnswers[qi] = value;
}

async function agentSubmitQuiz() {
    if (!agent.quizQuestions) return;
    let correct = 0;
    agent.quizQuestions.forEach((q, qi) => {
        const userAnswer = agent.quizAnswers[qi];
        const isCorrect = userAnswer === q.correct_answer;
        if (isCorrect) correct++;
        (q.options || []).forEach((opt, oi) => {
            const el = document.getElementById(`agent-opt-${qi}-${oi}`);
            if (!el) return;
            if (opt === q.correct_answer) el.classList.add('correct');
            else if (opt === userAnswer && !isCorrect) el.classList.add('incorrect');
        });
        const expl = document.getElementById(`agent-expl-${qi}`);
        if (expl) expl.classList.add('visible');
    });
    const total = agent.quizQuestions.length;
    const pct = Math.round((correct / total) * 100);

    try {
        const verdict = await api('/api/agent/verify', {
            topic: agent.topic, score: pct, correct, total,
        });
        const color = pct >= 80 ? 'var(--green)' : pct >= 50 ? 'var(--amber)' : 'var(--coral)';
        document.getElementById('agentQuizArea').insertAdjacentHTML('beforeend', `
            <div class="alert" style="background:rgba(124,108,255,0.08);border:1px solid rgba(124,108,255,0.2);margin-top:16px;">
                Score: <strong style="color:${color};font-size:1.2rem;">${correct}/${total} (${pct}%)</strong>
                — ${verdict.message}<br>
                <span style="color:var(--text-muted);font-size:0.82rem;">Vidya Smriti mastery on <strong>${verdict.mastery.topic}</strong>:
                ${Math.round(verdict.mastery.score)}% over ${verdict.mastery.attempts} attempt(s).</span>
            </div>`);
    } catch (err) {
        document.getElementById('agentQuizArea').insertAdjacentHTML('beforeend',
            `<div class="alert alert-error">Mastery update failed: ${err.message}</div>`);
    }
}

// ═══════════════════════════════════════════════════════════════════════════
//  GENERIC TOOL — one shell, configured per tool from the backend registry
// ═══════════════════════════════════════════════════════════════════════════

const genericState = { toolId: null, config: null };

async function renderGenericPage(toolId) {
    try {
        const cfg = await api(`/api/tools/${toolId}`);
        genericState.toolId = toolId;
        genericState.config = cfg;

        document.getElementById('genericIcon').textContent = cfg.icon || '⚙️';
        document.getElementById('genericTitle').textContent = `${cfg.name} — ${cfg.description.split('.')[0]}`;
        document.getElementById('genericBadge').textContent = cfg.category;
        document.getElementById('genericDescription').textContent = cfg.description;
        document.getElementById('genericInputLabel').textContent = cfg.input_label || 'Input';

        const input = document.getElementById('genericInput');
        input.placeholder = `Paste ${cfg.input_label?.toLowerCase() || 'content'} here…`;
        input.value = '';

        // Render options dynamically
        const optsEl = document.getElementById('genericOptions');
        optsEl.innerHTML = (cfg.options || []).map(opt => {
            if (opt.type === 'select') {
                const opts = (opt.values || []).map(v => `<option value="${v}">${v}</option>`).join('');
                return `<div class="form-group">
                    <label>${opt.label}</label>
                    <select id="opt-${opt.id}">${opts}</select>
                </div>`;
            }
            return `<div class="form-group">
                <label>${opt.label}</label>
                <input type="text" id="opt-${opt.id}" placeholder="${opt.placeholder || ''}">
            </div>`;
        }).join('');

        document.getElementById('genericResult').innerHTML = '';
    } catch (err) {
        document.getElementById('genericResult').innerHTML =
            `<div class="alert alert-error">Failed to load tool config: ${err.message}</div>`;
    }
}

async function runGenericTool() {
    const cfg = genericState.config;
    if (!cfg) return;
    const input = document.getElementById('genericInput').value.trim();
    if (!input) return alert('Provide input first.');

    const options = {};
    (cfg.options || []).forEach(opt => {
        const el = document.getElementById(`opt-${opt.id}`);
        if (el) options[opt.id] = el.value;
    });

    showLoading(`Running ${cfg.name}…`);
    try {
        const data = await api(`/api/tools/${genericState.toolId}/run`, { input, options });

        const resultEl = document.getElementById('genericResult');
        if (data.kind === 'mermaid') {
            resultEl.innerHTML = `<div class="result-container">
                <h3>${cfg.icon} ${cfg.name} — Diagram</h3>
                <div class="mindmap-container"><pre class="mermaid">${escapeHtml(data.result)}</pre></div>
            </div>`;
            try { await mermaid.run({ querySelector: '#genericResult .mermaid' }); } catch (e) { console.warn(e); }
        } else if (data.kind === 'mermaid_with_text') {
            // Extract mermaid block + remaining text
            const m = data.result.match(/```mermaid\s*([\s\S]*?)```/);
            const mer = m ? m[1].trim() : '';
            const rest = m ? data.result.replace(m[0], '').trim() : data.result;
            resultEl.innerHTML = `<div class="result-container">
                <h3>${cfg.icon} ${cfg.name}</h3>
                ${mer ? `<div class="mindmap-container" style="margin-bottom:14px;"><pre class="mermaid">${escapeHtml(mer)}</pre></div>` : ''}
                <div class="markdown-body">${renderMarkdown(rest)}</div>
            </div>`;
            if (mer) { try { await mermaid.run({ querySelector: '#genericResult .mermaid' }); } catch (e) { console.warn(e); } }
        } else {
            resultEl.innerHTML = resultCard(`${cfg.icon} ${cfg.name}`, renderMarkdown(data.result));
        }
        // Stash result so chained tools can pick it up
        if (typeof data.result === 'string') state.neuroreadContent = data.result;
    } catch (err) {
        document.getElementById('genericResult').innerHTML =
            `<div class="alert alert-error">Error: ${err.message}</div>`;
    } finally {
        hideLoading();
    }
}

function escapeHtml(s) {
    return (s || '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
}

// ═══════════════════════════════════════════════════════════════════════════
//  GRAPHIQ — 2D graphing via Desmos
// ═══════════════════════════════════════════════════════════════════════════

let desmosCalc = null;

async function runGraphiQ() {
    const desc = document.getElementById('graphiqDesc').value.trim();
    if (!desc) return alert('Describe what to graph.');
    showLoading('Translating description → equations…');
    try {
        const data = await api('/api/graphiq/equations', {
            description: desc,
            style: document.getElementById('graphiqStyle').value,
        });
        const explainEl = document.getElementById('graphiqResult');
        explainEl.innerHTML = `<div class="result-container">
            <h3>📊 Equations</h3>
            <div class="markdown-body">${renderMarkdown(data.explanation || '')}</div>
            <ul style="margin-top:10px;">${(data.equations || []).map(e => `<li><code>${e}</code></li>`).join('')}</ul>
        </div>`;

        const container = document.getElementById('desmos-container');
        container.style.display = 'block';
        if (!desmosCalc && typeof Desmos !== 'undefined') {
            desmosCalc = Desmos.GraphingCalculator(container, {
                expressions: true, settingsMenu: false, zoomButtons: true,
            });
        }
        if (desmosCalc) {
            desmosCalc.setBlank();
            (data.equations || []).forEach((eq, i) => {
                desmosCalc.setExpression({ id: `eq${i}`, latex: eq });
            });
            const w = data.window || { xmin: -10, xmax: 10, ymin: -10, ymax: 10 };
            desmosCalc.setMathBounds({
                left: w.xmin, right: w.xmax, bottom: w.ymin, top: w.ymax,
            });
        }
    } catch (err) {
        document.getElementById('graphiqResult').innerHTML =
            `<div class="alert alert-error">Error: ${err.message}</div>`;
    } finally {
        hideLoading();
    }
}

// ═══════════════════════════════════════════════════════════════════════════
//  AUDIO OVERVIEW — script + MP3
// ═══════════════════════════════════════════════════════════════════════════

const audioState = { script: '' };

async function generateAudioScript() {
    const content = document.getElementById('audioContent').value.trim();
    if (!content) return alert('Provide source content.');
    showLoading('Writing spoken script…');
    try {
        const data = await api('/api/audio/script', {
            content,
            style: document.getElementById('audioStyle').value,
            duration: document.getElementById('audioDuration').value,
        });
        audioState.script = data.script;
        document.getElementById('audioResult').innerHTML = `<div class="result-container">
            <h3>🎙️ Spoken Script</h3>
            <div class="markdown-body" style="white-space:pre-wrap;">${escapeHtml(data.script)}</div>
            <button class="btn btn-primary" style="margin-top:14px;" onclick="generateAudioMP3()">🔊 Synthesize MP3 →</button>
        </div>`;
    } catch (err) {
        document.getElementById('audioResult').innerHTML =
            `<div class="alert alert-error">Error: ${err.message}</div>`;
    } finally {
        hideLoading();
    }
}

async function generateAudioMP3() {
    let script = audioState.script;
    if (!script) {
        const content = document.getElementById('audioContent').value.trim();
        if (!content) return alert('Generate the script first or paste content.');
        await generateAudioScript();
        script = audioState.script;
    }
    if (!script) return;

    showLoading('Synthesizing audio (gTTS)…');
    try {
        const r = await fetch('/api/audio/audio', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                script,
                accent: document.getElementById('audioAccent').value,
            }),
        });
        if (!r.ok) throw new Error(await r.text());
        const blob = await r.blob();
        const url = URL.createObjectURL(blob);
        document.getElementById('audioResult').insertAdjacentHTML('beforeend', `
            <div class="result-container" style="margin-top:14px;">
                <h3>🔊 Audio</h3>
                <audio controls style="width:100%;margin-top:8px;" src="${url}"></audio>
                <a href="${url}" download="polaris_overview.mp3" class="btn btn-secondary btn-sm" style="margin-top:10px;">⬇️ Download MP3</a>
            </div>`);
    } catch (err) {
        document.getElementById('audioResult').insertAdjacentHTML('beforeend',
            `<div class="alert alert-error">Audio synthesis failed: ${err.message}</div>`);
    } finally {
        hideLoading();
    }
}
