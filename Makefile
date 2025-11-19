.PHONY: help venv setup install run test build push deploy update clean

ACCOUNT_ID ?= $(shell aws sts get-caller-identity --query Account --output text)
REGION ?= us-west-1
ECR_REPO ?= core
IMAGE_NAME ?= commonforms
IMAGE_TAG ?= latest
IMAGE_URI = $(ACCOUNT_ID).dkr.ecr.$(REGION).amazonaws.com/$(ECR_REPO):$(IMAGE_NAME)-$(IMAGE_TAG)
LOCAL_IMAGE = $(IMAGE_NAME):$(IMAGE_TAG)
VENV = venv
PYTHON = $(VENV)/bin/python
PIP = $(VENV)/bin/pip
UVICORN = $(VENV)/bin/uvicorn

help:
	@echo "CommonForms Service - Available commands:"
	@echo ""
	@echo "  make setup        Create venv and install dependencies (first time)"
	@echo "  make venv         Create virtual environment"
	@echo "  make install      Install Python dependencies"
	@echo "  make test         Test Lambda function locally"
	@echo "  make test-aws     Test Lambda function on AWS"
	@echo "  make build        Build Docker image"
	@echo "  make push         Push Docker image to ECR"
	@echo "  make deploy       Deploy to AWS Lambda with SAM (first time only)"
	@echo "  make update-lambda Update existing Lambda function with new image"
	@echo "  make update       Build + Push + Update Lambda (full update)"
	@echo "  make clean        Remove temporary files"
	@echo ""
	@echo "To activate venv manually:"
	@echo "  source venv/bin/activate"
	@echo ""
	@echo "Environment variables:"
	@echo "  ACCOUNT_ID=$(ACCOUNT_ID)"
	@echo "  REGION=$(REGION)"
	@echo "  ECR_REPO=$(ECR_REPO)"
	@echo "  IMAGE_NAME=$(IMAGE_NAME)"
	@echo "  IMAGE_TAG=$(IMAGE_TAG)"
	@echo "  IMAGE_URI=$(IMAGE_URI)"

venv:
	python3 -m venv $(VENV)
	@echo "Virtual environment created. Activate with: source venv/bin/activate"

setup: venv install
	@echo "Setup complete! Run 'make run' to start the service"

install: venv
	$(PIP) install -r requirements-dev.txt

test: install
	@echo "Testing Lambda function locally..."
	$(PYTHON) test_local.py

test-aws: install
	@echo "Testing Lambda function on AWS..."
	$(PYTHON) test_aws.py

build:
	docker build --platform linux/amd64 -t $(LOCAL_IMAGE) .

push: build
	@echo "Logging into ECR..."
	@aws ecr get-login-password --region $(REGION) | \
		docker login --username AWS --password-stdin $(ACCOUNT_ID).dkr.ecr.$(REGION).amazonaws.com
	@echo "Tagging image..."
	docker tag $(LOCAL_IMAGE) $(IMAGE_URI)
	@echo "Pushing to ECR..."
	docker push $(IMAGE_URI)
	@echo "Done! Image pushed to $(IMAGE_URI)"

deploy:
	sam build
	@if [ ! -f samconfig.toml ]; then \
		echo "First time deployment - running with --guided"; \
		sam deploy --guided --image-repository $(ACCOUNT_ID).dkr.ecr.$(REGION).amazonaws.com/$(ECR_REPO); \
	else \
		sam deploy --image-repository $(ACCOUNT_ID).dkr.ecr.$(REGION).amazonaws.com/$(ECR_REPO); \
	fi

update-lambda:
	@echo "Updating Lambda function with new image..."
	aws lambda update-function-code \
		--function-name commonforms \
		--image-uri $(IMAGE_URI) \
		--region $(REGION)
	@echo "Lambda function updated successfully!"

update: push update-lambda
	@echo "Service updated successfully!"

clean:
	rm -rf .aws-sam venv
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
