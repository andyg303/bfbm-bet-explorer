FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create non-root user
RUN adduser --disabled-password --gecos '' appuser

# Copy application code
COPY . .

# Switch to non-root user
USER appuser

EXPOSE 8000

CMD ["python", "api/main.py"]
