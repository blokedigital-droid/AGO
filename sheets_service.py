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

def search_properties(query):
    # Esta es la función CLAVE que busca en el Excel
    available = get_available_properties()
    if not available: return []
    q = query.lower()
    scored = []
    
    # Si busca por categorías generales
    if 'apartaestudio' in q: return [p for p in available if 'apartaestudio' in p.get('Tipo','').lower()]
    if 'apartamento' in q: return [p for p in available if 'apartamento' in p.get('Tipo','').lower() and 'apartaestudio' not in p.get('Tipo','').lower()]
    
    for prop in available:
        score = 0
        text = f"{prop.get('Tipo','')} {prop.get('Ubicacion','')} {prop.get('Ciudad','')} {prop.get('ID','')}".lower()
        if q in text: score += 60
        ratio = fuzz.partial_ratio(q, text)
        if ratio > 70: score += ratio
        if score > 0: scored.append((score, prop))
    
    scored.sort(key=lambda x: x[0], reverse=True)
    return [item[1] for item in scored[:6]]

def format_property_response(prop, name=""):
    res = f"¡Excelente elección, *{name}*! Aquí tienes el detalle: 🏠✨\n\n"
    res += f"📌 *{prop.get('Tipo', 'Inmueble')}* ({prop.get('ID', '')})\n"
    res += f"📍 {prop.get('Ubicacion', 'Consultar')}\n"
    res += f"💰 *CANON:* {prop.get('Precio', 'Consultar')}\n"
    res += f"📐 {prop.get('Area_m2', 'N/A')} m² | 🛏 {prop.get('Habitaciones', 'N/A')} Hab\n"
    if prop.get('Link_Fotos'): res += f"\n📸 *FOTOS:* {prop.get('Link_Fotos')}"
    if prop.get('Link_Video'): res += f"\n🎥 *VIDEO:* {prop.get('Link_Video')}"
    res += f"\n\n📅 *AGÉNDATE AQUÍ:* \n{prop.get('Link_agenamiento', 'https://wa.me/573024929820')}"
    res += f"\n\n*¿Ya lograste agendar o prefieres hablar con un asesor?* 😊"
    return res

def format_property_list(props, name, context=""):
    res = f"¡Claro, *{name}*! Encontré estas *{len(props)} opciones* {context}: 🏠✨\n"
    for i, p in enumerate(props, 1):
        res += f"\n*{i}. {p.get('Tipo','')}* ({p.get('ID','')})\n💰 {p.get('Precio','')}\n"
    res += "\n¿Cuál te interesa conocer? Escribe solo el *número*. 🎯"
    return res
