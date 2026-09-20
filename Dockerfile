# Copyright (c) 2026 Aman Anand, M (T&I), Barauni
FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt pyproject.toml README.md LICENSE ./
COPY gateway ./gateway
COPY config ./config

RUN pip install --no-cache-dir -r requirements.txt && pip install --no-cache-dir .

EXPOSE 4840 8091
CMD ["python", "-m", "gateway", "-c", "config/gateway.yaml"]
