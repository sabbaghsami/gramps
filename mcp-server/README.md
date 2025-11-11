# Grandad Reminders MCP Server

An MCP (Model Context Protocol) server that allows AI assistants like ChatGPT and Claude to send messages to your grandad's display screen via the Railway app.

## What it does

This MCP server provides a single tool (`send_message_to_grandad`) that:
1. Accepts a message in any language
2. Posts it to the Railway app API
3. Displays it on grandad's screen

## Use Case

**In ChatGPT Desktop:**
```
User: "Send a message to grandad saying 'Dinner at 4 o'clock tonight' in Syrian Arabic"

ChatGPT:
1. Translates to Syrian Arabic: "العشاء الساعة 4 الليلة"
2. Calls: send_message_to_grandad(message="العشاء الساعة 4 الليلة")
3. Message appears on grandad's screen!
```

## Installation

### 1. Install dependencies

```bash
cd mcp-server
pip install -r requirements.txt
```

### 2. Configure ChatGPT Desktop

Add this to your ChatGPT Desktop MCP settings file:

**On macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`

**On Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "grandad-reminders": {
      "command": "python3",
      "args": [
        "/absolute/path/to/grandad-reminders/mcp-server/server.py"
      ],
      "env": {
        "GRANDAD_APP_URL": "https://gramps-production.up.railway.app"
      }
    }
  }
}
```

**Important:** Replace `/absolute/path/to/` with your actual path!

### 3. Restart ChatGPT Desktop

Close and reopen ChatGPT Desktop for the changes to take effect.

## Usage

Once configured, you can use natural language in ChatGPT:

```
✅ "Send grandad a message saying 'Good morning' in Arabic"
✅ "Tell grandad dinner is at 6pm tonight in Syrian Arabic"
✅ "Post a reminder to grandad's screen: 'Doctor appointment tomorrow at 10am' in Arabic"
✅ "Message grandad in Lebanese Arabic: 'Call me when you're free'"
```

ChatGPT will:
1. Understand your intent
2. Translate to the appropriate Arabic dialect
3. Call the MCP tool with the translated message
4. Confirm when the message is sent

## Available Tools

### `send_message_to_grandad`

Sends a message to grandad's display screen.

**Parameters:**
- `message` (string, required): The message to display. Can be in any language.

**Returns:**
- Success message with message ID and timestamp
- Or error message if something went wrong

## Environment Variables

- `GRANDAD_APP_URL` - The URL of your Railway app (default: https://gramps-production.up.railway.app)

## Testing

Test the MCP server manually:

```bash
# Install MCP inspector
pip install mcp

# Test the server
mcp dev mcp-server/server.py
```

## Troubleshooting

### ChatGPT doesn't see the tool

1. Check the config file path is correct
2. Make sure you used absolute paths (not relative `~/` paths)
3. Restart ChatGPT Desktop completely
4. Check ChatGPT logs for MCP errors

### "Connection refused" error

1. Verify your Railway app is running: visit the URL in a browser
2. Check the `GRANDAD_APP_URL` is correct in your config
3. Ensure your Railway app API endpoint `/api/messages` works

### Message not appearing on display

1. Open the admin page: `https://gramps-production.up.railway.app/admin`
2. Check if the message was added to the list
3. The display page auto-refreshes every 30 seconds

## Architecture

```
ChatGPT Desktop
      ↓
   MCP Server (this)
      ↓
   Railway App API (/api/messages)
      ↓
   PostgreSQL Database
      ↓
   Display Page (Grandad's screen)
```

## Development

The MCP server is a simple Python script using:
- `mcp` - Model Context Protocol SDK
- `httpx` - Async HTTP client for API calls
- `stdio` transport - Communication with ChatGPT Desktop

## License

MIT
