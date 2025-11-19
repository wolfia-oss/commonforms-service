# CommonForms Lambda Service

Simple FastAPI wrapper around CommonForms for AWS Lambda. Isolates AGPL-licensed CommonForms library from your main application.

## What This Does

Upload PDF → Lambda converts it → Download fillable PDF

## Files

```
commonforms-service/
├── app.py              # FastAPI app (80 lines)
├── requirements.txt    # 5 dependencies
├── Dockerfile         # Lambda container
├── template.yaml      # SAM deployment
└── README.md          # This file
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

## Deployment to AWS Lambda

### Prerequisites
- AWS CLI configured
- Docker installed
- AWS SAM CLI: `brew install aws-sam-cli`

### First Time Setup

**1. Set your ECR repository name**

If your ECR repo is named something other than `commonforms`, set it:
```bash
export ECR_REPO=your-ecr-repo-name
```

Or edit the Makefile and change `ECR_REPO ?= commonforms` to your repo name.

**2. Initial deployment**
```bash
make update
```

This will:
- Build Docker image
- Push to your ECR repository
- Deploy to Lambda with SAM (you'll be prompted for settings)

SAM deployment settings:
- Stack Name: `commonforms`
- AWS Region: `us-east-1`
- Confirm changes: `y`
- Allow SAM IAM role creation: `y`
- Save arguments to config file: `y`

**3. Get your API endpoint**

After deployment, note the `ApiEndpoint` in the outputs.

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

## Updating the Service

After making code changes:
```bash
make update
```

Or run steps individually:
```bash
make build    # Build Docker image
make push     # Push to ECR
make deploy   # Deploy to Lambda
```

## Available Make Commands

```bash
make help       # Show all available commands
make setup      # Create venv and install (first time)
make venv       # Create virtual environment
make install    # Install Python dependencies
make run        # Run locally
make test       # Test local service
make build      # Build Docker image
make push       # Push to ECR
make deploy     # Deploy to Lambda
make update     # Build + Push + Deploy
make clean      # Remove temporary files and venv
```

## Costs

~$0.20-0.50 per PDF conversion (3GB Lambda, ~60s processing)

## License

Wraps CommonForms (AGPL-3.0). Network separation avoids AGPL requirements in your main application.
