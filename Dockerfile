FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .
COPY start_server.py .

EXPOSE 3001

CMD ["python", "start_server.py"]
