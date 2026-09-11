const $ = (id) => document.getElementById(id);
const API = window.location.protocol === 'file:' ? 'http://127.0.0.1:8000' : '';
const state = { timer: null, history: JSON.parse(localStorage.getItem('yatharth_history') || '[]') };

function setStatus(text, kind='') { const el = $('status'); el.textContent = text; el.className = `status ${kind}`; }
function renderHistory() {
  const el = $('history');
  if (!state.history.length) { el.textContent = 'No generated songs yet.'; return; }
  el.innerHTML = state.history.slice(0, 20).map((x) => `<div class="history-item"><div><strong>${escapeHtml(x.title)}</strong><small>${escapeHtml(x.language)} · ${escapeHtml(x.genre)} · ${escapeHtml(x.voice)}</small></div><button data-url="${escapeAttr(x.url)}">Play</button></div>`).join('');
  el.querySelectorAll('button').forEach(b => b.onclick = () => { $('player').src = b.dataset.url; $('download').href = b.dataset.url; $('result').classList.remove('hidden'); $('player').play().catch(()=>{}); });
}
function escapeHtml(s='') { return String(s).replace(/[&<>'"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c])); }
function escapeAttr(s='') { return escapeHtml(s); }

async function checkHealth() {
  try {
    const r = await fetch(`${API}/api/health`); const j = await r.json();
    $('modeBadge').textContent = j.demo_mode ? 'DEMO MODE' : (j.engine_reachable ? 'AI ENGINE READY' : 'ENGINE OFFLINE');
    $('modeBadge').classList.toggle('live', !j.demo_mode && j.engine_reachable);
  } catch { $('modeBadge').textContent = 'OFFLINE'; }
}

async function poll(taskId) {
  clearInterval(state.timer);
  state.timer = setInterval(async () => {
    try {
      const r = await fetch(`${API}/api/tasks/${taskId}`); const j = await r.json();
      if (j.status === 'processing' || j.status === 'queued') { setStatus(`Creating your music… ${j.progress || 0}%`); return; }
      clearInterval(state.timer);
      if (j.status === 'failed') throw new Error(j.error || 'Generation failed');
      if (j.status === 'completed') {
        const url = j.audio_url || `${API}/api/audio/${taskId}`;
        $('player').src = url; $('download').href = url; $('download').download = `yatharth-song.${$('format').value}`; $('result').classList.remove('hidden');
        const m = j.metadata || {};
        $('meta').textContent = j.demo ? 'Demo audio. Connect ACE-Step for real AI music.' : `AI creation ready${m.bpm ? ` · ${m.bpm} BPM` : ''}${m.keyscale ? ` · ${m.keyscale}` : ''}${m.duration ? ` · ${m.duration}s` : ''}`;
        setStatus('Music created successfully.', 'success');
        const r = { title: ($('prompt').value || 'My Yatharth Song').slice(0, 60), language: $('language').value, genre: $('genre').value, voice: $('voice').value, url };
        state.history = [r, ...state.history.filter(x => x.url !== url)].slice(0, 20); localStorage.setItem('yatharth_history', JSON.stringify(state.history)); renderHistory();
      }
    } catch (e) { clearInterval(state.timer); setStatus(e.message, 'error'); }
  }, 1200);
}

$('generate').onclick = async () => {
  const prompt = $('prompt').value.trim(), lyrics = $('lyrics').value.trim();
  const instrumental = $('instrumental').checked || $('voice').value === 'Instrumental';
  if (!prompt && !lyrics && !instrumental) { setStatus('Please enter a song idea or lyrics.', 'error'); return; }
  $('generate').disabled = true; setStatus('Starting music generation…');
  try {
    const bpm = $('bpm').value ? Number($('bpm').value) : null;
    const payload = { prompt, lyrics, language: $('language').value, genre: $('genre').value, mood: $('mood').value, voice: $('voice').value, duration: Number($('duration').value), format: $('format').value, bpm, key: $('key').value || null, time_signature: $('timeSignature').value || null, instrumental };
    const r = await fetch(`${API}/api/generate`, { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify(payload) });
    const j = await r.json(); if (!r.ok) throw new Error(j.detail || 'Could not start generation');
    await poll(j.task_id);
  } catch (e) { setStatus(e.message, 'error'); }
  finally { $('generate').disabled = false; }
};

$('voice').onchange = () => { if ($('voice').value === 'Instrumental') $('instrumental').checked = true; };
checkHealth(); renderHistory();
