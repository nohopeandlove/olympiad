FROM python:3.12-slim
WORKDIR /app
COPY requirements.lock .
RUN --mount=type=secret,id=build_ca \
    if [ -f /run/secrets/build_ca ]; then export PIP_CERT=/run/secrets/build_ca; fi; \
    pip install --no-cache-dir -r requirements.lock
COPY . .
RUN useradd -u 10001 -m app && chmod -R a+rX /app
USER app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--no-proxy-headers"]
