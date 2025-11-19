import base64
import json
import boto3
from pathlib import Path

lambda_client = boto3.client('lambda', region_name='us-west-1')

with open('test_data/input.pdf', 'rb') as f:
    pdf_bytes = f.read()

pdf_base64 = base64.b64encode(pdf_bytes).decode('utf-8')

event = {
    'pdf_base64': pdf_base64,
    'keep_existing_fields': True,
    'confidence': 0.6
}

print("Testing Lambda function on AWS...")
print(f"Input PDF size: {len(pdf_bytes) / 1024:.1f} KB")

response = lambda_client.invoke(
    FunctionName='commonforms',
    InvocationType='RequestResponse',
    Payload=json.dumps(event)
)

result = json.loads(response['Payload'].read())

print(f"Lambda response: {json.dumps(result, indent=2)}")

if result.get('statusCode') == 200:
    output_base64 = result['body']['pdf_base64']
    output_bytes = base64.b64decode(output_base64)

    output_path = Path('test_data/output_aws.pdf').resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'wb') as f:
        f.write(output_bytes)

    print(f"✓ Conversion successful! Output saved to {output_path}")
    print(f"  Output size: {len(output_bytes) / 1024:.1f} KB")
else:
    error_message = ""
    body = result.get('body')
    if isinstance(body, dict) and 'error' in body:
        error_message = body['error']
    elif isinstance(body, str):
        try:
            body_json = json.loads(body)
            error_message = body_json.get('error') or body_json.get('message') or body
        except json.JSONDecodeError:
            error_message = body
    elif 'errorMessage' in result:
        error_message = result['errorMessage']
    else:
        error_message = str(result)

    print(f"✗ Conversion failed: {error_message}")
