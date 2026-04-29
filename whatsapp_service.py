import os, requests
from dotenv import load_dotenv
load_dotenv()

ACCESS_TOKEN = os.getenv('WHATSAPP_ACCESS_TOKEN')
PHONE_NUMBER_ID = os.getenv('WHATSAPP_PHONE_NUMBER_ID')
API_URL = f"https://graph.facebook.com/v21.0/{PHONE_NUMBER_ID}/messages"
HEADERS = {"Authorization": f"Bearer {ACCESS_TOKEN}", "Content-Type": "application/json"}

def send_text_message(to, text):
    payload = {"messaging_product": "whatsapp", "to": to, "type": "text", "text": {"preview_url": True, "body": text}}
    return requests.post(API_URL, json=payload, headers=HEADERS).json()

def send_media_message(to, media_url, media_type="image"):
    # Esta función envía la imagen/video si el link es directo (.jpg, .mp4)
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": media_type,
        media_type: {"link": media_url}
    }
    return requests.post(API_URL, json=payload, headers=HEADERS).json()

def mark_as_read(message_id):
    payload = {"messaging_product": "whatsapp", "status": "read", "message_id": message_id}
    requests.post(API_URL, json=payload, headers=HEADERS)
