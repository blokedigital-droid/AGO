"""
Servicio de Google Sheets para el Bot Inmobiliario AGO.
Lee y busca inmuebles en el spreadsheet conectado.
Soporta columnas: Requisitos, Link_Estudio, Datos_Inmobiliaria.
"""

import os
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from thefuzz import fuzz
from dotenv import load_dotenv

load_dotenv()

SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
SHEET_ID = os.getenv('GOOGLE_SHEET_ID', '1hue1nHUQ6yzmrsRqPqjD7mksPnGFbfduxx8v7V5elr4')
CREDENTIALS_PATH = os.getenv('GOOGLE_CREDENTIALS_PATH', 'credentials.json')


def get_sheets_service():
    """Crea y retorna el servicio autenticado de Google Sheets."""
    creds = Credentials.from_service_account_file(CREDENTIALS_PATH, scopes=SCOPES)
    service = build('sheets', 'v4', credentials=creds)
    return service


def fetch_all_properties():
    """Obtiene todos los inmuebles del Google Sheet. Soporta columnas dinámicas."""
    service = get_sheets_service()
    sheet = service.spreadsheets()

    # Obtener nombres de hojas
    spreadsheet = sheet.get(spreadsheetId=SHEET_ID).execute()
    sheet_name = spreadsheet['sheets'][0]['properties']['title']

    # Leer datos (rango amplio para columnas futuras)
    result = sheet.values().get(
        spreadsheetId=SHEET_ID,
        range=f"'{sheet_name}'!A1:Z500"
    ).execute()

    values = result.get('values', [])
    if not values or len(values) < 2:
        return []

    headers = values[0]
    properties = []
    for row in values[1:]:
        while len(row) < len(headers):
            row.append('')
        prop = dict(zip(headers, row))
        properties.append(prop)

    return properties


def get_available_properties():
    """Retorna solo los inmuebles con estado 'Disponible'."""
    all_props = fetch_all_properties()
    available = []
    for p in all_props:
        estado = p.get('Estado', '').strip().lower()
        if estado == '' or 'disponible' in estado:
            available.append(p)
    return available


def search_properties(query):
    """
    Busca inmuebles relevantes según el mensaje del cliente.
    Usa búsqueda difusa (fuzzy) sobre tipo, ubicación, ciudad y descripción.
    """
    available = get_available_properties()
    if not available:
        return []

    query_lower = query.lower()
    scored = []
    keywords = query_lower.split()

    for prop in available:
        score = 0
        searchable_fields = [
            prop.get('Tipo', ''),
            prop.get('Operacion', ''),
            prop.get('Ubicacion', ''),
            prop.get('Ciudad', ''),
            prop.get('Descripcion_Plus', ''),
            prop.get('ID', ''),
        ]
        combined_text = ' '.join(searchable_fields).lower()

        # Búsqueda por ID exacto (ej: "AGO001")
        for kw in keywords:
            if kw.upper().startswith('AGO') and kw.upper() in prop.get('ID', '').upper():
                score += 100

        # Búsqueda por ciudad
        ciudad = prop.get('Ciudad', '').lower()
        if ciudad and ciudad in query_lower:
            score += 40

        # Búsqueda por tipo de inmueble
        tipo = prop.get('Tipo', '').lower()
        type_keywords = {
            'apartamento': ['apartamento', 'apto', 'apt'],
            'apartaestudio': ['apartaestudio', 'estudio', 'aparta'],
            'casa': ['casa'],
            'local': ['local', 'comercial'],
            'duplex': ['duplex', 'dúplex'],
        }
        for tipo_key, aliases in type_keywords.items():
            if tipo_key in tipo:
                for alias in aliases:
                    if alias in query_lower:
                        score += 35

        # Búsqueda por operación
        operacion = prop.get('Operacion', '').lower()
        if 'arriendo' in query_lower or 'alquiler' in query_lower or 'arrendar' in query_lower or 'rentar' in query_lower:
            if 'arriendo' in operacion:
                score += 25
        if 'venta' in query_lower or 'comprar' in query_lower or 'compra' in query_lower:
            if 'venta' in operacion:
                score += 25

        # Búsqueda por precio
        precio = prop.get('Precio', '').replace('$', '').replace(',', '').replace('.', '').strip()
        for kw in keywords:
            clean_kw = kw.replace('$', '').replace(',', '').replace('.', '')
            if clean_kw.isdigit() and precio and clean_kw in precio:
                score += 30

        # Búsqueda por habitaciones
        habs = prop.get('Habitaciones', '')
        for kw in keywords:
            if kw.isdigit() and ('habitacion' in query_lower or 'cuarto' in query_lower or 'alcoba' in query_lower):
                if kw == habs:
                    score += 20

        # Búsqueda por ubicación (fuzzy)
        ubicacion = prop.get('Ubicacion', '').lower()
        if ubicacion:
            ratio = fuzz.partial_ratio(query_lower, ubicacion)
            if ratio > 60:
                score += int(ratio * 0.3)

        # Búsqueda difusa general
        general_ratio = fuzz.partial_ratio(query_lower, combined_text)
        if general_ratio > 50:
            score += int(general_ratio * 0.15)

        if score > 0:
            scored.append((score, prop))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [item[1] for item in scored[:3]]


