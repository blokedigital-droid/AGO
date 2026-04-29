import os
import requests
import csv
from io import StringIO
from thefuzz import fuzz

# Reemplaza con tu ID de Google Sheet
SHEET_ID = os.getenv('GOOGLE_SHEET_ID', '1hue1nHUQ6yzmrsRqPqjD7mksPnGFbfduxx8v7V5elr4')

def fetch_all_properties():
    # Esta URL descarga el Excel como un archivo de texto (CSV) automáticamente
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"
    response = requests.get(url)
    
    if response.status_code != 200:
        print("Error al leer el Google Sheet público")
        return []

    content = StringIO(response.text)
    reader = csv.DictReader(content)
    return list(reader)

def get_available_properties():
    all_props = fetch_all_properties()
    return [p for p in all_props if p.get('Estado', '').strip().lower() in ['', 'disponible']]
