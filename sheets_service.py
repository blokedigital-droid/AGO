import os, requests, csv
from io import StringIO
from thefuzz import fuzz

SHEET_ID = os.getenv('GOOGLE_SHEET_ID', '1hue1nHUQ6yzmrsRqPqjD7mksPnGFbfduxx8v7V5elr4')

def fetch_all_properties():
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"
    try:
        response = requests.get(url)
        response.encoding = 'utf-8'
        return list(csv.DictReader(StringIO(response.text))) if response.status_code == 200 else []
    except: return []

def get_available_properties():
    return [p for p in fetch_all_properties() if p.get('Estado', '').strip().lower() in ['', 'disponible']]

def filter_properties(query):
    available = get_available_properties()
    query = query.lower()
    
    # Clasificación por tipo o ciudad
    if 'apartaestudio' in query:
        return [p for p in available if 'apartaestudio' in p.get('Tipo','').lower()]
    if 'apartamento' in query:
        return [p for p in available if 'apartamento' in p.get('Tipo','').lower() and 'apartaestudio' not in p.get('Tipo','').lower()]
    if 'cali' in query:
        return [p for p in available if 'cali' in p.get('Ciudad','').lower()]
    if 'jamundi' in query or 'jamundí' in query:
        return [p for p in available if 'jamundi' in p.get('Ciudad','').lower()]
        
    return []

def format_property_list(props, name):
    res = f"¡Claro que sí, *{name}*! Aquí tienes las opciones que coinciden con tu búsqueda: 🏠✨\n"
    for i, p in enumerate(props, 1):
        res += f"\n*{i}. {p.get('Tipo','')}* en {p.get('Ciudad','')} ({p.get('ID','')})\n💰 {p.get('Precio','')}\n"
    res += "\n¿Cuál te gustaría conocer a detalle? Escribe el *número* o el *código* (ej: AGO001). 🎯"
    return res
