import os, requests, csv
from io import StringIO
from thefuzz import fuzz

SHEET_ID = os.getenv('GOOGLE_SHEET_ID', '1hue1nHUQ6yzmrsRqPqjD7mksPnGFbfduxx8v7V5elr4')

def fetch_all_properties():
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"
    try:
        response = requests.get(url)
        if response.status_code != 200: return []
        return list(csv.DictReader(StringIO(response.text)))
    except: return []

def get_available_properties():
    all_props = fetch_all_properties()
    return [p for p in all_props if p.get('Estado', '').strip().lower() in ['', 'disponible']]

def search_properties(query):
    available = get_available_properties()
    if not available: return []
    query_lower = query.lower()
    scored = []
    for prop in available:
        score = 0
        search_text = f"{prop.get('Tipo','')} {prop.get('Ubicacion','')} {prop.get('Ciudad','')} {prop.get('Descripcion_Plus','')}".lower()
        if query_lower in search_text: score += 70
        ratio = fuzz.partial_ratio(query_lower, search_text)
        if ratio > 65: score += ratio
        if score > 0: scored.append((score, prop))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [item[1] for item in scored[:3]]

def format_property_response(prop, name=""):
    res = f"¡Mira esta excelente opción, *{name}*! 🎯\n\n"
    res += f"🏠 *{prop.get('Tipo', 'Inmueble')}*\n"
    res += f"📍 {prop.get('Ubicacion', 'Consultar')}\n"
    res += f"🏙️ *{prop.get('Ciudad', '')}*\n\n"
    res += f"💰 *Canon:* {prop.get('Precio', 'Consultar')}\n"
    res += f"📐 {prop.get('Area_m2', 'N/A')} m² | 🛏 {prop.get('Habitaciones', 'N/A')} Hab | 🚿 {prop.get('Baños', 'N/A')} Baños\n"
    
    if prop.get('Link_Fotos'): res += f"\n📸 *Fotos:* {prop.get('Link_Fotos')}"
    if prop.get('Link_Video'): res += f"\n🎥 *Video:* {prop.get('Link_Video')}"
    
    # Requisitos
    req = prop.get('Requisitos', '').strip()
    if req:
        res += f"\n\n📋 *Requisitos para este inmueble:*\n{req[:250]}..." # Limitado para no saturar el chat
    
    if prop.get('Link_agenamiento'):
        res += f"\n\n📅 *Agenda tu visita aquí:* \n{prop.get('Link_agenamiento')}"
    
    return res
