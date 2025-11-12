let currentContext = localStorage.getItem('boardContext') || 'personal';

function contextQuery() {
    return `?context=${encodeURIComponent(currentContext)}`;
}

async function translateMessage() {
    const text = document.getElementById('messageText').value.trim();
    const targetLanguage = document.getElementById('targetLanguage').value;

    if (!text) {
        showStatus('Please enter a message to translate', 'error');
        return;
    }

    showStatus('Translating...', 'success');

    try {
        const response = await fetch('/api/translate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text, target_language: targetLanguage })
        });

        const data = await response.json();

        if (response.ok) {
            document.getElementById('translatedText').value = data.translated_text;
            document.getElementById('translationGroup').style.display = 'block';
            showStatus('Translation complete! You can edit it before adding.', 'success');
        } else {
            showStatus('Translation failed: ' + (data.error || 'Unknown error'), 'error');
        }
    } catch {
        showStatus('Error: Could not translate message', 'error');
    }
}

function handleExpiryChange() {
    const preset = document.getElementById('expiryPreset').value;
    const customGroup = document.getElementById('customExpiryGroup');
    customGroup.style.display = preset === 'custom' ? 'block' : 'none';
}

function getExpiryDurationMinutes() {
    const preset = document.getElementById('expiryPreset').value;
    if (preset === 'never') return null;
    if (preset === 'custom') {
        const hours = parseInt(document.getElementById('customHours').value) || 0;
        const minutes = parseInt(document.getElementById('customMinutes').value) || 0;
        const total = (hours * 60) + minutes;
        return total > 0 ? total : null;
    }
    return parseInt(preset);
}

async function addMessage() {
    const translated = document.getElementById('translatedText').value.trim();
    const original = document.getElementById('messageText').value.trim();
    const text = translated || original;
    if (!text) return showStatus('Please enter a message', 'error');

    const expiry = getExpiryDurationMinutes();
    try {
        const body = { text };
        if (expiry !== null) body.expiry_duration_minutes = expiry;

        const res = await fetch('/api/messages' + contextQuery(), {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body)
        });

        if (res.ok) {
            document.getElementById('messageText').value = '';
            document.getElementById('translatedText').value = '';
            document.getElementById('translationGroup').style.display = 'none';
            showStatus('Message added successfully!', 'success');
            loadMessages();
        } else showStatus('Failed to add message', 'error');
    } catch {
        showStatus('Error: Could not add message', 'error');
    }
}

async function deleteMessage(id) {
    if (!confirm('Are you sure you want to delete this message?')) return;
    try {
        const res = await fetch(`/api/messages/${id}` + contextQuery(), { method: 'DELETE' });
        if (res.ok) {
            showStatus('Message deleted', 'success');
            loadMessages();
        } else showStatus('Failed to delete message', 'error');
    } catch {
        showStatus('Error: Could not delete message', 'error');
    }
}

async function loadMessages() {
    try {
        const res = await fetch('/api/messages' + contextQuery());
        const messages = await res.json();
        const list = document.getElementById('messagesList');
        if (!messages.length) return list.innerHTML = '<p>No messages yet</p>';

        list.innerHTML = messages.map(msg => {
            const expiry = msg.expiry_time
                ? `<span style="color: #e17055;">• Expires: ${new Date(msg.expiry_time).toLocaleString()}</span>`
                : '<span style="color: #00b894;">• Never expires</span>';
            return `
                <div class="message-item">
                    <div class="message-text">${msg.text}</div>
                    <div class="message-meta">
                        <div>
                            Added: ${new Date(msg.timestamp).toLocaleString()}<br>${expiry}
                        </div>
                        <button class="delete-btn" onclick="deleteMessage('${msg.id}')">Delete</button>
                    </div>
                </div>`;
        }).join('');
    } catch {
        document.getElementById('messagesList').innerHTML = '<p>Could not load messages</p>';
    }
}

function showStatus(message, type) {
    const el = document.getElementById('status');
    el.innerHTML = `<div class="${type}">${message}</div>`;
    setTimeout(() => el.innerHTML = '', 3000);
}

async function loadWorkspaces() {
    try {
        const res = await fetch('/api/workspaces');
        if (!res.ok) return;
        const list = await res.json();
        const select = document.getElementById('boardContext');
        select.innerHTML = '<option value="personal">My Board</option>' +
            list.map(ws => `<option value="workspace:${ws.id}">👥 ${ws.name}</option>`).join('');
        if (![...select.options].some(o => o.value === currentContext))
            currentContext = 'personal';
        select.value = currentContext;
    } catch {}
}

document.getElementById('boardContext').addEventListener('change', e => {
    currentContext = e.target.value;
    localStorage.setItem('boardContext', currentContext);
    document.getElementById('previewLink').href = '/' + `?context=${encodeURIComponent(currentContext)}`;
    loadMessages();
});

document.getElementById('newWorkspaceBtn').addEventListener('click', async () => {
    const name = prompt('Name for the new shared board:');
    if (!name) return;
    try {
        const res = await fetch('/api/workspaces', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name })
        });
        if (res.ok) {
            showStatus('Shared board created', 'success');
            await loadWorkspaces();
        } else {
            const err = await res.json();
            showStatus(err.error || 'Failed to create shared board', 'error');
        }
    } catch {
        showStatus('Error creating shared board', 'error');
    }
});

document.getElementById('inviteBtn').addEventListener('click', async () => {
    if (!currentContext.startsWith('workspace:'))
        return showStatus('Switch to a shared board first', 'error');
    const email = prompt('Enter the email to invite:');
    if (!email) return;
    const wsId = currentContext.split(':')[1];
    try {
        const res = await fetch(`/api/workspaces/${wsId}/invite`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email })
        });
        if (res.ok) showStatus('Invite sent', 'success');
        else {
            const err = await res.json();
            showStatus(err.error || 'Failed to send invite', 'error');
        }
    } catch {
        showStatus('Error sending invite', 'error');
    }
});

(async function init() {
    await loadWorkspaces();
    document.getElementById('previewLink').href = '/' + `?context=${encodeURIComponent(currentContext)}`;
    await loadMessages();
})();
