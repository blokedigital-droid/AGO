import os
import requests
import csv
from io import StringIO
from thefuzz import fuzz

# ID de tu Google Sheet
SHEET_ID = os.getenv('GOOGLE_SHEET_ID', '1hue1nHUQ6yzmrsRqPqjD7mksPnGFbfduxx8v7V5elr4')

def fetch_all_properties():
    """Lee el Excel público como CSV."""
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"
    try:
        response = requests.get(url)
        if response.status_code != 200:
            return []
        content = StringIO(response.text)
        reader = csv.DictReader(content)
        return list(reader)
    except:
        return []

def get_available_properties():
    """Filtra solo los disponibles."""
    all_props = fetch_all_properties()
    return [p for p in all_props if p.get('Estado', '').strip().lower() in ['', 'disponible']]

def search_properties(query):
    """Busca inmuebles según lo que escriba el cliente."""
    available = get_available_properties()
    if not available: return []
    query_lower = query.lower()
    scored = []
    for prop in available:
        score = 0
        text = f"{prop.get('Tipo','')} {prop.get('Ubicacion','')} {prop.get('Ciudad','')} {prop.get('Descripcion_Plus','')}".lower()
        if query_lower in text: score += 50
        ratio = fuzz.partial_ratio(query_lower, text)
        if ratio > 60: score += ratio
        if score > 0: scored.append((score, prop))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [item[1] for item in scored[:3]]

def format_property_response(prop, include_apply_info=False):
    """Crea el mensaje bonito para WhatsApp."""
    res = f"🏠 *{prop.get('Tipo', 'Inmueble')}*\n"
    res += f"📍 {prop.get('Ubicacion', '')}, {prop.get('Ciudad', '')}\n"
    res += f"💰 *Canon: {prop.get('Precio', 'Consultar')}*\n"
    res += f"🛏 {prop.get('Habitaciones', 'N/A')} Hab | 🚿 {prop.get('Baños', 'N/A')} Baños\n"
    if prop.get('Link_Fotos'): res += f"\n📸 *Fotos:* {prop.get('Link_Fotos')}"
    if prop.get('Link_Video'): res += f"\n🎥 *Video:* {prop.get('Link_Video')}"
    if prop.get('Link_agenamiento'): res += f"\n📅 *Agendar visita:* {prop.get('Link_agenamiento')}"
    return res

def format_apply_info(prop):
    """Crea la info de requisitos y estudio."""
    res = f"📋 *Trámite para: {prop.get('Tipo', 'Inmueble')}*\n\n"
    res += f"✅ *Requisitos:* {prop.get('Requisitos', 'Consultar con asesor')}\n\n"
    res += f"📄 *Estudio El Libertador:* https://www.ellibertador.co/\n"
    res += f"\n🏢 *Código Inmobiliaria:* AGO-2026"
    return res
