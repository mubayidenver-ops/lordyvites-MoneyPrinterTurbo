'use strict';
const $ = id => document.getElementById(id);
let source = 'pexels', timer;
const notify = message => { $('notice').textContent = message; };
async function api(path, options = {}) {
  const response = await fetch(path, { ...options, headers: { 'Content-Type': 'application/json', ...options.headers } });
  let data; try { data = await response.json(); } catch { throw new Error('The PC returned an unreadable response.'); }
  if (response.status === 401 && path !== '/pair') { showPair(); throw new Error('Reconnect using the code on your PC.'); }
  if (!response.ok) throw new Error(data.message || 'Request failed. Check your computer.');
  return data;
}
function showPair() { clearTimeout(timer); $('pair-panel').hidden = false; $('studio').hidden = true; }
async function connected() {
  const status = await api('/studio-status'); source = status.source;
  $('pair-panel').hidden = true; $('studio').hidden = false; notify('Connected to your computer.');
  await refresh();
}
$('pair-form').addEventListener('submit', async event => {
  event.preventDefault(); try { await api('/pair', { method: 'POST', body: JSON.stringify({ code: $('pair-code').value }) }); $('pair-code').value = ''; await connected(); } catch (error) { notify(error.message); }
});
$('disconnect').addEventListener('click', async () => { try { await api('/unpair', { method: 'POST' }); showPair(); notify('Disconnected.'); } catch (error) { notify(error.message); } });
$('video-form').addEventListener('submit', async event => {
  event.preventDefault(); const form = new FormData(event.target); const body = Object.fromEntries(form);
  body.paragraph_number = Number(body.paragraph_number); body.subtitle_enabled = form.has('subtitle_enabled');
  Object.assign(body, { video_source: source, video_language: 'en', font_name: 'BeVietnamPro-Medium.ttf', bgm_type: '', video_count: 1 });
  $('generate').disabled = true;
  try { await api('/api/v1/videos', { method: 'POST', body: JSON.stringify(body) }); notify('Your video is queued. You can follow its progress below.'); await refresh(); }
  catch (error) { notify(error.message); } finally { $('generate').disabled = false; }
});
function element(tag, text, className) { const node = document.createElement(tag); if (text) node.textContent = text; if (className) node.className = className; return node; }
function safeMedia(path) { try { const url = new URL(path, location.origin); return url.origin === location.origin && url.pathname.startsWith('/tasks/') ? url.href : null; } catch { return null; } }
async function refresh() {
  clearTimeout(timer);
  try {
    const response = await api('/api/v1/tasks?page=1&page_size=30'); const tasks = response.data.tasks || [];
    const container = $('tasks'); container.replaceChildren();
    if (!tasks.length) container.append(element('p', 'Your first video is waiting to happen.', 'hint'));
    for (const task of tasks) {
      const article = element('article', '', 'task');
      article.append(element('h3', task.params?.video_subject || task.subject || `Video ${String(task.task_id).slice(0, 8)}`));
      const status = task.state === 1 ? 'Ready to watch' : task.state === -1 ? 'Generation failed. Check provider keys and the PC log.' : 'Creating your video…';
      article.append(element('p', status));
      if (task.state !== 1 && task.state !== -1) { const progress = element('progress'); progress.max = 100; progress.value = Number(task.progress) || 0; article.append(progress); }
      if (task.state === 1) for (const path of task.videos || []) {
        const href = safeMedia(path); if (!href) continue;
        const video = element('video'); video.controls = true; video.preload = 'none'; video.src = href; video.setAttribute('playsinline', ''); article.append(video);
        const link = element('a', 'Download video ↗'); link.href = href; link.download = ''; article.append(link);
      }
      container.append(article);
    }
    timer = setTimeout(refresh, tasks.some(task => ![1, -1].includes(task.state)) ? 4000 : 15000);
  } catch (error) { notify(error.message); if (!$('studio').hidden) timer = setTimeout(refresh, 10000); }
}
$('refresh').addEventListener('click', refresh);
(async () => {
  const code = new URLSearchParams(location.hash.slice(1)).get('pair'); history.replaceState(null, '', '/');
  try { if (code) await api('/pair', { method: 'POST', body: JSON.stringify({ code }) }); await connected(); } catch (error) { showPair(); if (code) notify(error.message); }
})();
