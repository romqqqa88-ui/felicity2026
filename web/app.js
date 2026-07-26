// Felicity AI Web Studio Frontend Logic

document.addEventListener('DOMContentLoaded', () => {
  initTabs();
  initChat();
  loadData();
});

// Tab Navigation
function initTabs() {
  const tabs = document.querySelectorAll('.nav-tab');
  const panes = document.querySelectorAll('.tab-pane');

  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      tabs.forEach(t => t.classList.remove('active'));
      panes.forEach(p => p.classList.remove('active'));

      tab.classList.add('active');
      const targetPane = document.getElementById(tab.dataset.tab);
      if (targetPane) targetPane.classList.add('active');
    });
  });
}

// Chat Functionality
function initChat() {
  const chatForm = document.getElementById('chatForm');
  const chatInput = document.getElementById('chatInput');
  const btnClear = document.getElementById('btnClearChat');

  chatForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const text = chatInput.value.trim();
    if (!text) return;

    appendUserMessage(text);
    chatInput.value = '';
    showTyping(true);

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text })
      });
      const data = await res.json();
      showTyping(false);

      if (data.error) {
        appendSystemMessage('Ошибка: ' + data.error);
        return;
      }

      appendFelicityMessage(data.reply, data.thought, data.emotion);
      if (data.emotion) updateEmotionState(data.emotion, data.thought);
      if (data.rag) updateRagChips(data.rag);

    } catch (err) {
      showTyping(false);
      appendSystemMessage('Не удалось связаться с сервером Felicity.');
    }
  });

  btnClear.addEventListener('click', () => {
    const list = document.getElementById('messagesList');
    list.innerHTML = `
      <div class="message system-msg">
        <div class="msg-content">✨ История чата очищена.</div>
      </div>`;
  });

  document.getElementById('btnSleepTrigger').addEventListener('click', async () => {
    if (confirm('Запустить процесс переупаковки памяти (Sleep Consolidation) для Felicity?')) {
      try {
        const res = await fetch('/api/sleep', { method: 'POST' });
        const data = await res.json();
        alert(data.message || 'Процесс сна успешно выполнен!');
        loadDiary();
      } catch (err) {
        alert('Ошибка при выполнении ночного сна.');
      }
    }
  });
}

function sendQuickMsg(text) {
  const input = document.getElementById('chatInput');
  input.value = text;
  document.getElementById('chatForm').dispatchEvent(new Event('submit'));
}

function appendUserMessage(text) {
  const list = document.getElementById('messagesList');
  const msgEl = document.createElement('div');
  msgEl.className = 'message user-msg';
  msgEl.innerHTML = `
    <div class="msg-bubble">${escapeHtml(text)}</div>
    <div class="msg-meta">${getCurrentTime()}</div>
  `;
  list.appendChild(msgEl);
  scrollToBottom();
}

function appendFelicityMessage(text, thought, emotion) {
  const list = document.getElementById('messagesList');
  const msgEl = document.createElement('div');
  msgEl.className = 'message felicity-msg';
  
  let thoughtHtml = thought ? `<div class="msg-thought">💭 ${escapeHtml(thought)}</div>` : '';
  
  msgEl.innerHTML = `
    ${thoughtHtml}
    <div class="msg-bubble">${escapeHtml(text)}</div>
    <div class="msg-meta">Felicity • ${getCurrentTime()}</div>
  `;
  list.appendChild(msgEl);
  scrollToBottom();
}

function appendSystemMessage(text) {
  const list = document.getElementById('messagesList');
  const msgEl = document.createElement('div');
  msgEl.className = 'message system-msg';
  msgEl.innerHTML = `<div class="msg-content">${escapeHtml(text)}</div>`;
  list.appendChild(msgEl);
  scrollToBottom();
}

