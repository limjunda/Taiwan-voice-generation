const API = 'http://localhost:8000';
let voices = [];
let personas = {};
let customPersonas = {};
let selectedVoice = null;
let selectedPersona = null;
let demoTexts = {};
let currentFilter = 'all';
let currentGender = 'all';
let activeSessionId = null;

async function init() {
    await checkApiStatus();
    await loadData();
    await loadAllPersonas();
    renderVoices();
    renderPersonas();
    await loadSessions();
    setupEventListeners();
    populateVoiceDropdown();
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
        // Cache-busting parameter to ensure fresh data
        const timestamp = Date.now();
        const [v, t] = await Promise.all([
            fetch(`data/voices.json?v=${timestamp}`).then(r => r.json()),
            fetch('data/demo_texts.json').then(r => r.json())
        ]);
        voices = v.voices;
        demoTexts = t;
        document.getElementById('text-content').value = demoTexts.insurance_demo;
    } catch (e) {
        console.error('Failed to load data:', e);
    }
}

async function loadAllPersonas() {
    try {
        // Load built-in personas
        const builtInRes = await fetch('data/personas.json');
        const builtInData = await builtInRes.json();
        personas = {};
        builtInData.personas.forEach(p => personas[p.id] = p);

        // Load custom personas from API
        const customRes = await fetch(`${API}/custom-personas`);
        customPersonas = await customRes.json();

        // Merge
        Object.assign(personas, customPersonas);
    } catch (e) {
        console.error('Failed to load personas:', e);
    }
}

async function loadSessions() {
    try {
        const res = await fetch(`${API}/sessions`);
        const data = await res.json();
        const sessions = data.sessions || [];
        activeSessionId = data.active_session_id;

        const list = document.getElementById('session-list');
        let html = '';

        // Favorites section
        html += `<div class="session-item" data-type="favorites">
            <div class="session-name">⭐ Favorites</div>
            <div class="session-meta">Favorited files</div>
        </div>`;

        // All audio (legacy)
        html += `<div class="session-item ${!activeSessionId ? 'active' : ''}" data-type="all-audio">
            <div class="session-name">📂 All Audio</div>
            <div class="session-meta">Legacy files</div>
        </div>`;

        // Sessions
        sessions.forEach(s => {
            const isActive = s.id === activeSessionId;
            const fileCount = s.generated_files?.length || 0;
            const date = new Date(s.created_at).toLocaleDateString();
            html += `<div class="session-item ${isActive ? 'active' : ''}" data-id="${s.id}">
                <div class="session-name">📁 ${s.name}</div>
                <div class="session-meta">${fileCount} files • ${date}</div>
            </div>`;
        });

        list.innerHTML = html;

        // Load audio for active session
        await loadAudio();
    } catch (e) {
        console.error('Failed to load sessions:', e);
        await loadAudio();
    }
}

async function loadAudio() {
    try {
        const res = await fetch(`${API}/audio`);
        const audioFiles = await res.json();

        clearResults();
        audioFiles.forEach(audio => {
            addResultRow(audio.voice, audio.persona, audio.filename, audio.is_favorite);
        });
    } catch (e) {
        console.error('Failed to load audio:', e);
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

        updateSidebarActive('favorites');
    } catch (e) {
        console.error('Failed to load favorites:', e);
    }
}

async function switchSession(sessionId) {
    try {
        await fetch(`${API}/sessions/active/${sessionId}`, { method: 'POST' });
        activeSessionId = sessionId;
        await loadAudio();
        updateSidebarActive(sessionId);
    } catch (e) {
        console.error('Failed to switch session:', e);
    }
}

async function loadAllLegacyAudio() {
    try {
        // Load legacy audio files (from output/ folder, not session folders)
        activeSessionId = null;
        const res = await fetch(`${API}/audio?legacy=true`);
        const audioFiles = await res.json();

        clearResults();
        audioFiles.forEach(audio => {
            addResultRow(audio.voice, audio.persona, audio.filename, audio.is_favorite);
        });

        updateSidebarActive('all-audio');
    } catch (e) {
        console.error('Failed to load audio:', e);
    }
}

function updateSidebarActive(id) {
    document.querySelectorAll('.session-item').forEach(el => el.classList.remove('active'));
    const target = id === 'favorites' || id === 'all-audio'
        ? document.querySelector(`.session-item[data-type="${id}"]`)
        : document.querySelector(`.session-item[data-id="${id}"]`);
    if (target) target.classList.add('active');
}

