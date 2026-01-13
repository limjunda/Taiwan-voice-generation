const API = 'http://localhost:8000';
let voices = [];
let personas = [];
let selectedVoice = null;
let selectedPersona = null;
let demoTexts = {};
let currentFilter = 'all';
let currentSessionId = null;
let currentSessionFiles = [];

async function init() {
    await checkApiStatus();
    await loadData();
    renderVoices();
    renderPersonas();
    await loadSessions();
    setupEventListeners();
}

async function checkApiStatus() {
    try {
        const res = await fetch(`${API}/auth/status`);
        const data = await res.json();
        const statusEl = document.getElementById('api-status');
        statusEl.textContent = data.valid ? '✓ Connected' : '✗ Not connected';
        statusEl.className = 'api-status ' + (data.valid ? 'connected' : 'error');
    } catch {
        const statusEl = document.getElementById('api-status');
        statusEl.textContent = '✗ API Offline';
        statusEl.className = 'api-status error';
    }
}

async function loadData() {
    try {
        const [v, p, t] = await Promise.all([
            fetch('data/voices.json').then(r => r.json()),
            fetch('data/personas.json').then(r => r.json()),
            fetch('data/demo_texts.json').then(r => r.json())
        ]);
        voices = v.voices;
        personas = p.personas;
        demoTexts = t;
        document.getElementById('text-content').value = demoTexts.insurance_demo;
    } catch (e) {
        console.error('Failed to load data:', e);
    }
}

async function loadSessions() {
    try {
        const res = await fetch(`${API}/sessions`);
        const sessions = await res.json();
        const list = document.getElementById('session-list');

        // Always load audio files for counts
        const audioRes = await fetch(`${API}/audio`);
        const audioFiles = await audioRes.json();
        const favCount = audioFiles.filter(a => a.is_favorite).length;

        let sidebarHTML = '';

        // Favorites section
        sidebarHTML += `<div class="session-item" data-type="favorites">
            <div class="session-name">⭐ Favorites</div>
            <div class="session-meta">${favCount} file(s)</div>
        </div>`;

        // All Audio section
        sidebarHTML += `<div class="session-item active" data-type="all-audio">
            <div class="session-name">📂 All Audio</div>
            <div class="session-meta">${audioFiles.length} file(s)</div>
        </div>`;

        // Add sessions if any
        if (sessions.length > 0) {
            sidebarHTML += sessions.map(s => `
                <div class="session-item" data-id="${s.id}">
                    <div class="session-name">${s.name}</div>
                    <div class="session-meta">${s.voices_tested.length} voices</div>
                </div>
            `).join('');
        }

        list.innerHTML = sidebarHTML;

        // Load all audio into results
        clearResults();
        audioFiles.forEach(audio => {
            addResultRow(audio.voice, audio.persona, audio.filename, audio.is_favorite);
        });

    } catch (e) {
        console.log('Failed to load sessions:', e);
        await loadAllAudio();
    }
}

async function loadAllAudio() {
    try {
        const res = await fetch(`${API}/audio`);
        const audioFiles = await res.json();
        const favCount = audioFiles.filter(a => a.is_favorite).length;

        const list = document.getElementById('session-list');
        list.innerHTML = `
            <div class="session-item" data-type="favorites">
                <div class="session-name">⭐ Favorites</div>
                <div class="session-meta">${favCount} file(s)</div>
            </div>
            <div class="session-item active" data-type="all-audio">
                <div class="session-name">📂 All Audio</div>
                <div class="session-meta">${audioFiles.length} file(s)</div>
            </div>`;

        clearResults();
        audioFiles.forEach(audio => {
            addResultRow(audio.voice, audio.persona, audio.filename, audio.is_favorite);
        });
    } catch (e) {
        console.log('Failed to load audio:', e);
    }
}

