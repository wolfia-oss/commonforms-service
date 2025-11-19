FROM --platform=linux/amd64 public.ecr.aws/lambda/python:3.12

RUN dnf install -y mesa-libGL mesa-libGLU libgomp || \
    microdnf install -y mesa-libGL || \
    yum install -y mesa-libGL || true

COPY requirements.txt ${LAMBDA_TASK_ROOT}/
RUN pip install --no-cache-dir -r ${LAMBDA_TASK_ROOT}/requirements.txt

COPY app.py ${LAMBDA_TASK_ROOT}/
RUN chmod 644 ${LAMBDA_TASK_ROOT}/app.py

CMD ["app.lambda_handler"]
