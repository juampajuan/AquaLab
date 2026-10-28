FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# CLI standalone de Tailwind (sin Node). Va fuera de /app porque Compose monta el repo encima.
# La misma versión se usa en el CI (.github/workflows/ci.yml).
ARG TAILWIND_VERSION=v4.3.3
ARG TARGETARCH
RUN case "${TARGETARCH:-amd64}" in arm64) arch=arm64 ;; *) arch=x64 ;; esac \
    && python -c "import sys, urllib.request; urllib.request.urlretrieve(sys.argv[1], sys.argv[2])" \
       "https://github.com/tailwindlabs/tailwindcss/releases/download/${TAILWIND_VERSION}/tailwindcss-linux-${arch}" \
       /usr/local/bin/tailwindcss \
    && chmod +x /usr/local/bin/tailwindcss

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
