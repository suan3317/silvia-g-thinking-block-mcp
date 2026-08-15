FROM python:3.12-slim

WORKDIR /app
COPY server.py .

ENV PYTHONUNBUFFERED=1
EXPOSE 8787

HEALTHCHECK --interval=30s --timeout=3s --start-period=3s --retries=3 \
  CMD ["python3", "-c", "import os, urllib.request; port = os.environ.get('PORT', '8787'); urllib.request.urlopen(f'http://127.0.0.1:{port}/health', timeout=2)"]

CMD ["python3", "server.py"]
