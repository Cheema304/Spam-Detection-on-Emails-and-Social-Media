# Four-Member Team Allocation

Use actual member names/IDs when setting up Jira and GitHub.

| Member | Primary ownership | Secondary ownership | Required evidence |
|---|---|---|---|
| Member 1 — Project Lead / Business Analyst | Week 1 charter, stakeholders, success criteria, Jira coordination | Week 2 problem analysis | Meeting minutes, Jira issue history, charter commits |
| Member 2 — Data / ML Engineer | Dataset research, preprocessing, training, model comparison | Week 2 research evidence | Dataset-source notes, training commits, metrics/charts |
| Member 3 — Requirements / UI Engineer | Week 3 requirements, Week 4 SRS, frontend UX | Acceptance criteria | Requirement-register commits, UI commits, screenshots |
| Member 4 — Cybersecurity / QA Engineer | Week 5 feasibility, risk register, security controls, testing | API and integration QA | Risk commits, test evidence, Jira defects and closures |

## Cross-review rule
Every major deliverable should have a second team member review it through a GitHub pull request or documented Jira review task. This creates evidence of collaboration rather than isolated individual work.

## Suggested branch names
- `member1/charter-business`
- `member2/ml-data`
- `member3/requirements-ui`
- `member4/security-testing`

Use pull requests into `main`. Avoid direct large final commits to `main`.
