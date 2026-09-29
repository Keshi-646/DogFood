# Five-Minute Demo Script

## 0:00–0:30 — Start

Run:

```bash
docker compose up --build
```

Open `http://localhost:8000`.

Explain: this is a self-hostable HackForge event portal with seeded data.

## 0:30–1:15 — Participant lifecycle

Login as:
`alice@example.com / alice123`

Show the seeded team and submission in the public gallery.

Optionally demonstrate registration with a new participant through `POST /api/register`.

## 1:15–2:00 — Organizer assignment

Use organizer credentials:

`organizer@example.com / organizer123`

Assign a submission to a judge using:

```http
POST /api/assignments
{
  "submission_id": 1,
  "judge_id": 3
}
```

Explain that assignments are persisted and duplicate pairs are rejected.

## 2:00–3:15 — Judge scoring

Login as Judge One:

`judge1@example.com / judge123`

Call:

```http
GET /api/judge/assignments
```

Score each criterion through:

```http
POST /api/judge/score
```

Explain the 40/30/30 weighted rubric.

## 3:15–4:00 — Security demonstration

Switch to Judge Two:

`judge2@example.com / judge123`

Request Judge One's submission score:

```http
GET /api/judge/scores/1
```

Show HTTP 403.

Explain: score isolation is enforced by the backend, not merely hidden in the UI.

## 4:00–4:35 — Normalize and rank

Switch back to organizer and call:

```http
POST /api/normalize
```

Then:

```http
GET /api/results
```

Explain the event-relative min-max normalization and stored rank.

## 4:35–5:00 — Gallery/export

Show:

```http
GET /api/gallery
GET /api/export/submissions.csv
```

Conclude by showing the repository documentation and tests.
