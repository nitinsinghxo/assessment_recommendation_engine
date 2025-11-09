FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Train model if it doesn't exist (for deployment)
RUN python train_and_serialize.py || true

EXPOSE 8000

ENV PORT=8000
CMD uvicorn src.app:app --host 0.0.0.0 --port ${PORT:-8000}

