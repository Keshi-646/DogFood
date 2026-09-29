# Judging Strategy

## 1. Judge assignment strategy

Assignments are stored explicitly in the `assignments` table.

The organizer selects a submission and a judge. A unique constraint prevents duplicate assignment pairs.

For a larger event, the recommended extension is deterministic balanced assignment:
1. Build the eligible submission list.
2. Build the active judge list.
3. Shuffle using a recorded event seed.
4. Round-robin submissions across judges.
5. Reject assignments where the judge belongs to the submission team.
6. Continue until each submission reaches the configured number of judges.

This keeps assignment logic auditable and avoids accidental duplicate assignment.

## 2. Scoring methodology

The seeded rubric uses:

| Criterion | Weight |
|---|---:|
| Technical Quality | 40% |
| Impact & Innovation | 30% |
| UX & Completeness | 30% |

Each criterion is scored from 0 to 100.

A judge's weighted total is:

`Σ(score × weight / 100)`

The total therefore remains on a 0–100 scale.

## 3. Normalization method

Multiple judges may use slightly different parts of the scoring range. The system first averages the weighted judge totals for each submission.

Then event-level min-max normalization is applied:

`N = (R - Rmin) / (Rmax - Rmin) × 100`

where:
- `R` = submission raw average
- `Rmin` = lowest raw average in the event
- `Rmax` = highest raw average in the event

Tie edge cases:
- If `Rmax == Rmin > 0`, every submission receives 100.
- If `Rmax == Rmin == 0`, every submission receives 0.

## 4. Integrity controls

The key integrity requirement is backend judge isolation.

A judge may access scores only for submissions assigned to that judge. The server checks the assignment against the authenticated user before returning score data.

A malicious client cannot bypass this by calling the API directly.

Organizers/admins can access scores across submissions for administration and result processing.

## 5. Results

The organizer runs normalization after judging is complete. Results are ranked by normalized score descending and stored in `normalized_results`.

The public results endpoint exposes the final normalized score and rank, while judge-specific score access remains assignment-scoped.

## 6. Rationale

The approach favors:
- reproducibility
- simple auditability
- explicit assignment records
- transparent weighted scoring
- deterministic normalization
- server-side authorization
- easy local testing

It avoids hidden frontend-only rules and avoids opaque scoring transformations.