async function loadFavorites() {
    try {
        const res = await fetch(`${API}/favorites`);
        const favorites = await res.json();

        clearResults();
        favorites.forEach(audio => {
            addResultRow(audio.voice, audio.persona, audio.filename, true);
        });

        // Update active state
        document.querySelectorAll('.session-item').forEach(el => el.classList.remove('active'));
        const favEl = document.querySelector('.session-item[data-type="favorites"]');
        if (favEl) favEl.classList.add('active');
    } catch (e) {
        console.log('Failed to load favorites:', e);
    }
}

async function loadSession(sessionId) {
    try {
        const res = await fetch(`${API}/sessions/${sessionId}`);
        const session = await res.json();

        currentSessionId = session.id;
        currentSessionFiles = session.generated_files;

        // Update UI
        clearResults();
        session.generated_files.forEach(filename => {
            // Parse filename to get voice and persona
            const parts = filename.replace('.wav', '').split('_');
            const voice = parts.length > 2 ? parts[2] : 'unknown';
            const persona = parts.length > 3 ? parts[3] : 'default';
            addResultRow(voice, persona, filename);
        });

        // Highlight selected session
        document.querySelectorAll('.session-item').forEach(el => el.classList.remove('active'));
        const sessionEl = document.querySelector(`.session-item[data-id="${sessionId}"]`);
        if (sessionEl) sessionEl.classList.add('active');

        // Restore text content if available
        if (session.text_content) {
            document.getElementById('text-content').value = session.text_content;
        }

        // Restore persona selection
        if (session.persona_id) {
            selectedPersona = session.persona_id;
            renderPersonas();
            const persona = personas.find(p => p.id === session.persona_id);
            if (persona) {
                const infoEl = document.getElementById('persona-info');
                infoEl.textContent = `Tone: ${persona.tone_instructions}`;
                infoEl.classList.add('visible');
            }
        }

    } catch (e) {
        console.error('Failed to load session:', e);
    }
}

async function createNewSession() {
    const text = document.getElementById('text-content').value;
    const textType = document.querySelector('.tab.active')?.dataset.tab || 'custom';

    try {
        const res = await fetch(`${API}/sessions`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                name: `Session ${new Date().toLocaleString()}`,
                persona_id: selectedPersona,
                text_type: textType,
                text_content: text,
                voices: [],
                files: []
            })
        });
        const session = await res.json();
        currentSessionId = session.id;
        currentSessionFiles = [];

        clearResults();
        await loadSessions();

        return session;
    } catch (e) {
        console.error('Failed to create session:', e);
        return null;
    }
}

async function updateCurrentSession(voice, filename) {
    if (!currentSessionId) {
        // Create new session first
        await createNewSession();
    }

    if (currentSessionId) {
        currentSessionFiles.push(filename);

        try {
            await fetch(`${API}/sessions/${currentSessionId}`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    voices: [voice],
                    files: [filename]
                })
            });
        } catch (e) {
            console.log('Failed to update session:', e);
        }
    }
}

function renderVoices() {
    const grid = document.getElementById('voice-grid');
    const filteredVoices = currentFilter === 'all'
        ? voices
        : voices.filter(v => v.characteristic === currentFilter);

    grid.innerHTML = filteredVoices.map(v => `
        <div class="voice-card ${selectedVoice === v.name ? 'selected' : ''}" data-voice="${v.name}" data-char="${v.characteristic}">
            <div class="voice-name">${v.name}</div>
            <div class="voice-char">${v.characteristic}</div>
        </div>
    `).join('');
}

function renderPersonas() {
    const grid = document.getElementById('persona-grid');
    grid.innerHTML = personas.map(p => `
        <div class="persona-card ${selectedPersona === p.id ? 'selected' : ''}" data-persona="${p.id}">
            <div class="persona-name">${p.name}</div>
            <div class="persona-local">${p.local_name}</div>
            <div class="persona-rec">Rec: ${p.recommended_voice}</div>
        </div>
    `).join('');
}

