FROM python:3.12-slim
WORKDIR /judge
COPY requirements.lock .
RUN --mount=type=secret,id=build_ca \
    if [ -f /run/secrets/build_ca ]; then export PIP_CERT=/run/secrets/build_ca; fi; \
    pip install --no-cache-dir -r requirements.lock
COPY main.py .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "9000"]
