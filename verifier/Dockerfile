FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

# Слушает только на loopback — наружу торчит через Caddy (/verify/* -> 127.0.0.1:5557).
# Запускать с --network host, чтобы достучаться до туннеля малины на 127.0.0.1:5556.
EXPOSE 5557
CMD ["uvicorn", "app:app", "--host", "127.0.0.1", "--port", "5557"]
