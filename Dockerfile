# Gebruik een officiële Python runtime als basisimage
FROM python:3.11-slim

# Stel de werkmap in de container in
WORKDIR /usr/src/app

# Kopieer de requirements file en installeer afhankelijkheden
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Kopieer de rest van de applicatiecode (app.py, data-map, etc.)
COPY . .

# CMD ["app:app", "--bind", "0.0.0.0:${PORT}"] <-- Oude, foutieve regel

# Nieuwe, gefixeerde regel:
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:8000"]