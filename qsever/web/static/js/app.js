(function () {
  'use strict';

  const chatArea = document.getElementById('chat-area');
  const messageInput = document.getElementById('message-input');
  const sendBtn = document.getElementById('send-btn');
  const imageInput = document.getElementById('image-input');
  const imagePreview = document.getElementById('image-preview');
  const profileSelect = document.getElementById('profile-select');
  const settingsBtn = document.getElementById('settings-btn');
  const settingsModal = document.getElementById('settings-modal');
  const settingsClose = document.getElementById('settings-close');
  const profileFormModal = document.getElementById('profile-form-modal');
  const profileFormClose = document.getElementById('profile-form-close');
  const galleryBtn = document.getElementById('gallery-btn');
  const galleryModal = document.getElementById('gallery-modal');
  const galleryClose = document.getElementById('gallery-close');
  const galleryGrid = document.getElementById('gallery-grid');
  const galleryEmpty = document.getElementById('gallery-empty');
  const usageBtn = document.getElementById('usage-btn');
  const clearBtn = document.getElementById('clear-btn');
  const usageModal = document.getElementById('usage-modal');
  const usageClose = document.getElementById('usage-close');
  const usageBody = document.getElementById('usage-body');
  const welcomeMessage = document.getElementById('welcome-message');

  let pendingImages = [];
  let isStreaming = false;
  let mathjaxTimer = null;

  function getSessionId() {
    let id = localStorage.getItem('qsever_session_id');
    if (!id) {
      id = crypto.randomUUID();
      localStorage.setItem('qsever_session_id', id);
    }
    return id;
  }

  const sessionId = getSessionId();

  function getHeaders() {
    return { 'X-Session-ID': sessionId };
  }

  function scrollToBottom() {
    chatArea.scrollTop = chatArea.scrollHeight;
  }

  function hideWelcome() {
    if (welcomeMessage) {
      welcomeMessage.style.display = 'none';
    }
  }

  function appendUserMessage(text, images) {
    hideWelcome();
    const msgDiv = document.createElement('div');
    msgDiv.className = 'message user';

    let content = '';
    if (images && images.length > 0) {
      content += images.map(img =>
        `<img src="/api/images/file/${img}" style="max-width:120px;max-height:120px;border-radius:8px;margin-right:8px;">`
      ).join('');
    }
    if (text) {
      content += `<span>${escapeHtml(text)}</span>`;
    }

    msgDiv.innerHTML = `<div class="message-bubble">${content}</div>`;
    chatArea.appendChild(msgDiv);
    scrollToBottom();
  }

  function appendAIBubble() {
    hideWelcome();
    const msgDiv = document.createElement('div');
    msgDiv.className = 'message ai';
    const bubble = document.createElement('div');
    bubble.className = 'message-bubble';
    bubble.innerHTML = '<div class="typing-indicator"><span></span><span></span><span></span></div>';
    msgDiv.appendChild(bubble);
    chatArea.appendChild(msgDiv);
    scrollToBottom();
    return bubble;
  }

  function renderMarkdown(element, text) {
    const LBRACKET = '%%LBRACKET%%';
    const RBRACKET = '%%RBRACKET%%';
    const LPAREN = '%%LPAREN%%';
    const RPAREN = '%%RPAREN%%';

    let protected_text = text
      .replace(/\\\[/g, LBRACKET)
      .replace(/\\\]/g, RBRACKET)
      .replace(/\\\(/g, LPAREN)
      .replace(/\\\)/g, RPAREN);

    let html = marked.parse(protected_text);

    html = html
      .replace(new RegExp(LBRACKET, 'g'), '\\[')
      .replace(new RegExp(RBRACKET, 'g'), '\\]')
      .replace(new RegExp(LPAREN, 'g'), '\\(')
      .replace(new RegExp(RPAREN, 'g'), '\\)');

    element.innerHTML = html;
  }

  function typesetMath(element) {
    if (window.MathJax && MathJax.typesetPromise) {
      MathJax.typesetPromise([element]).catch(() => {});
    }
  }

  function debounceTypeset(element) {
    if (mathjaxTimer) clearTimeout(mathjaxTimer);
    mathjaxTimer = setTimeout(() => {
      typesetMath(element);
    }, 200);
  }

  function showError(bubble, message) {
    bubble.className = 'message-bubble error-bubble';
    bubble.textContent = message;
  }

  function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  function parseSSEEvents(buffer) {
    const events = [];
    const parts = buffer.split('\n\n');
    let remaining = '';

    for (let i = 0; i < parts.length; i++) {
      const part = parts[i].trim();
      if (!part) continue;

      if (i === parts.length - 1 && !buffer.endsWith('\n\n')) {
        remaining = part;
        break;
      }

      let eventType = 'message';
      let data = '';

      for (const line of part.split('\n')) {
        if (line.startsWith('event:')) {
          eventType = line.slice(6).trim();
        } else if (line.startsWith('data:')) {
          data = line.slice(5).trim();
        }
      }

      if (data) {
        try {
          events.push({ type: eventType, data: JSON.parse(data) });
        } catch {
          events.push({ type: eventType, data: {} });
        }
      }
    }

    return { parsed: events, remaining };
  }

  async function sendMessage() {
    const text = messageInput.value.trim();
    if (!text && pendingImages.length === 0) return;
    if (isStreaming) return;

    const images = pendingImages.map(img => img.name);
    messageInput.value = '';
    messageInput.style.height = 'auto';
    clearImagePreview();
    isStreaming = true;
    sendBtn.disabled = true;

    appendUserMessage(text, images);
    const bubble = appendAIBubble();

    let fullText = '';
    let buffer = '';

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...getHeaders(),
        },
        body: JSON.stringify({ message: text, images }),
      });

      if (!response.ok) {
        const err = await response.json().catch(() => ({ detail: '请求失败' }));
        showError(bubble, err.detail || '请求失败');
        return;
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const { parsed, remaining } = parseSSEEvents(buffer);
        buffer = remaining;

        for (const event of parsed) {
          if (event.type === 'delta') {
            fullText += event.data.content;
            renderMarkdown(bubble, fullText);
            debounceTypeset(bubble);
            scrollToBottom();
          } else if (event.type === 'usage') {
            // usage info received
          } else if (event.type === 'error') {
            showError(bubble, event.data.message || '发生错误');
          } else if (event.type === 'done') {
            typesetMath(bubble);
          }
        }
      }

      if (fullText) {
        renderMarkdown(bubble, fullText);
        typesetMath(bubble);
      }
    } catch (err) {
      if (!fullText) {
        showError(bubble, '网络错误: ' + err.message);
      }
    } finally {
      isStreaming = false;
      sendBtn.disabled = false;
      messageInput.focus();
    }
  }

  function clearImagePreview() {
    pendingImages = [];
    imagePreview.innerHTML = '';
  }

  async function handleImageUpload(files) {
    for (const file of files) {
      if (!file.type.startsWith('image/')) continue;

      const formData = new FormData();
      formData.append('file', file);

      try {
        const res = await fetch('/api/images/upload', {
          method: 'POST',
          headers: getHeaders(),
          body: formData,
        });
        const data = await res.json();
        if (data.ok) {
          pendingImages.push({ name: data.filename, file });
          addImagePreviewItem(data.filename, file);
        }
      } catch (err) {
        console.error('Upload failed:', err);
      }
    }
    imageInput.value = '';
  }

  function addImagePreviewItem(name, file) {
    const item = document.createElement('div');
    item.className = 'image-preview-item';
    item.dataset.name = name;

    const img = document.createElement('img');
    img.src = URL.createObjectURL(file);
    item.appendChild(img);

    const removeBtn = document.createElement('button');
    removeBtn.className = 'remove-image';
    removeBtn.textContent = '×';
    removeBtn.onclick = () => {
      pendingImages = pendingImages.filter(i => i.name !== name);
      item.remove();
    };
    item.appendChild(removeBtn);

    imagePreview.appendChild(item);
  }

  async function loadConfig() {
    try {
      const res = await fetch('/api/config', { headers: getHeaders() });
      const data = await res.json();
      profileSelect.innerHTML = '';
      for (const p of data.profiles) {
        const opt = document.createElement('option');
        opt.value = p.name;
        opt.textContent = `${p.name} (${p.model_id})`;
        if (p.name === data.active_profile) opt.selected = true;
        profileSelect.appendChild(opt);
      }
    } catch (err) {
      console.error('Load config failed:', err);
    }
  }

  async function switchProfile(name) {
    try {
      const res = await fetch('/api/config/active', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json', ...getHeaders() },
        body: JSON.stringify({ profile: name }),
      });
      if (res.ok) {
        showToast(`已切换到 ${name}`);
      } else {
        const err = await res.json().catch(() => ({ detail: '切换失败' }));
        showToast(err.detail || '切换失败', 'error');
      }
    } catch (err) {
      showToast('切换失败', 'error');
    }
  }

  async function showUsage() {
    try {
      const res = await fetch('/api/usage', { headers: getHeaders() });
      const data = await res.json();
      usageBody.innerHTML = `
        <div class="usage-item"><span class="usage-label">请求数</span><span class="usage-value">${data.total_requests}</span></div>
        <div class="usage-item"><span class="usage-label">总 Tokens</span><span class="usage-value">${data.total_tokens.toLocaleString()}</span></div>
        <div class="usage-item"><span class="usage-label">输入 Tokens</span><span class="usage-value">${data.total_prompt_tokens.toLocaleString()}</span></div>
        <div class="usage-item"><span class="usage-label">输出 Tokens</span><span class="usage-value">${data.total_completion_tokens.toLocaleString()}</span></div>
        <div class="usage-item"><span class="usage-label">总费用</span><span class="usage-value">$${data.total_cost.toFixed(4)}</span></div>
        <div class="usage-item"><span class="usage-label">剩余预算</span><span class="usage-value">$${data.remaining_budget.toFixed(4)}</span></div>
      `;
      usageModal.classList.add('active');
    } catch (err) {
      console.error('Load usage failed:', err);
    }
  }

  async function clearConversation() {
    if (!confirm('确定清空对话历史？')) return;
    try {
      await fetch('/api/conversation', { method: 'DELETE', headers: getHeaders() });
      chatArea.innerHTML = '';
      chatArea.appendChild(welcomeMessage);
      welcomeMessage.style.display = '';
    } catch (err) {
      console.error('Clear failed:', err);
    }
  }

  function showToast(message, type = 'success') {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 3000);
  }

  async function openSettings() {
    settingsModal.classList.add('active');
    await loadProfileList();
    await loadGeneralSettings();
  }

  async function loadProfileList() {
    try {
      const res = await fetch('/api/config', { headers: getHeaders() });
      const data = await res.json();
      const listEl = document.getElementById('profile-list');
      listEl.innerHTML = '';
      
      for (const p of data.profiles) {
        const item = document.createElement('div');
        item.className = `profile-item ${p.name === data.active_profile ? 'active' : ''}`;
        item.innerHTML = `
          <div class="profile-info">
            <div class="profile-name">${escapeHtml(p.name)} ${p.name === data.active_profile ? '<span style="color:var(--primary)">[当前]</span>' : ''}</div>
            <div class="profile-detail">${escapeHtml(p.model_id)} | ${p.base_url} | Key: ${p.api_key_masked}</div>
          </div>
          <div class="profile-actions">
            <button class="btn-secondary" data-action="edit" data-name="${escapeHtml(p.name)}">编辑</button>
            <button class="btn-danger" data-action="delete" data-name="${escapeHtml(p.name)}">删除</button>
          </div>
        `;
        
        item.querySelector('[data-action="edit"]').addEventListener('click', () => {
          openProfileForm(p);
        });
        
        item.querySelector('[data-action="delete"]').addEventListener('click', () => {
          deleteProfile(p.name);
        });
        
        listEl.appendChild(item);
      }
      
      window._configData = data;
    } catch (err) {
      console.error('Load profile list failed:', err);
    }
  }

  async function loadGeneralSettings() {
    try {
      const res = await fetch('/api/config', { headers: getHeaders() });
      const data = await res.json();
      document.getElementById('setting-budget').value = data.settings.budget_limit;
      document.getElementById('setting-auto-open').checked = data.settings.auto_open_html;
    } catch (err) {
      console.error('Load settings failed:', err);
    }
  }

  function openProfileForm(profile = null) {
    document.getElementById('pf-original-name').value = profile ? profile.name : '';
    document.getElementById('pf-name').value = profile ? profile.name : '';
    document.getElementById('pf-api-key').value = profile ? profile.api_key_masked : '';
    document.getElementById('pf-base-url').value = profile ? profile.base_url : '';
    document.getElementById('pf-model').value = profile ? profile.model_id : '';
    document.getElementById('pf-input-price').value = profile ? profile.input_price : '';
    document.getElementById('pf-output-price').value = profile ? profile.output_price : '';
    document.getElementById('profile-form-title').textContent = profile ? '编辑预设' : '添加预设';
    profileFormModal.classList.add('active');
  }

  async function saveProfileForm() {
    const originalName = document.getElementById('pf-original-name').value;
    const name = document.getElementById('pf-name').value.trim();
    const body = {
      name: name,
      api_key: document.getElementById('pf-api-key').value,
      base_url: document.getElementById('pf-base-url').value,
      model_id: document.getElementById('pf-model').value,
      input_price: parseFloat(document.getElementById('pf-input-price').value) || 0,
      output_price: parseFloat(document.getElementById('pf-output-price').value) || 0,
    };
    
    try {
      let url, method;
      if (originalName) {
        url = `/api/config/profile/${encodeURIComponent(originalName)}`;
        method = 'PUT';
      } else {
        url = '/api/config/profile';
        method = 'POST';
      }
      
      const res = await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json', ...getHeaders() },
        body: JSON.stringify(body),
      });
      
      if (res.ok) {
        showToast('预设已保存');
        profileFormModal.classList.remove('active');
        await loadProfileList();
        await loadConfig();
      } else {
        const err = await res.json().catch(() => ({ detail: '保存失败' }));
        showToast(err.detail || '保存失败', 'error');
      }
    } catch (err) {
      showToast('保存失败', 'error');
    }
  }

  async function deleteProfile(name) {
    if (!confirm(`确定删除预设「${name}」？`)) return;
    try {
      const res = await fetch(`/api/config/profile/${encodeURIComponent(name)}`, {
        method: 'DELETE',
        headers: getHeaders(),
      });
      if (res.ok) {
        showToast('预设已删除');
        await loadProfileList();
        await loadConfig();
      } else {
        const err = await res.json().catch(() => ({ detail: '删除失败' }));
        showToast(err.detail || '删除失败', 'error');
      }
    } catch (err) {
      showToast('删除失败', 'error');
    }
  }

  async function saveGeneralSettings() {
    const body = {
      budget_limit: parseFloat(document.getElementById('setting-budget').value),
      auto_open_html: document.getElementById('setting-auto-open').checked,
    };
    try {
      const res = await fetch('/api/config/settings', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json', ...getHeaders() },
        body: JSON.stringify(body),
      });
      if (res.ok) {
        showToast('设置已保存');
      } else {
        showToast('保存失败', 'error');
      }
    } catch (err) {
      showToast('保存失败', 'error');
    }
  }

  async function openGallery() {
    galleryModal.classList.add('active');
    await loadGallery();
  }

  async function loadGallery() {
    try {
      const res = await fetch('/api/images', { headers: getHeaders() });
      const data = await res.json();
      
      galleryGrid.innerHTML = '';
      galleryEmpty.style.display = data.images.length === 0 ? '' : 'none';
      
      for (const img of data.images) {
        const item = document.createElement('div');
        item.className = 'gallery-item';
        if (pendingImages.some(pi => pi.name === img.name)) {
          item.classList.add('selected');
        }
        
        item.innerHTML = `
          <img src="${img.url}" alt="${escapeHtml(img.name)}" loading="lazy">
          <div class="gallery-item-info">
            <div>${escapeHtml(img.name)}</div>
            <div>${img.size_kb} KB</div>
          </div>
          <button class="gallery-delete" title="删除">&times;</button>
        `;
        
        item.addEventListener('click', (e) => {
          if (e.target.classList.contains('gallery-delete')) return;
          toggleImageFromGallery(img.name, item);
        });
        
        item.querySelector('.gallery-delete').addEventListener('click', async (e) => {
          e.stopPropagation();
          if (!confirm(`确定删除图片 ${img.name}？`)) return;
          try {
            const delRes = await fetch(`/api/images/${encodeURIComponent(img.name)}`, {
              method: 'DELETE',
              headers: getHeaders(),
            });
            if (delRes.ok) {
              pendingImages = pendingImages.filter(pi => pi.name !== img.name);
              updateImagePreview();
              await loadGallery();
            }
          } catch (err) {
            console.error('Delete image failed:', err);
          }
        });
        
        galleryGrid.appendChild(item);
      }
    } catch (err) {
      console.error('Load gallery failed:', err);
    }
  }

  function toggleImageFromGallery(name, element) {
    const idx = pendingImages.findIndex(pi => pi.name === name);
    if (idx >= 0) {
      pendingImages.splice(idx, 1);
      element.classList.remove('selected');
      showToast('已移除图片');
    } else {
      pendingImages.push({ name: name, file: null });
      element.classList.add('selected');
      showToast('已添加图片');
    }
    updateImagePreview();
  }

  function updateImagePreview() {
    imagePreview.innerHTML = '';
    for (const img of pendingImages) {
      const item = document.createElement('div');
      item.className = 'image-preview-item';
      item.dataset.name = img.name;
      
      const imgEl = document.createElement('img');
      if (img.file) {
        imgEl.src = URL.createObjectURL(img.file);
      } else {
        imgEl.src = `/api/images/file/${img.name}`;
      }
      item.appendChild(imgEl);
      
      const removeBtn = document.createElement('button');
      removeBtn.className = 'remove-image';
      removeBtn.textContent = '×';
      removeBtn.onclick = () => {
        pendingImages = pendingImages.filter(i => i.name !== img.name);
        updateImagePreview();
      };
      item.appendChild(removeBtn);
      
      imagePreview.appendChild(item);
    }
  }

  // Event listeners
  sendBtn.addEventListener('click', sendMessage);

  messageInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });

  messageInput.addEventListener('input', () => {
    messageInput.style.height = 'auto';
    messageInput.style.height = Math.min(messageInput.scrollHeight, 120) + 'px';
  });

  messageInput.addEventListener('paste', (e) => {
    const items = e.clipboardData.items;
    const files = [];
    for (let i = 0; i < items.length; i++) {
      if (items[i].type.startsWith('image/')) {
        const file = items[i].getAsFile();
        if (file) files.push(file);
      }
    }
    if (files.length > 0) {
      e.preventDefault();
      handleImageUpload(files);
      showToast(`已粘贴 ${files.length} 张图片`);
    }
  });

  const inputArea = document.querySelector('.input-area');
  inputArea.addEventListener('paste', (e) => {
    if (e.target === messageInput) return;
    const items = e.clipboardData.items;
    const files = [];
    for (let i = 0; i < items.length; i++) {
      if (items[i].type.startsWith('image/')) {
        const file = items[i].getAsFile();
        if (file) files.push(file);
      }
    }
    if (files.length > 0) {
      e.preventDefault();
      handleImageUpload(files);
      showToast(`已粘贴 ${files.length} 张图片`);
    }
  });

  inputArea.addEventListener('dragover', (e) => {
    e.preventDefault();
    inputArea.style.borderColor = 'var(--primary)';
  });

  inputArea.addEventListener('dragleave', (e) => {
    e.preventDefault();
    inputArea.style.borderColor = '';
  });

  inputArea.addEventListener('drop', (e) => {
    e.preventDefault();
    inputArea.style.borderColor = '';
    const files = e.dataTransfer.files;
    const imageFiles = Array.from(files).filter(f => f.type.startsWith('image/'));
    if (imageFiles.length > 0) {
      handleImageUpload(imageFiles);
      showToast(`已拖入 ${imageFiles.length} 张图片`);
    }
  });

  imageInput.addEventListener('change', (e) => {
    handleImageUpload(e.target.files);
  });

  profileSelect.addEventListener('change', (e) => {
    switchProfile(e.target.value);
  });

  usageBtn.addEventListener('click', showUsage);
  clearBtn.addEventListener('click', clearConversation);

  usageClose.addEventListener('click', () => {
    usageModal.classList.remove('active');
  });

  usageModal.addEventListener('click', (e) => {
    if (e.target === usageModal) {
      usageModal.classList.remove('active');
    }
  });

  settingsBtn.addEventListener('click', openSettings);
  settingsClose.addEventListener('click', () => settingsModal.classList.remove('active'));
  settingsModal.addEventListener('click', (e) => {
    if (e.target === settingsModal) settingsModal.classList.remove('active');
  });

  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
      document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
      btn.classList.add('active');
      document.getElementById(`tab-${btn.dataset.tab}`).classList.add('active');
    });
  });

  document.getElementById('add-profile-btn').addEventListener('click', () => openProfileForm());
  document.getElementById('pf-save').addEventListener('click', saveProfileForm);
  document.getElementById('pf-cancel').addEventListener('click', () => profileFormModal.classList.remove('active'));
  profileFormClose.addEventListener('click', () => profileFormModal.classList.remove('active'));
  profileFormModal.addEventListener('click', (e) => {
    if (e.target === profileFormModal) profileFormModal.classList.remove('active');
  });

  document.getElementById('save-settings-btn').addEventListener('click', saveGeneralSettings);

  galleryBtn.addEventListener('click', openGallery);
  galleryClose.addEventListener('click', () => galleryModal.classList.remove('active'));
  galleryModal.addEventListener('click', (e) => {
    if (e.target === galleryModal) galleryModal.classList.remove('active');
  });

  // Init
  loadConfig();
  messageInput.focus();
})();
