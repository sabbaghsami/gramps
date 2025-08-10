# Grandad's Reminder System

A simple web app to display messages for grandad on a screen in his house.

## Setup

1. Install dependencies:
   ```bash
   npm install
   ```

2. Start the server:
   ```bash
   npm start
   ```

3. Open your browser:
   - **Display page** (for grandad's screen): http://localhost:3000/
   - **Admin page** (for family to add messages): http://localhost:3000/admin

## Usage

- Family members use the admin page to add/delete messages
- The display page shows all messages in large, readable text
- Messages auto-refresh every 30 seconds
- All messages are stored in `messages.json`

## Deployment

For grandad's house, you can:
1. Run this on a Raspberry Pi
2. Set up port forwarding on your router
3. Use a service like ngrok for testing
4. Deploy to a cloud service like Heroku or Railway

## Features

- Large, readable text (48px)
- Simple admin interface
- Auto-refresh display
- Persistent message storage
- Mobile-friendly admin panel