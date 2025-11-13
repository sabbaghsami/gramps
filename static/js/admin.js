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

// Email list management
let pendingInvites = [];

function showModalError(message) {
    const errorEl = document.getElementById('modalError');
    errorEl.textContent = message;
    errorEl.classList.add('show');

    // Auto-hide after 3 seconds
    setTimeout(() => {
        errorEl.classList.remove('show');
    }, 3000);
}

function hideModalError() {
    const errorEl = document.getElementById('modalError');
    errorEl.classList.remove('show');
}

// Inline error for the single Invite modal
function showInviteModalError(message) {
    const el = document.getElementById('inviteModalError');
    if (!el) return;
    el.textContent = message;
    el.classList.add('show');
}

function hideInviteModalError() {
    const el = document.getElementById('inviteModalError');
    if (!el) return;
    el.classList.remove('show');
}

function addEmailToList() {
    const emailInput = document.getElementById('inviteEmailInput');
    const email = emailInput.value.trim().toLowerCase();

    // Validate email
    if (!email) {
        showModalError('Please enter an email address');
        return;
    }

    // Basic email validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
        showModalError('Please enter a valid email address');
        return;
    }

    // Check for duplicates
    if (pendingInvites.includes(email)) {
        showModalError('Email already added');
        return;
    }

    // Add to list
    pendingInvites.push(email);
    emailInput.value = '';
    hideModalError();
    renderEmailList();
}

function removeEmail(email) {
    pendingInvites = pendingInvites.filter(e => e !== email);
    renderEmailList();
}

function renderEmailList() {
    const emailList = document.getElementById('emailList');

    if (pendingInvites.length === 0) {
        emailList.innerHTML = '<div class="email-list-empty">No emails added yet</div>';
        return;
    }

    emailList.innerHTML = pendingInvites.map(email => `
        <div class="email-chip">
            <span class="email-chip-text">${email}</span>
            <button class="email-chip-remove" onclick="removeEmail('${email}')" type="button">
                ×
            </button>
        </div>
    `).join('');
}

// Modal functions
function openModal(modalId) {
    const overlay = document.getElementById('modalOverlay');
    const modal = document.getElementById(modalId);

    // Hide all modals first
    document.querySelectorAll('.modal').forEach(m => m.style.display = 'none');

    // Show the requested modal
    modal.style.display = 'block';
    overlay.classList.add('show');

    // Clear any previous errors
    hideModalError();
    hideInviteModalError();

    // Initialize email list if opening workspace modal
    if (modalId === 'newWorkspaceModal') {
        renderEmailList();
    }

    // Focus the input field
    setTimeout(() => {
        const input = modal.querySelector('input');
        if (input) input.focus();
    }, 100);
}

function closeModal() {
    const overlay = document.getElementById('modalOverlay');
    overlay.classList.remove('show');

    // Clear errors
    hideModalError();

    // Clear input fields and email list after animation
    setTimeout(() => {
        document.getElementById('workspaceName').value = '';
        document.getElementById('inviteEmail').value = '';
        document.getElementById('inviteEmailInput').value = '';
        pendingInvites = [];
        renderEmailList();
    }, 300);
}

// Close modal on overlay click
document.getElementById('modalOverlay').addEventListener('click', (e) => {
    if (e.target.id === 'modalOverlay') {
        closeModal();
    }
});

// Close modal on Escape key
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        closeModal();
    }
});

