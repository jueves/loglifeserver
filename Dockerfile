FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .
COPY generate_cert.py .
COPY run_server.py .

# Expose both HTTP and HTTPS ports
EXPOSE 8000 8443

# Run with HTTPS by default (will generate certificate if needed)
CMD ["python", "run_server.py", "--host", "0.0.0.0", "--port", "8443"]
