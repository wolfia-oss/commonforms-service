import os
import base64
import tempfile
import traceback
from pathlib import Path


def configure_runtime_environment_for_lambda():
    aws_execution_environment = os.environ.get("AWS_EXECUTION_ENV", "")
    if not aws_execution_environment.startswith("AWS_Lambda"):
        return

    os.environ["HOME"] = "/tmp"
    os.environ.setdefault("XDG_CACHE_HOME", "/tmp/.cache")
    os.environ.setdefault("XDG_CONFIG_HOME", "/tmp/.config")
    os.environ.setdefault("HF_HOME", "/tmp/.cache/huggingface")
    os.environ.setdefault("HF_HUB_CACHE", "/tmp/.cache/huggingface")
    os.environ.setdefault("MPLCONFIGDIR", "/tmp/.config/matplotlib")
    os.environ.setdefault("ULTRALYTICS_CONFIG_DIR", "/tmp/Ultralytics")
    os.environ.setdefault("ULTRALYTICS_CACHE_DIR", "/tmp/Ultralytics")


configure_runtime_environment_for_lambda()

from commonforms import prepare_form


def lambda_handler(event, context):
    temp_dir = Path(tempfile.mkdtemp(prefix="commonforms_"))
    input_pdf_path = temp_dir / "input.pdf"
    output_pdf_path = temp_dir / "output.pdf"

    try:
        pdf_base64 = event.get('pdf_base64')
        if not pdf_base64:
            return {
                'statusCode': 400,
                'body': {'error': 'pdf_base64 is required in event'}
            }

        pdf_bytes = base64.b64decode(pdf_base64)

        with open(input_pdf_path, "wb") as pdf_file:
            pdf_file.write(pdf_bytes)

        model_from_event = event.get('model_or_path')
        model_from_env = os.environ.get('COMMONFORMS_MODEL')
        model_or_path = model_from_event or model_from_env or "FFDNET-L"

        fast_from_event = event.get('fast')
        if fast_from_event is not None:
            fast = bool(fast_from_event)
        else:
            fast_env = os.environ.get('COMMONFORMS_FAST', 'true')
            fast = str(fast_env).lower() in {"1", "true", "yes", "y"}

        device = os.environ.get('COMMONFORMS_DEVICE', 'cpu')

        prepare_form(
            str(input_pdf_path),
            str(output_pdf_path),
            keep_existing_fields=event.get('keep_existing_fields', True),
            confidence=event.get('confidence', 0.6),
            model_or_path=model_or_path,
            fast=fast,
            device=device
        )

        with open(output_pdf_path, "rb") as output_file:
            output_base64 = base64.b64encode(output_file.read()).decode('utf-8')

        return {
            'statusCode': 200,
            'body': {
                'pdf_base64': output_base64,
                'message': 'PDF conversion successful'
            }
        }

    except Exception as exception:
        traceback.print_exc()
        return {
            'statusCode': 500,
            'body': {'error': f'Conversion failed: {str(exception)}'}
        }

    finally:
        try:
            for file_path in temp_dir.glob("*"):
                file_path.unlink()
            temp_dir.rmdir()
        except Exception:
            pass
