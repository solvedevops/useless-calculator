FROM python:3.11-alpine

# Install build and runtime dependencies
RUN apk add --update --no-cache \
    gcc \
    python3-dev \
    py3-pip \
    musl-dev \
    libffi-dev \
    openssl-dev \
    linux-headers \
    libffi \
    openssl

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# Copy application code
COPY . /app

# Expose port
EXPOSE 5000

# Run the application
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "5000", "--proxy-headers"]