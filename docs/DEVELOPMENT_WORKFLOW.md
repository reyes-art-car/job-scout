# Branch and commit organization

`main` contains the integrated project. Existing published commits are preserved.
The following branches are integrated in order because later changes depend on earlier ones.
Each branch is merged with a merge commit so its scope remains visible in the history.

| Order | Branch | Commit scope |
| --- | --- | --- |
| 1 | `security/backend-hardening` | API authentication, request limits, sanitization, application boundaries, dependencies, and regression tests |
| 2 | `refactor/frontend-offer-workflows` | API and demo gateways, token handling, offer validation, scoring, smaller UI components, and regression tests |
| 3 | `refactor/automation-pipeline` | Extract the search script into a validated pipeline with separate adapters, prompts, and tests |
| 4 | `build/quality-and-deployment` | Separate commits for Docker infrastructure, quality and security workflows, and documentation |

Commit subjects and bodies are written in English using the convention
`type(scope): imperative description`. Dates reflect the actual commits.

## Validation before publication

- Backend: Ruff lint and formatting, mypy, Bandit, and pytest with a minimum coverage of 85%.
- Automation: Ruff and pytest.
- Frontend: Angular lint, tests in headless Chrome, and a production build.
- Review staged files for private data and generated artifacts.

## Future changes

Start each new branch from the latest `main`, keep one concrete purpose per branch,
and include relevant tests with the implementation. Push the branch and open a pull request
describing the problem, the resulting behavior, and the checks performed.
Delete merged branches when they are no longer useful; the merge history preserves their context.
