# Data Model

## Entities

### users
- `id` PK
- `name`
- `email` UNIQUE
- `password`
- `role`: participant | judge | organizer | admin

### events
- `id` PK
- `name`
- `slug` UNIQUE
- `status`

### teams
- `id` PK
- `event_id` FK → events
- `name`
- `captain_id` FK → users

### team_members
- composite PK `(team_id, user_id)`
- links users to teams

### submissions
- `id` PK
- `event_id` FK
- `team_id` FK
- `title`
- `description`
- `repo_url`
- `demo_url`
- `status`
- `created_at`

### rubric_criteria
- `id` PK
- `event_id` FK
- `name`
- `weight`

### assignments
- `id` PK
- `submission_id` FK
- `judge_id` FK
- UNIQUE `(submission_id, judge_id)`

### scores
- `id` PK
- `assignment_id` FK
- `criterion_id` FK
- `score` 0–100
- UNIQUE `(assignment_id, criterion_id)`

### normalized_results
- `submission_id` PK/FK
- `raw_score`
- `normalized_score`
- `rank`

## Relationships

```text
Event 1---N Team
Team N---N User
Team 1---N Submission
Event 1---N RubricCriterion
Submission 1---N Assignment N---1 Judge(User)
Assignment 1---N Score N---1 RubricCriterion
Submission 1---1 NormalizedResult
```

## Seed/import path

Seed data is created by `seed_db()` in `app/db.py`, invoked by `run.py` at startup. The seed is idempotent: if users already exist, it does not duplicate the dataset.

## Export path

`GET /api/export/submissions.csv` returns a CSV containing:
- submission id
- title
- team
- repository URL
- demo URL
- submission status

Only organizer/admin roles can access the export.

## Future import extension

A production deployment can add CSV/JSON import endpoints using the same relational IDs. Imports should validate event membership, unique emails, team membership, rubric weights and foreign keys before committing a transaction.
