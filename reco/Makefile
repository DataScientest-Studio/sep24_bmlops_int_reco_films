.PHONY: setup data preprocess train run-api test

setup:
	@echo "Setting up the virtual environment and installing dependencies..."
	python -m venv venv
	. venv/bin/activate && pip install -r requirements.txt

data:
	@echo "Managing data with DVC..."
	dvc init
	dvc add data/raw/static_data.csv

preprocess:
	@echo "Preprocessing data..."
	python src/data/preprocess.py

train:
	@echo "Training the model..."
	python src/models/train_model.py

run-api:
	@echo "Starting the API..."
	uvicorn src.api.main:app --reload

test:
	@echo "Running tests..."
	pytest tests/