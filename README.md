# DocBot - WhatsApp Doctor Appointment System

A WhatsApp-based appointment management system for a single-doctor practice in India. Patients book online (paid) or offline (free) consultations entirely through a button-based WhatsApp bot, with full automation for payments (Razorpay), video consultations (Google Meet), reminders, cancellations with refunds, and prescription delivery.

## Quick Start

### Prerequisites

- Python 3.11+
- [UV package manager](https://github.com/astral-sh/uv)

### Installation

```bash
# Install dependencies
uv sync

# Copy example config
cp config.example.json config.test.json

# Set environment
export DOCBOT_ENV=test

# Edit config.test.json with your values
```

### Running

```bash
# Start development server
uv run uvicorn docbot.main:app --reload --host 0.0.0.0 --port 8000
```

### Health Check

```bash
curl http://localhost:8000/health
curl http://localhost:8000/ready
```

## Project Structure

```
docbot/
├── src/docbot/           # Main application package
│   ├── __init__.py       # Package initialization
│   ├── main.py           # FastAPI app with health endpoints
│   ├── config.py         # Configuration system
│   └── logging_config.py # Structured JSON logging
├── config.example.json   # Configuration template
├── pyproject.toml        # UV project definition
└── .planning/            # Development planning artifacts
```

## Configuration

Configuration is loaded from environment-specific JSON files:

- `config.test.json` - Test/development configuration
- `config.prod.json` - Production configuration

Set `DOCBOT_ENV` environment variable to choose which config to load (defaults to `test`).

See `config.example.json` for all available configuration options.

## Development

### Project Status

Phase 1 (Foundation) - In Progress

See `.planning/STATE.md` for current project status and `.planning/ROADMAP.md` for the complete development roadmap.

### Testing

```bash
# Run tests
uv run pytest

# Run with coverage
uv run pytest --cov=docbot
```

## Architecture

- **Backend Framework:** FastAPI with Python 3.11+
- **Package Manager:** UV for fast, reliable dependency management
- **Database:** SQLite (single-doctor deployment)
- **Logging:** Structured JSON logs with request correlation
- **Configuration:** Environment-based JSON with Pydantic validation

## Core Features (Planned)

- WhatsApp bot with button-based flows (multi-language)
- Online/offline appointment booking
- Razorpay payment integration (UPI/QR)
- Google Calendar sync with Meet links
- Automated reminders and cancellations
- Prescription generation and delivery
- Doctor web dashboard with Google OAuth

## License

Private project for single-doctor practice.
