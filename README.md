# Grandad's Reminder System

A simple web application to display reminder messages for grandad on a screen in his house. Built with Python Flask and supports both PostgreSQL (production) and JSON file storage (local development).

## Features

- 📱 Large, readable text display optimized for screens
- ⚙️ Simple admin interface for adding/removing messages
- 🔄 Auto-refresh display every 30 seconds
- 💾 Persistent storage with PostgreSQL or JSON file
- 🎨 Mobile-friendly admin panel
- 🚀 Production-ready with modular, object-oriented architecture

## Architecture

The application follows clean architecture principles with separation of concerns:

```
├── app.py           # Flask application with ReminderApp class
├── config.py        # Configuration and constants
├── database.py      # Database interface (PostgreSQL & JSON)
├── models.py        # Message data model
├── requirements.txt # Python dependencies
├── admin.html       # Admin interface
└── display.html     # Display page
```

## Setup

### Local Development

1. **Create and activate a virtual environment** (recommended):
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Start the development server**:
   ```bash
   python app.py
   ```

4. **Open your browser**:
   - **Display page** (for grandad's screen): http://localhost:3000/
   - **Admin page** (for family to add messages): http://localhost:3000/admin

The app will automatically use JSON file storage for local development.

### Production Deployment (Railway)

The application is configured to automatically detect and use PostgreSQL when deployed:

1. **Push to Railway**:
   ```bash
   git push origin main
   ```

2. **Railway automatically**:
   - Detects Python app from `requirements.txt`
   - Connects to PostgreSQL database via `DATABASE_URL`
   - Runs the application with proper production settings

3. **Database persistence**:
   - Messages are stored in PostgreSQL
   - Survives deployments and restarts
   - Automatic schema initialization on first run

## Environment Variables

- `DATABASE_URL` - PostgreSQL connection string (auto-set by Railway)
- `PORT` - Server port (default: 3000)
- `DEBUG` - Enable debug mode (default: False)

## Usage

### For Family Members
1. Visit the `/admin` page
2. Type a message for grandad
3. Click "Add Message"
4. Messages appear immediately on the display

### For Grandad
- The display page (`/`) shows all messages in large, readable text
- Auto-refreshes every 30 seconds
- Fullscreen mode available for dedicated displays

## Technology Stack

- **Backend**: Python 3.13+ with Flask
- **Database**: PostgreSQL (production) / JSON (development)
- **Database Driver**: psycopg3
- **Production Server**: Gunicorn
- **Deployment**: Railway
- **Architecture**: OOP with clean separation of concerns

## Development

### Project Structure

- `app.py` - Main application with Flask routes and business logic
- `config.py` - Centralized configuration management
- `database.py` - Abstract database interface with multiple implementations
- `models.py` - Data models using Python dataclasses
- `requirements.txt` - Python package dependencies

### Design Patterns Used

- **Factory Pattern**: Database selection based on environment
- **Strategy Pattern**: Swappable database implementations
- **Application Factory**: Production WSGI server support
- **Single Responsibility**: Each module has one clear purpose

### Adding New Features

The modular architecture makes it easy to extend:

1. **New storage backend**: Implement `DatabaseInterface` in `database.py`
2. **New configuration**: Add to `Config` class in `config.py`
3. **New data fields**: Extend `Message` model in `models.py`
4. **New routes**: Add methods to `ReminderApp` class in `app.py`

## Deployment Options

### Railway (Current)
- Deployed at: https://gramps-production.up.railway.app
- PostgreSQL database included
- Automatic deployments from Git

### Alternative Options
1. **Raspberry Pi** - Run locally in grandad's house
2. **Docker** - Containerized deployment
3. **Heroku** - Similar to Railway
4. **Self-hosted** - Any server with Python 3.13+


