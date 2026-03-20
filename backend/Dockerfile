FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Pre-create persistent data directories
RUN mkdir -p data/uploads

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]