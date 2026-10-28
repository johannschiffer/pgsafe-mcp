FROM python:3.11-slim
WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir . && useradd -m -u 10001 appuser && chown -R appuser:appuser /app
USER appuser
ENTRYPOINT ["pgsafe-mcp"]
