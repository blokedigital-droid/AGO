import os, requests
from dotenv import load_dotenv
load_dotenv()

ACCESS_TOKEN = os.getenv('WHATSAPP_ACCESS_TOKEN')
PHONE_NUMBER_ID = os.getenv('WHATSAPP_PHONE_NUMBER_ID')
# Versión v25.0 para asegurar miniaturas grandes
API_URL = f"https://graph.facebook.com/v25.0/{PHONE_NUMBER_ID}/messages"
HEADERS = {"Authorization": f"Bearer {ACCESS_TOKEN}", "Content-Type": "application/json"}

def send_text_message(to, text):
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"preview_url": True, "body": text}
    }
    return requests.post(API_URL, json=payload, headers=HEADERS).json()
