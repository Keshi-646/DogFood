# Architecture

## Overview

HackForge is a single-container Flask application backed by SQLite. The design intentionally minimizes infrastructure so `docker compose up` can start a seeded portal without cloud services.

```text
Browser
  |
  v
Flask HTTP API + server-rendered gallery
  |
  +--> Authentication / RBAC
  |
  +--> Event / Team / Submission services
  |
  +--> Judge assignment + score isolation
  |
  +--> Weighted scoring + normalization
  |
  v
SQLite
```

## Major decisions

### Flask + SQLite

Flask keeps the reference implementation small and easy to self-host. SQLite is sufficient for a seeded evaluation deployment and removes the need for a separate database service.

### Backend authorization

Authorization is enforced in API handlers, not only in the UI. In particular, `/api/judge/scores/<submission_id>` checks that the authenticated judge has an assignment for the requested submission.

### Relational model

Users, events, teams, submissions, rubric criteria, assignments and scores are normalized into separate tables with foreign keys. This prevents duplicated identity and judging data.

### Weighted rubric

Each criterion has a percentage weight. A judge's submission score is:

`judge_total = Σ(score / 100 × criterion_weight)`

where criterion weights sum to 100.

### Normalization

The implementation first averages judge totals for each submission. It then min-max normalizes the event's submission totals to 0–100:

`normalized = (raw - min_raw) / (max_raw - min_raw) × 100`

If all raw scores are equal and positive, all submissions receive 100. If all are zero, all receive 0.

### Public/private boundary

Gallery and results are public. Judge assignment and scoring operations require authenticated judge or organizer/admin roles. Judge score visibility is assignment-scoped.

## Lifecycle

1. User registers.
2. Participant creates a team.
3. Team submits a project.
4. Organizer assigns judges.
5. Judge sees only their assignments.
6. Judge scores rubric criteria.
7. Organizer normalizes results.
8. Results are ranked.
9. Public gallery exposes submitted projects.
10. Organizer can export submissions as CSV.

## Operability

- One Docker Compose service
- Persistent named volume for SQLite
- Environment variables for database and secret
- Seed data created automatically
- Tests runnable without external services
