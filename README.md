# CommonForms Lambda Service

Small AWS Lambda wrapper around CommonForms that converts a static PDF into a fillable PDF. This isolates the AGPL-licensed CommonForms library from your main application behind a Lambda boundary.

## What This Does

Upload PDF → Lambda converts it with CommonForms → Download fillable PDF

## Files

```
commonforms-service/
├── app.py               # Lambda handler using commonforms.prepare_form
├── requirements.txt     # Runtime dependencies for the Lambda image
├── requirements-dev.txt # Local dev/test dependencies (boto3, requests, etc.)
├── Dockerfile           # Lambda container image
├── template.yaml        # SAM stack definition (direct invocation)
└── README.md            # This file
```

## Local Development

**First time setup:**
```bash
make setup    # Creates venv and installs dependencies
make test     # Test Lambda function locally
```

Or manually:
```bash
make venv              # Create virtual environment
source venv/bin/activate
make install           # Install dependencies
python test_local.py  # Test conversion
```

To test the deployed Lambda from your machine:

```bash
make test-aws   # Invoke the deployed Lambda and save test_data/output_aws.pdf
```

## Deployment to AWS Lambda

### Prerequisites
- AWS CLI configured
- Docker installed
- AWS SAM CLI: `brew install aws-sam-cli`
- An ECR repository for the image (defaults to `core`)

### 1. Set or confirm your ECR repository

By default the Makefile uses:

```make
ECR_REPO ?= core
REGION  ?= us-west-1
```

If your ECR repo is named something else (or in another region), either:

- Export the environment variable:
```bash
export ECR_REPO=your-ecr-repo-name
export REGION=your-region
```

Or edit the Makefile and change `ECR_REPO`/`REGION` defaults.

Make sure the ECR repository exists before deploying.

### 2. First-time deployment with SAM

For the first deployment (creating the stack, permissions, etc.):

```bash
make deploy
```

This will:
- Run `sam build`
- Run `sam deploy --guided` and prompt for stack details
- Create the `commonforms` Lambda function pointing at your ECR image

SAM deployment settings:
- Stack Name: `commonforms` (recommended)
- AWS Region: `us-west-1` (or your chosen region)
- Allow SAM IAM role creation: `y`
- Save arguments to config file: `y` (creates `samconfig.toml`)

After the first run, `make deploy` will use `samconfig.toml` and run non-interactively.

## Using from Your EKS Service

Direct Lambda invocation (no API Gateway):

```python
import boto3
import base64

lambda_client = boto3.client('lambda', region_name='us-west-1')

with open("input.pdf", "rb") as f:
    pdf_bytes = f.read()

pdf_base64 = base64.b64encode(pdf_bytes).decode('utf-8')

response = lambda_client.invoke(
    FunctionName='commonforms',
    InvocationType='RequestResponse',
    Payload=json.dumps({
        'pdf_base64': pdf_base64,
        'keep_existing_fields': True,
        'confidence': 0.6
    })
)

result = json.loads(response['Payload'].read())
if result['statusCode'] == 200:
    output_base64 = result['body']['pdf_base64']
    output_pdf = base64.b64decode(output_base64)

    with open("output.pdf", "wb") as f:
        f.write(output_pdf)
```

## Lambda Event Format

**Input event:**
```json
{
  "pdf_base64": "base64-encoded PDF content",
  "keep_existing_fields": true,
  "confidence": 0.6
}
```

**Response:**
```json
{
  "statusCode": 200,
  "body": {
    "pdf_base64": "base64-encoded converted PDF",
    "message": "PDF conversion successful"
  }
}
```

## Updating the Service (local workflow)

After making code changes:
```bash
make update
```

Or run steps individually:
```bash
make build       # Build Docker image
make push        # Push image to ECR
make update-lambda  # Point Lambda at the new image URI
```

The first push of a new dependency set (changes to `requirements.txt` or the base image) will upload a large image layer containing the ML stack. Subsequent code-only changes reuse that layer, so pushes only upload small deltas.

## GitHub Actions Deployment

This repo includes a GitHub Actions workflow at `.github/workflows/deploy.yml` that automates the same build → push → Lambda update steps on pushes to `main`.

### Trigger

- On push to `main` when any of these change:
  - `app.py`, `Dockerfile`, `requirements.txt`, `template.yaml`, or the workflow itself.
- Manual trigger via the Actions tab (`workflow_dispatch`).

### What the workflow does

- Assumes an AWS IAM role using GitHub OIDC (no long-lived AWS keys in GitHub).
- Builds the Docker image for `linux/amd64`.
- Pushes the image to your ECR repository as:
  - `<account>.dkr.ecr.<region>.amazonaws.com/core:commonforms-latest`
- Calls `aws lambda update-function-code` for the `commonforms` function with the new image URI.

### Required GitHub/AWS setup

1. **AWS IAM role**  
   - Trusts GitHub OIDC (`token.actions.githubusercontent.com`).  
   - Permissions:
     - Push to your ECR repo (`core` by default).
     - `lambda:UpdateFunctionCode` on the `commonforms` function.
     - `sts:GetCallerIdentity`.

2. **GitHub repo secret**  
   - Add `AWS_DEPLOY_ROLE_ARN` with the IAM role ARN.

Once configured, pushing to `main` will automatically build, push, and deploy the updated image.

## Available Make Commands

```bash
make help       # Show all available commands
make setup      # Create venv and install (first time)
make venv       # Create virtual environment
make install    # Install Python dependencies
make run        # Run locally
make test       # Test local service
make test-aws   # Invoke deployed Lambda and save output_aws.pdf
make build      # Build Docker image
make push       # Push to ECR
make deploy     # Deploy to Lambda
make update     # Build + Push + update existing Lambda
make clean      # Remove temporary files and venv
```

## Costs

Rough order of magnitude (depends on region and exact memory setting):
- At 6–10 GB memory and ~3–5s billed time, each conversion typically costs well under $0.01.
- For infrequent use (occasional conversions), total monthly cost is usually in the low single-digit dollars.

## License

Wraps CommonForms (AGPL-3.0). Network separation avoids AGPL requirements in your main application.
