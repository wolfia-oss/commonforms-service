# Contributing to CommonForms Lambda Service

Thanks for helping improve this project. This repository is a small AWS Lambda wrapper around the AGPL-licensed CommonForms library and is intended to stay minimal and focused.

## Development Workflow

- Fork the repository under your own GitHub account.
- Create a feature branch from `main`:

  ```bash
  git checkout -b feature/your-change
  ```

- Keep pull requests small and focused on a single concern.

## Local Setup

Requirements:
- Python 3.11+ installed locally
- Docker (for building the Lambda image)
- AWS CLI and SAM CLI (for optional deploy tests)

Recommended workflow:

```bash
make setup        # Create venv and install dev dependencies
make test         # Run local conversion test (no AWS)
make test-aws     # Invoke the deployed Lambda and save test_data/output_aws.pdf
```

`make test` calls `app.lambda_handler` directly using a local PDF; `make test-aws` uses `boto3` to invoke the real Lambda function named `commonforms` in your AWS account.

## Coding Guidelines

- Follow the existing project style:
  - Descriptive variable and function names.
  - No unnecessary comments; keep the code self-explanatory.
  - Prefer small, composable functions and avoid duplication (DRY).
  - Use type hints consistently; introduce Pydantic models only when they clearly improve type safety or event structure.
- Keep the Lambda handler (`app.py`) minimal; push complex logic into well-named functions or into the CommonForms library where appropriate.
- Do not add extra dependencies lightly; any addition to `requirements.txt` increases image size and cold start time.

## Tests

- For any behavior change, make sure:
  - `make test` passes.
  - If relevant, `make test-aws` produces a valid `test_data/output_aws.pdf`.
- If you add new behavior that is testable locally (without AWS), extend `test_local.py` instead of introducing a new ad hoc test script.

## Deployment and CI

This repo has a GitHub Actions workflow at `.github/workflows/deploy.yml` that:
- Builds a Docker image for `linux/amd64`.
- Pushes it to an ECR repository (default `core`).
- Updates the `commonforms` Lambda function’s image.

Notes:
- The workflow is triggered on pushes to `main` that touch key deployment files.
- It assumes an AWS IAM role configured via `AWS_DEPLOY_ROLE_ARN` (set as a GitHub secret).
- Do not commit AWS credentials, `.env` files, `samconfig.toml`, or any other secrets.

As a contributor:
- You generally do not need to change the workflow file unless you are improving the CI/CD itself.
- If you propose CI changes, explain the reasoning clearly in the PR description.

## Pull Requests

- Include a short description of:
  - What changed.
  - How it was tested (`make test`, `make test-aws`, etc.).
  - Any impact on deployment or configuration.
- Avoid force-pushing to `main`. All changes should go through PRs and be squash-merged or rebased as appropriate.

## License and AGPL Considerations

- This project wraps the AGPL-licensed CommonForms library. The goal is to keep this wrapper minimal and focused so that your main application can remain under a different license while calling this Lambda as an isolated service.
- When contributing, do not copy large chunks of CommonForms’ source into this repo. Instead, use its public APIs.

By submitting changes, you agree that your contributions will be licensed under the same terms as the project.
