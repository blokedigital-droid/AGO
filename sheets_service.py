import os, requests, csv
from io import StringIO
from thefuzz import fuzz

SHEET_ID = os.getenv('GOOGLE_SHEET_ID', '1hue1nHUQ6yzmrsRqPqjD7mksPnGFbfduxx8v7V5elr4')

def fetch_all_properties():
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"
    try:
        response = requests.get(url)
        response.encoding = 'utf-8' # Forzamos el idioma español
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
        # Texto completo para buscar
        full_text = f"{prop.get('Tipo','')} {prop.get('Ubicacion','')} {prop.get('Ciudad','')} {prop.get('Descripcion_Plus','')} {prop.get('ID','')}".lower()
        
        # Prioridad por ubicación o tipo
        if query_lower in full_text: score += 50
        
        # Similitud aproximada
        ratio = fuzz.partial_ratio(query_lower, full_text)
        if ratio > 70: score += ratio
        
        if score > 0: scored.append((score, prop))
    
    scored.sort(key=lambda x: x[0], reverse=True)
    return [item[1] for item in scored[:3]]

def format_property_response(prop, name=""):
    # Limpiamos el texto de los requisitos para que no se vea feo
    req = prop.get('Requisitos', '').strip()
    
    res = f"¡Excelente elección, *{name}*! Mira este inmueble que tengo disponible para ti: 🏠✨\n\n"
    res += f"📌 *{prop.get('Tipo', 'Inmueble')}* ({prop.get('ID', '')})\n"
    res += f"📍 {prop.get('Ubicacion', 'Consultar')}\n"
    res += f"🏙️ *{prop.get('Ciudad', '')}*\n\n"
    res += f"💰 *CANON:* {prop.get('Precio', 'Consultar')}\n"
    res += f"📐 {prop.get('Area_m2', 'N/A')} m² | 🛏 {prop.get('Habitaciones', 'N/A')} Hab | 🚿 {prop.get('Baños', 'N/A')} Baños\n"
    
    if prop.get('Link_Fotos'): res += f"\n📸 *FOTOS AQUÍ:* {prop.get('Link_Fotos')}"
    if prop.get('Link_Video'): res += f"\n🎥 *VIDEO:* {prop.get('Link_Video')}"
    
    res += f"\n\n📝 *LO MEJOR:* {prop.get('Descripcion_Plus','')[:200]}..."
    
    if prop.get('Link_agenamiento'):
        res += f"\n\n📅 *¿TE GUSTARÍA VERLO EN PERSONA?*\nAgéndate aquí una cita de una vez: \n{prop.get('Link_agenamiento')}"
    
    return res