function renderVoices() {
    const grid = document.getElementById('voice-grid');
    let filteredVoices = voices;

    // Apply gender filter
    if (currentGender !== 'all') {
        filteredVoices = filteredVoices.filter(v => v.gender === currentGender);
    }

    // Apply characteristic filter
    if (currentFilter !== 'all') {
        filteredVoices = filteredVoices.filter(v => v.characteristic === currentFilter);
    }

    grid.innerHTML = filteredVoices.map(v => `
        <div class="voice-card ${selectedVoice === v.name ? 'selected' : ''}" data-voice="${v.name}" data-char="${v.characteristic}" data-gender="${v.gender}">
            <div class="voice-name">${v.gender === 'male' ? '♂' : '♀'} ${v.name}</div>
            <div class="voice-char">${v.characteristic}</div>
        </div>
    `).join('');
}

function renderPersonas() {
    const grid = document.getElementById('persona-grid');
    grid.innerHTML = Object.values(personas).map(p => {
        const isCustom = p.is_custom ? 'custom' : '';
        const isSelected = selectedPersona === p.id ? 'selected' : '';
        return `
            <div class="persona-card ${isCustom} ${isSelected}" data-persona="${p.id}">
                <div class="persona-name">${p.name}</div>
                <div class="persona-local">${p.local_name || ''}</div>
                <div class="persona-rec">Rec: ${p.recommended_voice || '-'}</div>
            </div>
        `;
    }).join('');
}

function populateVoiceDropdown() {
    const select = document.getElementById('persona-voice');
    select.innerHTML = '<option value="">Select a voice...</option>';
    voices.forEach(v => {
        select.innerHTML += `<option value="${v.name}">${v.name} (${v.characteristic})</option>`;
    });
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

    // Voice filtering (characteristic and gender)
    document.querySelector('.filter-bar').addEventListener('click', e => {
        const btn = e.target.closest('.filter-btn');
        if (btn) {
            // Handle gender filter separately
            if (btn.dataset.gender) {
                // Toggle gender filter
                document.querySelectorAll('.gender-btn').forEach(b => b.classList.remove('active'));
                if (currentGender === btn.dataset.gender) {
                    currentGender = 'all'; // Click again to clear
                } else {
                    btn.classList.add('active');
                    currentGender = btn.dataset.gender;
                }
            } else {
                // Handle characteristic filter
                document.querySelectorAll('.filter-btn:not(.gender-btn)').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                currentFilter = btn.dataset.filter;
            }
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

            const persona = personas[selectedPersona];
            if (persona) {
                const infoEl = document.getElementById('persona-info');
                infoEl.textContent = `Tone: ${persona.tone_instructions}`;
                infoEl.classList.add('visible');
            }

            updateExportConfig();
        }
    });

    // Double-click to edit custom persona
    document.getElementById('persona-grid').addEventListener('dblclick', e => {
        const card = e.target.closest('.persona-card.custom');
        if (card) {
            const personaId = card.dataset.persona;
            openPersonaModal(personaId);
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
                await loadAllLegacyAudio();
            } else if (sessionId) {
                await switchSession(sessionId);
            }
        }
    });

    // Generate buttons
    document.getElementById('generate-btn').addEventListener('click', generateSelected);
    document.getElementById('batch-btn').addEventListener('click', generateBatch);
    document.getElementById('copy-config').addEventListener('click', copyConfig);

    // New session button
    document.getElementById('new-session').addEventListener('click', createNewSession);

    // Create persona button
    document.getElementById('create-persona-btn').addEventListener('click', () => openPersonaModal());

    // Persona form submit
    document.getElementById('persona-form').addEventListener('submit', savePersona);

    // Delete persona button
    document.getElementById('delete-persona-btn').addEventListener('click', deletePersona);

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
            }
        });
    });

    // Audio slider
    document.getElementById('audio-slider').addEventListener('input', (e) => {
        if (currentAudio) {
            currentAudio.currentTime = e.target.value;
        }
    });
}

async function createNewSession() {
    const name = `Session ${new Date().toLocaleString()}`;
    const text = document.getElementById('text-content').value;
    const textType = document.querySelector('.tab.active')?.dataset.tab || 'demo';

    try {
        const res = await fetch(`${API}/sessions`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                name,
                persona_id: selectedPersona,
                text_type: textType,
                text_content: text
            })
        });
        const data = await res.json();
        activeSessionId = data.id;

        clearResults();
        await loadSessions();
    } catch (e) {
        console.error('Failed to create session:', e);
    }
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
                text,
                persona_id: selectedPersona,
                model
            })
        });
        const data = await res.json();

        if (data.success) {
            addResultRow(selectedVoice, selectedPersona, data.file_path, false);
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
                text,
                persona_id: selectedPersona,
                model
            })
        });
        const data = await res.json();

        progressBar.style.width = '100%';
        progressText.textContent = `${data.total}/${voiceNames.length}`;

        data.results.forEach((r, i) => {
            if (r.success) {
                addResultRow(voiceNames[i], selectedPersona, r.file_path, false);
            }
        });

        await loadSessions();
    } catch (e) {
        alert('Failed to batch generate: ' + e.message);
    } finally {
        btn.disabled = false;
        setTimeout(() => progressEl.style.display = 'none', 2000);
    }
}

