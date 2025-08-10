const express = require('express');
const fs = require('fs').promises;
const path = require('path');

const app = express();
const PORT = process.env.PORT || 3000;
const DATA_FILE = path.join(__dirname, 'messages.json');

app.use(express.json());
app.use(express.static(__dirname));

// Load messages from file
async function loadMessages() {
    try {
        const data = await fs.readFile(DATA_FILE, 'utf8');
        return JSON.parse(data);
    } catch (error) {
        // If file doesn't exist, return empty array
        return [];
    }
}

// Save messages to file
async function saveMessages(messages) {
    await fs.writeFile(DATA_FILE, JSON.stringify(messages, null, 2));
}

// Generate unique ID
function generateId() {
    return Date.now().toString(36) + Math.random().toString(36).substr(2);
}

// Routes
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'display.html'));
});

app.get('/admin', (req, res) => {
    res.sendFile(path.join(__dirname, 'admin.html'));
});

app.get('/api/messages', async (req, res) => {
    try {
        const messages = await loadMessages();
        res.json(messages);
    } catch (error) {
        res.status(500).json({ error: 'Failed to load messages' });
    }
});

app.post('/api/messages', async (req, res) => {
    try {
        const { text } = req.body;
        
        if (!text || text.trim() === '') {
            return res.status(400).json({ error: 'Message text is required' });
        }
        
        const messages = await loadMessages();
        const newMessage = {
            id: generateId(),
            text: text.trim(),
            timestamp: new Date().toISOString()
        };
        
        messages.unshift(newMessage); // Add to beginning of array
        await saveMessages(messages);
        
        res.status(201).json(newMessage);
    } catch (error) {
        res.status(500).json({ error: 'Failed to save message' });
    }
});

app.delete('/api/messages/:id', async (req, res) => {
    try {
        const { id } = req.params;
        const messages = await loadMessages();
        const filteredMessages = messages.filter(msg => msg.id !== id);
        
        if (filteredMessages.length === messages.length) {
            return res.status(404).json({ error: 'Message not found' });
        }
        
        await saveMessages(filteredMessages);
        res.json({ success: true });
    } catch (error) {
        res.status(500).json({ error: 'Failed to delete message' });
    }
});

app.listen(PORT, () => {
    console.log(`🚀 Server running at http://localhost:${PORT}`);
    console.log(`📱 Display page: http://localhost:${PORT}/`);
    console.log(`⚙️  Admin page: http://localhost:${PORT}/admin`);
});