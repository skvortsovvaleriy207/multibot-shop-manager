FROM python:3.12-slim

WORKDIR /app

# Install basic system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements (assuming they are identical, we use one as source)
COPY bestsocialbot/requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project
COPY . .

# Set PYTHONPATH so bots can import shared_storage
ENV PYTHONPATH=/app
