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
    available = get_available_properties(); q = query.lower().strip()
    
    # 🏙️ Inteligencia de Zonas y Barrios
    if 'norte' in q: return [p for p in available if 'norte' in p.get('Ubicacion','').lower() or 'norte' in p.get('Ciudad','').lower()]
    if 'sur' in q: return [p for p in available if 'sur' in p.get('Ubicacion','').lower() or 'sur' in p.get('Ciudad','').lower()]
    if 'cordoba' in q or 'córdoba' in q: return [p for p in available if 'cordoba' in p.get('Tipo','').lower() or 'cordoba' in p.get('Ubicacion','').lower()]
    if 'alamos' in q or 'álamos' in q: return [p for p in available if 'alamos' in p.get('Ubicacion','').lower()]
    if 'flora' in q: return [p for p in available if 'flora' in p.get('Tipo','').lower() or 'flora' in p.get('Ubicacion','').lower()]
    if 'jamundi' in q or 'jamundí' in q: return [p for p in available if 'jamundi' in p.get('Ciudad','').lower()]
    
    # 🏠 Categorías base (Incluyendo Casas)
    if q in ['apartamento', 'apartamentos']: return [p for p in available if 'apartamento' in p.get('Tipo','').lower() and 'apartaestudio' not in p.get('Tipo','').lower()]
    if q in ['apartaestudio', 'apartaestudios', 'estudio']: return [p for p in available if 'apartaestudio' in p.get('Tipo','').lower()]
    if q in ['casa', 'casas']: return [p for p in available if 'casa' in p.get('Tipo','').lower()]
    
    return []

def search_properties(query):
    available = get_available_properties(); q = query.lower().strip()
    if len(q) < 3 and not q.isdigit(): return []
    scored = []
    for prop in available:
        score = 0
        text = f"{prop.get('Tipo','')} {prop.get('Ubicacion','')} {prop.get('Ciudad','')} {prop.get('ID','')}".lower()
        if q == prop.get('ID','').lower(): score += 100
        if q in text: score += 50
        ratio = fuzz.partial_ratio(q, text)
        if ratio > 80: score += ratio
        if score > 60: scored.append((score, prop))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [item[1] for item in scored]

def format_property_response(prop, name=""):
    res = f"¡Excelente elección, *{name}*! Aquí tienes el detalle: 🏠✨\n\n"
    res += f"📌 *{prop.get('Tipo', 'Inmueble')}* ({prop.get('ID', '')})\n"
    res += f"📍 {prop.get('Ubicacion', 'Consultar')}\n"
    res += f"🏙️ *{prop.get('Ciudad', '')}*\n\n"
    res += f"💰 *CANON:* {prop.get('Precio', 'Consultar')}\n"
    
    detalles = []
    if prop.get('Area_m2'): detalles.append(f"📐 {prop.get('Area_m2')} m²")
    if prop.get('Habitaciones'): detalles.append(f"🛏 {prop.get('Habitaciones')} Hab")
    if prop.get('Baños'): detalles.append(f"🚿 {prop.get('Baños')} Baños")
    res += " | ".join(detalles) + "\n\n"
    
    desc = prop.get('Descripcion_Plus', '').strip()
    if desc: res += f"📝 *Descripción:* \n{desc}\n\n"
    
    res += f"📅 *AGÉNDATE AQUÍ:* \n{prop.get('Link_agenamiento', 'https://wa.me/573024929820')}"
    res += f"\n\n*¿Ya lograste agendar o prefieres hablar con un asesor?* 😊"
    return res

def format_property_list(props, name, context=""):
    res = f"¡Claro, *{name}*! Encontré estas opciones {context}: 🏠✨\n"
    for i, p in enumerate(props, 1):
        res += f"\n*{i}. {p.get('Tipo','')}* en {p.get('Ciudad','')} ({p.get('ID','')})\n💰 {p.get('Precio','')}\n"
    res += "\n¿Cuál de estos te interesa conocer? Escribe solo el *número*. 🎯"
    return res
