# Gebruik een officiële Python runtime als basisimage
FROM python:3.11-slim

# Stel de werkmap in de container in
WORKDIR /usr/src/app

# Kopieer de requirements file en installeer afhankelijkheden
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Kopieer de rest van de applicatiecode (app.py, data-map, etc.)
COPY . .

# CRUCIALE FIX: Gebruik ENTRYPOINT en CMD in de array-syntax
# Dit zorgt ervoor dat Gunicorn de $PORT omgevingsvariabele correct kan lezen
ENTRYPOINT ["gunicorn"]
CMD ["app:app", "--bind", "0.0.0.0:${PORT}"]