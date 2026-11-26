FROM python:3.10-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1

COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Usuario sin privilegios; las fotos subidas se guardan en app/static/uploads
RUN useradd --create-home appuser \
    && mkdir -p /app/app/static/uploads/comentarios \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 5000

# --preload: las migraciones de arranque corren una sola vez, no por cada worker
CMD ["gunicorn", "--preload", "--workers", "2", "--bind", "0.0.0.0:5000", "--timeout", "60", "run:app"]