function setupEventListeners() {
    // Voice selection
    document.getElementById('voice-grid').addEventListener('click', e => {
        const card = e.target.closest('.voice-card');
        if (card) {
            document.querySelectorAll('.voice-card').forEach(c => c.classList.remove('selected'));
            card.classList.add('selected');
            selectedVoice = card.dataset.voice;
            updateExportConfig();
        }
    });

    // Voice filtering
    document.querySelector('.filter-bar').addEventListener('click', e => {
        const btn = e.target.closest('.filter-btn');
        if (btn) {
            document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            currentFilter = btn.dataset.filter;
            renderVoices();
        }
    });

    // Persona selection
    document.getElementById('persona-grid').addEventListener('click', e => {
        const card = e.target.closest('.persona-card');
        if (card) {
            document.querySelectorAll('.persona-card').forEach(c => c.classList.remove('selected'));
            card.classList.add('selected');
            selectedPersona = card.dataset.persona;

            const persona = personas.find(p => p.id === selectedPersona);
            const infoEl = document.getElementById('persona-info');
            infoEl.textContent = `Tone: ${persona.tone_instructions}`;
            infoEl.classList.add('visible');

            updateExportConfig();
        }
    });

    // Session sidebar click
    document.getElementById('session-list').addEventListener('click', async e => {
        const item = e.target.closest('.session-item');
        if (item) {
            const sessionId = item.dataset.id;
            const type = item.dataset.type;

            if (type === 'favorites') {
                await loadFavorites();
            } else if (type === 'all-audio') {
                await loadAllAudio();
            } else if (sessionId) {
                await loadSession(sessionId);
            }
        }
    });

    // Generate button
    document.getElementById('generate-btn').addEventListener('click', generateSelected);
    document.getElementById('batch-btn').addEventListener('click', generateBatch);
    document.getElementById('copy-config').addEventListener('click', copyConfig);

    // New session button
    document.getElementById('new-session').addEventListener('click', async () => {
        currentSessionId = null;
        currentSessionFiles = [];
        clearResults();
        selectedVoice = null;
        selectedPersona = null;
        renderVoices();
        renderPersonas();
        document.getElementById('persona-info').classList.remove('visible');
        document.getElementById('text-content').value = demoTexts.insurance_demo;

        // Remove active state from sessions
        document.querySelectorAll('.session-item').forEach(el => el.classList.remove('active'));
    });

    // Tabs
    document.querySelectorAll('.tab').forEach(tab => {
        tab.addEventListener('click', () => {
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            const type = tab.dataset.tab;
            if (type === 'demo') {
                document.getElementById('text-content').value = demoTexts.insurance_demo;
            } else if (type === 'phrases') {
                document.getElementById('text-content').value = demoTexts.test_phrases.join('\n');
            } else {
                document.getElementById('text-content').value = '';
                document.getElementById('text-content').placeholder = 'Enter custom text here...';
            }
        });
    });
}

