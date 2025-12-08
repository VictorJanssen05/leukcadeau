from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import json 
import os 
import re 

# Configuratie Variabelen
SERVER_PORT = 5000 
MY_ASSOCIATE_ID = "leukecadeaus2-21" 

app = Flask(__name__)
CORS(app) 

# Hoofdcategorieën die naar een eigen JSON-bestand verwijzen
HOOFDCATEGORIEEN = ['cadeaus', 'entertainment', 'huistechniek', 'leefstijl', 'humor']

# ===============================================
# --- FIX: SERVEER HTML/CSS/JS BESTANDEN ---
# ===============================================

@app.route('/')
def index():
    # Serveert de hoofdpagina (index.html)
    return send_from_directory('.', 'index.html')

@app.route('/<path:filename>')
def serve_files(filename):
    # Serveert alle andere bestanden zoals categorie.html, style.css, etc.
    return send_from_directory('.', filename)

# ===============================================
# --- EINDE FIX ---
# ===============================================


# --- FUNCTIE: DATA LADEN VANUIT JSON BESTAND ---
def laad_product_data(hoofd_categorie):
    # Probeer zowel 'cadeaus' als 'cadeaus_alle' te laden als we op de cadeaus-pagina staan
    if hoofd_categorie == 'cadeaus':
        filepath = os.path.join('data', 'cadeaus.json')
    else:
        filepath = os.path.join('data', f'{hoofd_categorie}.json')

    if not os.path.exists(filepath):
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


# --- FUNCTIE: PRODUCTEN ZOEKEN EN FILTEREN (GEOPTIMALISEERD) ---
def zoek_producten_op_categorie(categorie_trefwoord):
    
    trefwoord_delen = categorie_trefwoord.split('-') 
    hoofd_categorie = trefwoord_delen[0]
    sub_categorie_filter = trefwoord_delen[1] if len(trefwoord_delen) > 1 else 'alles'

    alle_producten_voor_hoofdcat = []
    
    # 1. SPECIAL CASE: 'Cadeaus-alles' of 'cadeaus-budget' moet ALLE producten laden
    if hoofd_categorie == 'cadeaus':
        # Combineer ALLE JSONs
        for cat_key in HOOFDCATEGORIEEN:
             alle_producten_voor_hoofdcat.extend(laad_product_data(cat_key))
             
        # Verwijder duplicaten (nodig bij het combineren van alle JSONs)
        seen_asins = set()
        unieke_producten = []
        for p in alle_producten_voor_hoofdcat:
            # Gebruik ASIN als unieke identifier, als deze bestaat
            if p.get('asin') and p.get('asin') not in seen_asins:
                seen_asins.add(p.get('asin'))
                unieke_producten.append(p)
        alle_producten_voor_hoofdcat = unieke_producten
             
    else:
        # Normale case: Laad alleen de JSON van de gevraagde hoofdcategorie
        alle_producten_voor_hoofdcat = laad_product_data(hoofd_categorie)

    
    producten_voor_frontend = []
    
    for product in alle_producten_voor_hoofdcat:
        
        # CRUCIALE FIX: Converteer de prijs naar een numerieke waarde (prijs_num)
        try:
            prijs_tekst = product.get('prijs', '€0').replace('€', '').replace(',', '.').strip()
            product['prijs_num'] = float(prijs_tekst)
        except ValueError:
            product['prijs_num'] = 9999.0 

        product_sub_cat = product.get('sub_categorie', 'onbekend')
        
        # 3. Hoofdfilter: Tonen als 'alles' is gekozen OF als subcategorie matcht.
        if sub_categorie_filter == 'alles' or product_sub_cat == sub_categorie_filter or sub_categorie_filter == 'budget' or sub_categorie_filter == 'populair':
            
            # De affiliate link wordt direct uit de JSON gehaald
            product["affiliate_link"] = product.get('affiliate_link', 'https://www.amazon.nl/') 
            
            producten_voor_frontend.append(product)
            
    # Retourneer de gefilterde producten
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
        # Gebruik ASIN als unieke identifier, als deze bestaat
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
#if __name__ == '__main__':
#    local_host = '127.0.0.1' 
#    print(f"Starte Flask Server op: http://{local_host}:{SERVER_PORT}/") 
#    app.run(host=local_host, port=SERVER_PORT, debug=True)