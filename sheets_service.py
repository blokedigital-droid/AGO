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
    # Esta es la función que el bot usará para filtrar
    available = get_available_properties()
    query = query.lower()
    if 'apartaestudio' in query:
        return [p for p in available if 'apartaestudio' in p.get('Tipo','').lower()]
    if 'apartamento' in query:
        return [p for p in available if 'apartamento' in p.get('Tipo','').lower() and 'apartaestudio' not in p.get('Tipo','').lower()]
    if 'cali' in query:
        return [p for p in available if 'cali' in p.get('Ciudad','').lower()]
    if 'jamundi' in query or 'jamundí' in query:
        return [p for p in available if 'jamundi' in p.get('Ciudad','').lower()]
    return []

def search_properties(query):
    # Esta función es la que estaba causando el error por el nombre
    available = get_available_properties()
    if not available: return []
    query_lower = query.lower()
    scored = []
    for prop in available:
        score = 0
        full_text = f"{prop.get('Tipo','')} {prop.get('Ubicacion','')} {prop.get('Ciudad','')} {prop.get('Descripcion_Plus','')} {prop.get('ID','')}".lower()
        if query_lower in full_text: score += 50
        ratio = fuzz.partial_ratio(query_lower, full_text)
        if ratio > 65: score += ratio
        if score > 0: scored.append((score, prop))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [item[1] for item in scored[:3]]

def format_property_response(prop, name=""):
    res = f"¡Excelente elección, *{name}*! Mira lo que encontré: 🏠✨\n\n"
    res += f"📌 *{prop.get('Tipo', 'Inmueble')}* ({prop.get('ID', '')})\n"
    res += f"📍 {prop.get('Ubicacion', 'Consultar')}\n"
    res += f"🏙️ *{prop.get('Ciudad', '')}*\n\n"
    res += f"💰 *CANON:* {prop.get('Precio', 'Consultar')}\n"
    res += f"📐 {prop.get('Area_m2', 'N/A')} m² | 🛏 {prop.get('Habitaciones', 'N/A')} Hab | 🚿 {prop.get('Baños', 'N/A')} Baños\n"
    if prop.get('Link_Fotos'): res += f"\n📸 *FOTOS:* {prop.get('Link_Fotos')}"
    if prop.get('Link_Video'): res += f"\n🎥 *VIDEO:* {prop.get('Link_Video')}"
    res += f"\n\n📝 *SOBRE EL INMUEBLE:* {prop.get('Descripcion_Plus','')[:180]}..."
    if prop.get('Link_agenamiento'): res += f"\n\n📅 *AGÉNDATE AQUÍ:* \n{prop.get('Link_agenamiento')}"
    return res

def format_property_list(props, name):
    res = f"¡Claro que sí, *{name}*! Estas son las mejores opciones para ti: 🏠✨\n"
    for i, p in enumerate(props, 1):
        res += f"\n*{i}. {p.get('Tipo','')}* en {p.get('Ciudad','')} ({p.get('ID','')})\n💰 {p.get('Precio','')}\n"
    res += "\n¿Cuál te gusta? Escribe el *número* o el *código* (ej: AGO001). 🎯"
    return res
