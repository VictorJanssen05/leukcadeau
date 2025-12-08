from flask import Flask, jsonify, request, send_from_directory # send_from_directory is NIEUW!
from flask_cors import CORS
import json 
import os 
import re 

# Configuratie Variabelen
SERVER_PORT = 5000 
MY_ASSOCIATE_ID = "leukecadeaus2-21" 

app = Flask(__name__)
# CORS is essentieel om communicatie tussen frontend (op file:// of localhost) en de Flask server mogelijk te maken
CORS(app) 

# Hoofdcategorieën die naar een eigen JSON-bestand verwijzen
HOOFDCATEGORIEEN = ['cadeaus', 'entertainment', 'huistechniek', 'leefstijl', 'humor']

# ===============================================
# --- FIX: SERVEER HTML/CSS/JS BESTANDEN ---
# Deze routes zorgen ervoor dat de browser de index.html en de andere files kan zien
# ===============================================

@app.route('/')
def index():
    # Serveert de hoofdpagina (index.html) wanneer iemand naar de root-URL (leukcadeau.com) gaat
    return send_from_directory('.', 'index.html')

@app.route('/<path:filename>')
def serve_files(filename):
    # Serveert alle andere bestanden zoals categorie.html, style.css, de JavaScript-bestanden, etc.
    # Dit is nodig omdat je applicatie niet alleen een API is, maar ook HTML moet tonen.
    return send_from_directory('.', filename)

# ===============================================
# --- EINDE FIX ---
# ===============================================


# --- FUNCTIE: DATA LADEN VANUIT JSON BESTAND ---
def laad_product_data(hoofd_categorie):
    # Probeer zowel 'cadeaus' als 'cadeaus_alle' te laden als we op de cadeaus-pagina staan
    if hoofd_categorie == 'cadeaus':
        # De cadeaus-pagina is een speciale categorie, maar laadt voor nu net als de andere
        filepath = os.path.join('data', 'cadeaus.json')
    else:
        filepath = os.path.join('data', f'{hoofd_categorie}.json')

    if not os.path.exists(filepath):
        # Controleer voor de zekerheid ook het meervoud (bijv. huistechnieken.json)
        # of een eventuele typo. Nu houden we ons aan de enkelvoudige naam.
        print(f"Waarschuwing: Bestand niet gevonden op {filepath}")
        return []
        
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
        
    except json.JSONDecodeError as e:
        print(f"Fout bij het parsen van {filepath}: {e}")
        return []
    except Exception as e:
        print(f"Onbekende fout bij het laden van {filepath}: {e}")
        return []


# --- FUNCTIE: PRODUCTEN ZOEKEN EN FILTEREN ---
# De logica in deze functie zorgt ervoor dat op de homepage ('cadeaus-alles') 
# en alle andere pagina's de juiste JSON-bestanden worden gebruikt.
def zoek_producten_op_categorie(categorie_trefwoord):
    
    trefwoord_delen = categorie_trefwoord.split('-') 
    hoofd_categorie = trefwoord_delen[0]
    sub_categorie_filter = trefwoord_delen[1] if len(trefwoord_delen) > 1 else 'alles'

    alle_producten_voor_hoofdcat = []
    
    # 1. SPECIAL CASE: 'Cadeaus-alles' of 'cadeaus-budget' moet ALLE producten laden
    # De front-end logica is ingesteld dat 'cadeaus' ALLE producten toont.
    if hoofd_categorie == 'cadeaus':
        # API oproep voor de 'cadeaus' hoofdcategorie moet ALLE JSONs combineren
        # Dit is de enige plek waar we alle data bij elkaar rapen, behalve /alles.
        for cat_key in HOOFDCATEGORIEEN:
             # Voorkom dubbel tellen als cadeaus.json al data bevat
            alle_producten_voor_hoofdcat.extend(laad_product_data(cat_key))
            
    else:
        # Normale case: Laad alleen de JSON van de gevraagde hoofdcategorie
        alle_producten_voor_hoofdcat = laad_product_data(hoofd_categorie)

    
    producten_voor_frontend = []
    
    for product in alle_producten_voor_hoofdcat:
        
        # CRUCIALE FIX: Converteer de prijs naar een numerieke waarde (prijs_num)
        try:
            # Voer prijsconversie lokaal uit voor rendering (dit staat ook in JS, maar is handig voor Budget filter)
            prijs_tekst = product.get('prijs', '€0').replace('€', '').replace(',', '.').strip()
            product['prijs_num'] = float(prijs_tekst)
        except ValueError:
            product['prijs_num'] = 9999.0 

        product_sub_cat = product.get('sub_categorie', 'onbekend')
        
        # 3. Hoofdfilter: Tonen als 'alles' is gekozen OF als subcategorie matcht.
        # De JS filtert al op de budget-knop (als die actief is)
        if sub_categorie_filter == 'alles' or product_sub_cat == sub_categorie_filter or sub_categorie_filter == 'budget' or sub_categorie_filter == 'populair':
            
            # De affiliate link wordt direct uit de JSON gehaald
            product["affiliate_link"] = product.get('affiliate_link', 'https://www.amazon.nl/') 
            
            producten_voor_frontend.append(product)
            
    # CRUCIALE FIX: Als 'cadeaus' wordt gevraagd, haal dan alle unieke producten op
    if hoofd_categorie == 'cadeaus':
        # Gebruik sets om duplicaten te verwijderen (op basis van ASIN)
        seen_asins = set()
        unieke_producten = []
        for p in producten_voor_frontend:
            if p.get('asin') not in seen_asins:
                seen_asins.add(p.get('asin'))
                unieke_producten.append(p)
        return unieke_producten


    return producten_voor_frontend


# --- NIEUWE FUNCTIE: LAAD ALLES OVER ALLE CATEGORIEËN HEEN (voor Homepage) ---
@app.route('/api/producten/alles', methods=['GET'])
def laad_alle_producten():
    alle_producten_lijst = []
    
    for categorie in HOOFDCATEGORIEEN:
        data = laad_product_data(categorie)
        
        for product in data:
            try:
                prijs_tekst = product.get('prijs', '€0').replace('€', '').replace(',', '.').strip()
                product['prijs_num'] = float(prijs_tekst)
            except ValueError:
                product['prijs_num'] = 9999.0

            product["affiliate_link"] = product.get('affiliate_link', 'https://www.amazon.nl/')
            alle_producten_lijst.append(product)
            
    # Verwijder eventuele duplicaten die ontstaan als een product in meerdere JSONs staat
    seen_asins = set()
    unieke_producten = []
    for p in alle_producten_lijst:
        if p.get('asin') and p.get('asin') not in seen_asins:
            seen_asins.add(p.get('asin'))
            unieke_producten.append(p)
            
    return jsonify(unieke_producten)


# --- DE FLASK API ROUTE ---

@app.route('/api/producten', methods=['GET'])
def get_producten():
    categorie = request.args.get('cat', 'algemeen') 
    product_lijst = zoek_producten_op_categorie(categorie)
    return jsonify(product_lijst)
    
# --- SERVER STARTEN ---
# --- SERVER STARTEN ---
#if __name__ == '__main__':
#    local_host = '127.0.0.1' 
#    print(f"Starte Flask Server op: http://{local_host}:{SERVER_PORT}/") 
#    app.run(host=local_host, port=SERVER_PORT, debug=True)