function showTyping(show) {
  const indicator = document.getElementById('typingIndicator');
  if (show) {
    indicator.classList.remove('hidden');
  } else {
    indicator.classList.add('hidden');
  }
  scrollToBottom();
}

function scrollToBottom() {
  const list = document.getElementById('messagesList');
  list.scrollTop = list.scrollHeight;
}

function updateEmotionState(emotion, thought) {
  document.getElementById('stateEmotion').textContent = emotion;
  if (thought) document.getElementById('stateThought').textContent = `"${thought}"`;
}

function updateRagChips(ragItems) {
  const ragList = document.getElementById('ragList');
  if (!ragItems || ragItems.length === 0) return;
  ragList.innerHTML = ragItems.map(item => `<div class="rag-chip">#${escapeHtml(item)}</div>`).join('');
}

// Data loading and saving
async function loadData() {
  loadWorkingMem();
  loadDiary();
  loadPrompts();
  loadConfig();
}

async function loadWorkingMem() {
  try {
    const res = await fetch('/api/memory');
    const data = await res.json();
    document.getElementById('workingMemText').value = data.workingMemory || '';
  } catch (e) {}
}

document.getElementById('btnSaveWorkingMem').addEventListener('click', async () => {
  const content = document.getElementById('workingMemText').value;
  try {
    await fetch('/api/memory', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ workingMemory: content })
    });
    alert('Краткосрочная память сохранена!');
  } catch (e) {
    alert('Ошибка сохранения краткосрочной памяти.');
  }
});

async function loadDiary() {
  try {
    const res = await fetch('/api/diary');
    const data = await res.json();
    const timeline = document.getElementById('diaryTimeline');
    if (!data.entries || data.entries.length === 0) {
      timeline.innerHTML = '<p class="text-muted">Записей в дневнике пока нет.</p>';
      return;
    }
    timeline.innerHTML = data.entries.map(entry => `
      <div class="diary-card">
        <div class="diary-date">📅 ${escapeHtml(entry.date)}</div>
        <div class="diary-text">${escapeHtml(entry.content)}</div>
      </div>
    `).join('');
  } catch (e) {}
}

document.getElementById('btnAddDiaryEntry').addEventListener('click', async () => {
  const text = prompt('Введите новое воспоминание для дневника Фелисити:');
  if (!text) return;
  try {
    await fetch('/api/diary', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content: text, date: new Date().toLocaleDateString('ru-RU') })
    });
    loadDiary();
  } catch (e) {
    alert('Ошибка создания записи.');
  }
});

async function loadPrompts() {
  try {
    const res = await fetch('/api/prompts');
    const data = await res.json();
    document.getElementById('promptCharacterBase').value = data.characterBase || '';
    document.getElementById('promptCharacterApp').value = data.characterAppearance || '';
  } catch (e) {}
}

async function savePrompt(promptName) {
  let content = '';
  if (promptName === 'character_base') content = document.getElementById('promptCharacterBase').value;
  if (promptName === 'character_appearance') content = document.getElementById('promptCharacterApp').value;

  try {
    await fetch('/api/prompts', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: promptName, content })
    });
    alert(`Промпт ${promptName}.md сохранен!`);
  } catch (e) {
    alert('Ошибка сохранения промпта.');
  }
}

async function loadConfig() {
  try {
    const res = await fetch('/api/config');
    const data = await res.json();
    document.getElementById('configTomlText').value = data.configToml || '';
  } catch (e) {}
}

document.getElementById('btnSaveConfig').addEventListener('click', async () => {
  const content = document.getElementById('configTomlText').value;
  try {
    await fetch('/api/config', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ configToml: content })
    });
    alert('Конфигурация config.toml успешно сохранена!');
  } catch (e) {
    alert('Ошибка сохранения config.toml');
  }
});

document.getElementById('btnReloadConfig').addEventListener('click', loadConfig);

// Helpers
function escapeHtml(str) {
  return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

function getCurrentTime() {
  const now = new Date();
  return now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}
