# OtakuRate

Personal anime and manga rating platform.

## Initial direction

- Web application first
- Subjective rating system for anime and manga/manhwa
- Separate title records from user ratings
- External source identifiers kept separately from OtakuRate data
- Future integrations through adapters
- Future browser extension for account/list synchronization

## Stack

- Python
- FastAPI
- SQLAlchemy
- SQLite for the initial local database
- Server-rendered HTML with Jinja2

## Run

```bash
pip install -e .
uvicorn otakurate.main:app --reload
```
