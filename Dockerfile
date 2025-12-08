# Gebruik een officiële Python runtime als basisimage
FROM python:3.11-slim

# Stel de werkmap in de container in
WORKDIR /usr/src/app

# Kopieer de requirements file en installeer afhankelijkheden
# Dit is sneller omdat het de layer cache gebruikt
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Kopieer de rest van de applicatiecode (app.py, categorie.html, de data-map, etc.)
COPY . .

# Stel de standaard opstartopdracht in met Gunicorn
# Dit is wat er wordt uitgevoerd wanneer de container start
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:$PORT"]