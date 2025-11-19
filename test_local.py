import base64
import json
from pathlib import Path
from app import lambda_handler


def test_conversion(input_pdf_path, output_pdf_path):
    with open(input_pdf_path, 'rb') as f:
        pdf_bytes = f.read()

    pdf_base64 = base64.b64encode(pdf_bytes).decode('utf-8')

    event = {
        'pdf_base64': pdf_base64,
        'keep_existing_fields': True,
        'confidence': 0.6
    }

    print(f"Testing conversion of {input_pdf_path}...")
    result = lambda_handler(event, None)

    if result['statusCode'] == 200:
        output_base64 = result['body']['pdf_base64']
        output_bytes = base64.b64decode(output_base64)

        with open(output_pdf_path, 'wb') as f:
            f.write(output_bytes)

        print(f"✓ Conversion successful! Output saved to {output_pdf_path}")
        print(f"  Input size: {len(pdf_bytes) / 1024:.1f} KB")
        print(f"  Output size: {len(output_bytes) / 1024:.1f} KB")
    else:
        print(f"✗ Conversion failed: {result['body']['error']}")

    return result


if __name__ == "__main__":
    test_conversion(
        "test_data/input.pdf",
        "test_data/output.pdf"
    )
