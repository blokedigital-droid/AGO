"""
Servicio de WhatsApp Business API para el Bot Inmobiliario AGO.
Envía mensajes de texto e interactivos a los clientes.
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

ACCESS_TOKEN = os.getenv('WHATSAPP_ACCESS_TOKEN')
PHONE_NUMBER_ID = os.getenv('WHATSAPP_PHONE_NUMBER_ID')
API_URL = f"https://graph.facebook.com/v21.0/{PHONE_NUMBER_ID}/messages"

HEADERS = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "Content-Type": "application/json"
}


def send_text_message(to, text):
    """Envía un mensaje de texto simple al cliente."""
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "text",
        "text": {
            "preview_url": True,
            "body": text
        }
    }
    response = requests.post(API_URL, json=payload, headers=HEADERS)
    return response.json()


def send_interactive_list(to, header_text, body_text, button_text, sections):
    """
    Envía un mensaje interactivo tipo lista.
    Útil para mostrar opciones de inmuebles.
    """
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "list",
            "header": {
                "type": "text",
                "text": header_text
            },
            "body": {
                "text": body_text
            },
            "action": {
                "button": button_text,
                "sections": sections
            }
        }
    }
    response = requests.post(API_URL, json=payload, headers=HEADERS)
    return response.json()


def mark_as_read(message_id):
    """Marca un mensaje como leído (doble check azul)."""
    payload = {
        "messaging_product": "whatsapp",
        "status": "read",
        "message_id": message_id
    }
    requests.post(API_URL, json=payload, headers=HEADERS)