async function generateSelected() {
    if (!selectedVoice) {
        alert('Please select a voice first');
        return;
    }

    const text = document.getElementById('text-content').value;
    if (!text.trim()) {
        alert('Please enter some text');
        return;
    }

    const model = document.getElementById('model-select').value;
    const btn = document.getElementById('generate-btn');
    btn.disabled = true;
    btn.textContent = '⏳ Generating...';

    try {
        const res = await fetch(`${API}/generate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                voice: selectedVoice,
                text: text,
                persona_id: selectedPersona,
                model: model
            })
        });
        const data = await res.json();

        if (data.success) {
            addResultRow(selectedVoice, selectedPersona, data.file_path);
            // Refresh session list
            await loadSessions();
        } else {
            alert('Error: ' + data.error);
        }
    } catch (e) {
        alert('Failed to generate: ' + e.message);
    } finally {
        btn.disabled = false;
        btn.textContent = '▶ Generate Selected';
    }
}

async function generateBatch() {
    const text = document.getElementById('text-content').value;
    if (!text.trim()) {
        alert('Please enter some text');
        return;
    }

    const model = document.getElementById('model-select').value;
    const voiceNames = voices.map(v => v.name);

    const btn = document.getElementById('batch-btn');
    const progressEl = document.getElementById('progress');
    const progressBar = document.getElementById('progress-bar');
    const progressText = document.getElementById('progress-text');

    btn.disabled = true;
    progressEl.style.display = 'flex';
    progressText.textContent = `0/${voiceNames.length}`;
    progressBar.style.width = '0%';

    try {
        const res = await fetch(`${API}/batch`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                voices: voiceNames,
                text: text,
                persona_id: selectedPersona,
                model: model
            })
        });
        const data = await res.json();

        progressBar.style.width = '100%';
        progressText.textContent = `${data.total}/${voiceNames.length}`;

        data.results.forEach((r, i) => {
            if (r.success) {
                addResultRow(voiceNames[i], selectedPersona, r.file_path);
            }
        });

        // Refresh sessions
        await loadSessions();

    } catch (e) {
        alert('Failed to batch generate: ' + e.message);
    } finally {
        btn.disabled = false;
        setTimeout(() => {
            progressEl.style.display = 'none';
        }, 2000);
    }
}

function addResultRow(voice, persona, filePath, isFavorite = false) {
    const tbody = document.querySelector('#results-table tbody');
    const row = document.createElement('tr');
    const personaName = persona ? (personas.find(p => p.id === persona)?.name || persona) : 'default';
    const filename = filePath.includes('/') ? filePath.split('/').pop() : filePath;
    const favClass = isFavorite ? 'favorited' : '';

    row.innerHTML = `
        <td>${voice}</td>
        <td>${personaName}</td>
        <td>
            <button onclick="event.stopPropagation(); playAudio('${filename}')" title="Play">▶</button>
            <button class="${favClass}" onclick="event.stopPropagation(); toggleFavorite(this, '${filename}')" title="Favorite">⭐</button>
            <button onclick="event.stopPropagation(); downloadFile('${filename}')" title="Download">💾</button>
            <button onclick="event.stopPropagation(); showMetadata('${filename}')" title="Info">ℹ️</button>
        </td>
    `;

    // Row click to show metadata
    row.addEventListener('click', () => {
        document.querySelectorAll('#results-table tbody tr').forEach(r => r.classList.remove('selected'));
        row.classList.add('selected');
        showMetadata(filename);
    });

    tbody.insertBefore(row, tbody.firstChild);
}

function clearResults() {
    document.querySelector('#results-table tbody').innerHTML = '';
}

async function toggleFavorite(btn, filename) {
    const isFavorited = btn.classList.contains('favorited');

    try {
        if (isFavorited) {
            await fetch(`${API}/favorites/${filename}`, { method: 'DELETE' });
            btn.classList.remove('favorited');
        } else {
            await fetch(`${API}/favorites/${filename}`, { method: 'POST' });
            btn.classList.add('favorited');
        }

        // Update sidebar counts
        const audioRes = await fetch(`${API}/audio`);
        const audioFiles = await audioRes.json();
        const favCount = audioFiles.filter(a => a.is_favorite).length;

        const favEl = document.querySelector('.session-item[data-type="favorites"] .session-meta');
        if (favEl) favEl.textContent = `${favCount} file(s)`;
    } catch (e) {
        console.error('Failed to toggle favorite:', e);
    }
}

function downloadFile(filename) {
    const link = document.createElement('a');
    link.href = `${API}/audio/${filename}`;
    link.download = filename;
    link.click();
}

function updateExportConfig() {
    const config = {
        voice: selectedVoice,
        persona: selectedPersona,
        model: document.getElementById('model-select').value,
        recommended_for: selectedPersona ? personas.find(p => p.id === selectedPersona)?.name : null
    };
    document.getElementById('export-config').textContent = JSON.stringify(config, null, 2);
}

function copyConfig() {
    const config = document.getElementById('export-config').textContent;
    navigator.clipboard.writeText(config).then(() => {
        const btn = document.getElementById('copy-config');
        const originalText = btn.textContent;
        btn.textContent = '✓ Copied!';
        setTimeout(() => btn.textContent = originalText, 2000);
    });
}

// Audio Player
let currentAudio = null;
let currentFilename = null;

function playAudio(filename) {
    // Stop current audio if playing different file
    if (currentAudio && currentFilename !== filename) {
        currentAudio.pause();
        currentAudio = null;
    }

    // If same file, just play
    if (currentFilename === filename && currentAudio) {
        currentAudio.play();
        document.getElementById('play-pause-btn').textContent = '⏸';
        return;
    }

    currentFilename = filename;
    currentAudio = new Audio(`${API}/audio/${filename}`);

    // Show player
    const player = document.getElementById('audio-player');
    player.style.display = 'block';

    // Update player info
    const parts = filename.replace('.wav', '').split('_');
    document.getElementById('player-voice').textContent = parts[2] || 'Unknown';
    document.getElementById('player-persona').textContent = parts.slice(3).join(' ') || 'default';

    // Setup audio events
    currentAudio.addEventListener('loadedmetadata', () => {
        document.getElementById('audio-slider').max = currentAudio.duration;
        updateTimeDisplay();
    });

    currentAudio.addEventListener('timeupdate', () => {
        document.getElementById('audio-slider').value = currentAudio.currentTime;
        updateTimeDisplay();
    });

    currentAudio.addEventListener('ended', () => {
        document.getElementById('play-pause-btn').textContent = '▶';
    });

    // Play
    currentAudio.play().catch(e => {
        console.error('Failed to play:', e);
        alert('Failed to play audio');
    });

    document.getElementById('play-pause-btn').textContent = '⏸';
}

function togglePlayPause() {
    if (!currentAudio) return;

    if (currentAudio.paused) {
        currentAudio.play();
        document.getElementById('play-pause-btn').textContent = '⏸';
    } else {
        currentAudio.pause();
        document.getElementById('play-pause-btn').textContent = '▶';
    }
}

function updateTimeDisplay() {
    if (!currentAudio) return;

    const current = formatTime(currentAudio.currentTime);
    const total = formatTime(currentAudio.duration || 0);
    document.getElementById('audio-time').textContent = `${current} / ${total}`;
}

function formatTime(seconds) {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
}

// Audio slider seek
document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('audio-slider').addEventListener('input', (e) => {
        if (currentAudio) {
            currentAudio.currentTime = e.target.value;
        }
    });
});

// Metadata Panel
async function showMetadata(filename) {
    try {
        // Load metadata from .txt file via API
        const metaFilename = filename.replace('.wav', '.txt');
        const res = await fetch(`${API}/metadata/${metaFilename}`);

        if (res.ok) {
            const text = await res.text();
            document.getElementById('metadata-text').textContent = text;
        } else {
            // Fallback: parse from filename
            const parts = filename.replace('.wav', '').split('_');
            document.getElementById('metadata-text').textContent =
                `Filename: ${filename}\n` +
                `Generated: ${parts[0]}_${parts[1]}\n` +
                `Voice: ${parts[2] || 'unknown'}\n` +
                `Persona: ${parts.slice(3).join(' ') || 'default'}`;
        }

        document.getElementById('metadata-panel').style.display = 'block';

        // Highlight row
        document.querySelectorAll('#results-table tbody tr').forEach(r => r.classList.remove('selected'));
    } catch (e) {
        console.error('Failed to load metadata:', e);
    }
}

function closeMetadata() {
    document.getElementById('metadata-panel').style.display = 'none';
}

// Initialize on load
document.addEventListener('DOMContentLoaded', init);