// Submit new workspace
async function submitNewWorkspace() {
    const name = document.getElementById('workspaceName').value.trim();
    if (!name) {
        showModalError('Please enter a board name');
        return;
    }

    try {
        // Create the workspace
        const res = await fetch('/api/workspaces', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name })
        });

        if (res.ok) {
            const workspace = await res.json();
            const wsId = workspace.id;

            // Send invites if there are any
            if (pendingInvites.length > 0) {
                let successCount = 0;
                let failCount = 0;
                const notRegistered = [];

                for (const email of pendingInvites) {
                    try {
                        const inviteRes = await fetch(`/api/workspaces/${wsId}/invite`, {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ email })
                        });
                        if (inviteRes.ok) {
                            successCount++;
                        } else {
                            failCount++;
                            const err = await inviteRes.json().catch(() => ({}));
                            if (err && err.error && err.error.toLowerCase().includes('no user')) {
                                notRegistered.push(email);
                            }
                        }
                    } catch {
                        failCount++;
                    }
                }

                // If there are unregistered emails, keep modal open and show them inline
                if (notRegistered.length > 0) {
                    showModalError(`These emails are not registered: ${notRegistered.join(', ')}`);
                    pendingInvites = notRegistered;
                    renderEmailList();
                } else {
                    closeModal();
                }
                // Only show page toast if there were no failures
                if (failCount === 0) {
                    if (successCount > 0) {
                        showStatus(`Board created and ${successCount} invite(s) sent!`, 'success');
                    } else {
                        showStatus('Shared board created', 'success');
                    }
                }
            } else {
                showStatus('Shared board created', 'success');
                closeModal();
            }

            await loadWorkspaces();
        } else {
            const err = await res.json();
            showStatus(err.error || 'Failed to create shared board', 'error');
        }
    } catch {
        showStatus('Error creating shared board', 'error');
    }
}

// Submit invite
async function submitInvite() {
    if (!currentContext.startsWith('workspace:')) {
        showStatus('Switch to a shared board first', 'error');
        closeModal();
        return;
    }

    const email = document.getElementById('inviteEmail').value.trim();
    if (!email) { showInviteModalError('Please enter an email address'); return; }

    const wsId = currentContext.split(':')[1];
    try {
        const res = await fetch(`/api/workspaces/${wsId}/invite`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email })
        });
        const data = await res.json().catch(() => ({}));
        if (res.ok) { showStatus('Invite sent', 'success'); closeModal(); }
        else { const msg = (data && (data.error || data.message)) || 'Failed to send invite'; showInviteModalError(msg); }
    } catch {
        showStatus('Error sending invite', 'error');
    }
}

// Handle Enter key in modal inputs
document.getElementById('workspaceName').addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        e.preventDefault();
        // If focused on name, check if we should submit or focus email input
        const emailInput = document.getElementById('inviteEmailInput');
        if (emailInput && emailInput.offsetParent !== null) {
            // Email section is visible, focus it
            emailInput.focus();
        } else {
            submitNewWorkspace();
        }
    }
});

document.getElementById('inviteEmailInput').addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        e.preventDefault();
        addEmailToList();
    }
});

document.getElementById('inviteEmail').addEventListener('keypress', (e) => {
    if (e.key === 'Enter') submitInvite();
});

document.getElementById('newWorkspaceBtn').addEventListener('click', () => {
    openModal('newWorkspaceModal');
});

document.getElementById('inviteBtn').addEventListener('click', () => {
    if (!currentContext.startsWith('workspace:')) {
        showStatus('Switch to a shared board first', 'error');
        return;
    }
    openModal('inviteModal');
});

// Dropdown menu toggle
const menuToggle = document.getElementById('menuToggle');
const dropdownMenu = document.getElementById('dropdownMenu');

menuToggle.addEventListener('click', (e) => {
    e.stopPropagation();
    dropdownMenu.classList.toggle('show');
});

// Close dropdown when clicking outside
document.addEventListener('click', (e) => {
    if (!menuToggle.contains(e.target) && !dropdownMenu.contains(e.target)) {
        dropdownMenu.classList.remove('show');
    }
});

// Close dropdown when clicking a menu item
dropdownMenu.addEventListener('click', (e) => {
    if (e.target.closest('.dropdown-item')) {
        dropdownMenu.classList.remove('show');
    }
});

(async function init() {
    await loadWorkspaces();
    document.getElementById('previewLink').href = '/' + `?context=${encodeURIComponent(currentContext)}`;
    await loadMessages();
})();
