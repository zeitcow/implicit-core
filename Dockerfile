FROM python:3.12-slim-bookworm
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_DISABLE_PIP_VERSION_CHECK=1
RUN printf "%s\n" "implicit-ai==1.0.0 --hash=sha256:afd5b2560eb45568243aafc61ea5419feec37df05194e023fb3130d04191f6fd" > /tmp/requirements.txt \
    && python -m pip install --no-cache-dir --no-deps --require-hashes -r /tmp/requirements.txt
USER 65532:65532
CMD ["implicit-mcp"]
