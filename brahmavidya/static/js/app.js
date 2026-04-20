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
    const page = document.getElementById(`page-${tool}`);
    const nav = document.querySelector(`.nav-item[data-tool="${tool}"]`);
    if (page) page.classList.add('active');
    if (nav) nav.classList.add('active');
    // Close mobile sidebar
    document.querySelector('.sidebar').classList.remove('open');
    // Refresh dashboard when switching to it
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
