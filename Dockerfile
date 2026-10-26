# Imagem da API do PetMind (Cloud Run, Render ou qualquer host de containers)
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONUNBUFFERED=1 \
    PORT=8080

EXPOSE 8080

# Na subida, as migrations do Alembic são aplicadas (PETMIND_AUTO_MIGRATE_ON_STARTUP).
# O Cloud Run informa a porta pela variável PORT e termina o HTTPS no proxy dele;
# --forwarded-allow-ips faz os redirecionamentos saírem com https.
CMD exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT} --proxy-headers --forwarded-allow-ips '*'