function addResultRow(voice, persona, filePath, isFavorite = false) {
    const tbody = document.querySelector('#results-table tbody');
    const row = document.createElement('tr');
    const personaName = persona ? (personas[persona]?.name || persona) : 'default';
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

// Audio Player
let currentAudio = null;
let currentFilename = null;

function playAudio(filename) {
    if (currentAudio && currentFilename !== filename) {
        currentAudio.pause();
        currentAudio = null;
    }

    if (currentFilename === filename && currentAudio) {
        currentAudio.play();
        document.getElementById('play-pause-btn').textContent = '⏸';
        return;
    }

    currentFilename = filename;
    currentAudio = new Audio(`${API}/audio/${filename}`);

    document.getElementById('audio-player').style.display = 'block';

    const parts = filename.replace('.wav', '').split('_');
    document.getElementById('player-voice').textContent = parts[2] || 'Unknown';
    document.getElementById('player-persona').textContent = parts.slice(3).join(' ') || 'default';

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

async function showMetadata(filename) {
    try {
        const metaFilename = filename.replace('.wav', '.txt');
        const res = await fetch(`${API}/metadata/${metaFilename}`);

        if (res.ok) {
            document.getElementById('metadata-text').textContent = await res.text();
        } else {
            const parts = filename.replace('.wav', '').split('_');
            document.getElementById('metadata-text').textContent =
                `Filename: ${filename}\nVoice: ${parts[2] || 'unknown'}\nPersona: ${parts.slice(3).join(' ') || 'default'}`;
        }

        document.getElementById('metadata-panel').style.display = 'block';
    } catch (e) {
        console.error('Failed to load metadata:', e);
    }
}

function closeMetadata() {
    document.getElementById('metadata-panel').style.display = 'none';
}

function updateExportConfig() {
    const config = {
        voice: selectedVoice,
        persona: selectedPersona,
        model: document.getElementById('model-select').value,
        recommended_for: selectedPersona ? personas[selectedPersona]?.name : null
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

// Custom Persona Modal
function openPersonaModal(personaId = null) {
    const modal = document.getElementById('persona-modal');
    const form = document.getElementById('persona-form');
    const title = document.getElementById('modal-title');
    const deleteBtn = document.getElementById('delete-persona-btn');

    form.reset();

    if (personaId && customPersonas[personaId]) {
        const p = customPersonas[personaId];
        title.textContent = 'Edit Custom Persona';
        document.getElementById('persona-id').value = personaId;
        document.getElementById('persona-name').value = p.name || '';
        document.getElementById('persona-local-name').value = p.local_name || '';
        document.getElementById('persona-archetype').value = p.archetype || '';
        document.getElementById('persona-traits').value = p.traits || '';
        document.getElementById('persona-tone').value = p.tone_instructions || '';
        document.getElementById('persona-voice').value = p.recommended_voice || '';
        deleteBtn.style.display = 'block';
    } else {
        title.textContent = 'Create Custom Persona';
        document.getElementById('persona-id').value = '';
        deleteBtn.style.display = 'none';
    }

    modal.style.display = 'flex';
}

function closePersonaModal() {
    document.getElementById('persona-modal').style.display = 'none';
}

async function savePersona(e) {
    e.preventDefault();

    const personaId = document.getElementById('persona-id').value;
    const data = {
        id: personaId || null,
        name: document.getElementById('persona-name').value,
        local_name: document.getElementById('persona-local-name').value,
        archetype: document.getElementById('persona-archetype').value,
        traits: document.getElementById('persona-traits').value,
        tone_instructions: document.getElementById('persona-tone').value,
        recommended_voice: document.getElementById('persona-voice').value
    };

    try {
        const method = personaId ? 'PUT' : 'POST';
        const url = personaId ? `${API}/custom-personas/${personaId}` : `${API}/custom-personas`;

        const res = await fetch(url, {
            method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        if (res.ok) {
            closePersonaModal();
            await loadAllPersonas();
            renderPersonas();
        } else {
            alert('Failed to save persona');
        }
    } catch (e) {
        console.error('Failed to save persona:', e);
        alert('Failed to save persona');
    }
}

async function deletePersona() {
    const personaId = document.getElementById('persona-id').value;
    if (!personaId) return;

    if (!confirm('Are you sure you want to delete this persona?')) return;

    try {
        const res = await fetch(`${API}/custom-personas/${personaId}`, { method: 'DELETE' });

        if (res.ok) {
            closePersonaModal();
            await loadAllPersonas();
            renderPersonas();
            if (selectedPersona === personaId) {
                selectedPersona = null;
                document.getElementById('persona-info').classList.remove('visible');
            }
        } else {
            alert('Failed to delete persona');
        }
    } catch (e) {
        console.error('Failed to delete persona:', e);
        alert('Failed to delete persona');
    }
}

// Initialize
document.addEventListener('DOMContentLoaded', init);