def format_property_response(prop, include_apply_info=False):
    """
    Formatea un inmueble como mensaje de WhatsApp.
    Incluye Requisitos, Link_Estudio y Datos_Inmobiliaria.
    Si include_apply_info=True, muestra toda la info de aplicación.
    """
    lines = []
    lines.append(f"🏠 *{prop.get('Tipo', 'Inmueble')}* - {prop.get('ID', '')}")
    lines.append(f"📍 {prop.get('Ubicacion', 'Sin ubicación')}, {prop.get('Ciudad', '')}")
    lines.append(f"💰 *Canon: {prop.get('Precio', 'Consultar')}*")
    lines.append(f"📐 Área: {prop.get('Area_m2', 'N/A')} m²")
    lines.append(f"🛏 Habitaciones: {prop.get('Habitaciones', 'N/A')}")
    lines.append(f"🚿 Baños: {prop.get('Baños', 'N/A')}")

    parq = prop.get('Parqueaderos', '')
    tipo_parq = prop.get('Tipo_parqueadero', '')
    if parq:
        lines.append(f"🅿️ Parqueadero: {parq} ({tipo_parq})")

    desc = prop.get('Descripcion_Plus', '')
    if desc and len(desc) > 200:
        desc = desc[:200] + '...'
    if desc:
        lines.append(f"\n📝 {desc}")

    link = prop.get('Link_Fotos', '')
    if link:
        lines.append(f"\n📸 *Ver fotos:* {link}")

    # --- Información de aplicación ---
    link_estudio = prop.get('Link_Estudio', '').strip()
    if link_estudio:
        lines.append(f"\n📄 *Estudio en línea (El Libertador):* {link_estudio}")

    datos_inmobiliaria = prop.get('Datos_Inmobiliaria', '').strip()
    if datos_inmobiliaria:
        lines.append(f"\n🏢 *Inmobiliaria:* {datos_inmobiliaria}")

    return '\n'.join(lines)


def format_apply_info(prop):
    """
    Formatea solo la información de aplicación/trámite de un inmueble.
    Incluye Requisitos, Link_Estudio y Datos_Inmobiliaria.
    """
    lines = []
    lines.append(f"📋 *Información para Aplicar - {prop.get('Tipo', 'Inmueble')}* ({prop.get('ID', '')})")
    lines.append(f"📍 {prop.get('Ubicacion', '')}, {prop.get('Ciudad', '')}")
    lines.append("")

    requisitos = prop.get('Requisitos', '').strip()
    if requisitos:
        lines.append(f"✅ *Requisitos:*")
        lines.append(f"{requisitos}")
        lines.append("")

    link_estudio = prop.get('Link_Estudio', '').strip()
    if link_estudio:
        lines.append(f"📄 *Realizar estudio en línea (El Libertador):*")
        lines.append(f"{link_estudio}")
        lines.append("")

    datos_inmobiliaria = prop.get('Datos_Inmobiliaria', '').strip()
    if datos_inmobiliaria:
        lines.append(f"🏢 *Datos de la Inmobiliaria:*")
        lines.append(f"{datos_inmobiliaria}")
        lines.append("")

    if not requisitos and not link_estudio and not datos_inmobiliaria:
        lines.append("ℹ️ Aún no tenemos los datos de aplicación para este inmueble. Un asesor te contactará con los detalles.")

    return '\n'.join(lines)
