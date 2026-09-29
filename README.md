# HackForge Dogfood 2026

A self-hostable, open-source hackathon registration, submission, judging and results portal.

## What is included

- Participant registration and team creation
- Submission workflow
- Organizer/admin judge assignment
- Judge-only assignment access
- Backend-enforced judge score isolation
- Weighted rubric scoring
- Normalization to a 0–100 scale
- Ranked results
- Public gallery
- CSV export
- Seeded demo data
- Docker Compose one-command startup
- Automated tests

## Quick start

```bash
docker compose up --build
```

Open http://localhost:8000

The container seeds a complete demo event automatically.

### Demo accounts

| Role | Email | Password |
|---|---|---|
| Participant | alice@example.com | alice123 |
| Participant | bob@example.com | bob123 |
| Judge | judge1@example.com | judge123 |
| Judge | judge2@example.com | judge123 |
| Organizer | organizer@example.com | organizer123 |
| Admin | admin@example.com | admin123 |

## Local development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python run.py .dogfood.toml
```

Run tests:

```bash
pytest -q
```

## Acceptance

The acceptance harness configuration is `.dogfood.toml`. The requested command is:

```bash
python3 run.py .dogfood.toml
```

This starts the seeded portal on port 8000.

## Security boundary

Judge score endpoints verify the authenticated judge owns the assignment. A judge cannot query another judge's scores through the API even if the frontend is bypassed.

## Repository layout

- `app/` Flask application and database
- `templates/` public portal page
- `tests/` automated tests
- `docker-compose.yml` deployment
- `ARCHITECTURE.md` technical design
- `DATA-MODEL.md` schema and import/export paths
- `JUDGING.md` assignment and scoring methodology
- `acceptance-report.txt` acceptance evidence
- `DEMO_SCRIPT.md` five-minute demo runbook

## License

MIT License. See `LICENSE`.
