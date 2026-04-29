"""
Servidor Flask - Bot Inmobiliario AGO
Webhook para WhatsApp Business API.
"""

import os
import json
import logging
from flask import Flask, request, jsonify
from dotenv import load_dotenv

from bot_logic import process_message
from whatsapp_service import send_text_message, mark_as_read

load_dotenv()

app = Flask(__name__)

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('AGO-Bot')

VERIFY_TOKEN = os.getenv('WHATSAPP_VERIFY_TOKEN', 'mi_token_secreto_ago_2024')


@app.route('/webhook', methods=['GET'])
def verify_webhook():
    """
    Verificación del webhook de WhatsApp.
    Meta envía un GET con un challenge que debemos devolver.
    """
    mode = request.args.get('hub.mode')
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')

    if mode == 'subscribe' and token == VERIFY_TOKEN:
        logger.info("✅ Webhook verificado exitosamente")
        return challenge, 200
    else:
        logger.warning("❌ Verificación de webhook fallida")
        return 'Forbidden', 403


@app.route('/webhook', methods=['POST'])
def handle_webhook():
    """
    Recibe y procesa los mensajes entrantes de WhatsApp.
    """
    try:
        body = request.get_json()
        logger.info(f"📩 Webhook recibido: {json.dumps(body, indent=2, ensure_ascii=False)}")

        if not body:
            return jsonify({"status": "no body"}), 200

        if body.get('object') != 'whatsapp_business_account':
            return jsonify({"status": "not whatsapp"}), 200

        entries = body.get('entry', [])
        for entry in entries:
            changes = entry.get('changes', [])
            for change in changes:
                value = change.get('value', {})
                messages = value.get('messages', [])

                for message in messages:
                    process_incoming_message(message)

    except Exception as e:
        logger.error(f"❌ Error procesando webhook: {str(e)}", exc_info=True)

    return jsonify({"status": "ok"}), 200


def process_incoming_message(message):
    """Procesa un mensaje individual entrante."""
    msg_id = message.get('id', '')
    msg_from = message.get('from', '')
    msg_type = message.get('type', '')

    logger.info(f"📨 Mensaje de {msg_from} | Tipo: {msg_type} | ID: {msg_id}")

    # Marcar como leído
    mark_as_read(msg_id)

    # Solo procesamos mensajes de texto
    if msg_type == 'text':
        text = message.get('text', {}).get('body', '').strip()
        if not text:
            return

        logger.info(f"💬 Texto recibido de {msg_from}: {text}")

        # Generar respuesta (pasamos phone_number para personalización)
        response = process_message(msg_from, text)

        # Enviar respuesta
        result = send_text_message(msg_from, response)
        logger.info(f"📤 Respuesta enviada a {msg_from}: {result}")

    elif msg_type == 'interactive':
        interactive = message.get('interactive', {})
        interactive_type = interactive.get('type', '')

        if interactive_type == 'list_reply':
            selected = interactive.get('list_reply', {})
            text = selected.get('title', '') or selected.get('id', '')
        elif interactive_type == 'button_reply':
            selected = interactive.get('button_reply', {})
            text = selected.get('title', '') or selected.get('id', '')
        else:
            text = ''

        if text:
            response = process_message(msg_from, text)
            result = send_text_message(msg_from, response)
            logger.info(f"📤 Respuesta interactiva enviada a {msg_from}: {result}")

    else:
        response = ("¡Gracias por tu mensaje! 😊\n\n"
                     "Por ahora solo puedo procesar mensajes de texto. "
                     "Escríbeme lo que necesitas y con gusto te ayudo.\n\n"
                     "*AGO - Tu Agente Inmobiliario* 🏠")
        send_text_message(msg_from, response)


@app.route('/health', methods=['GET'])
def health_check():
    """Endpoint de salud para monitoreo."""
    return jsonify({
        "status": "healthy",
        "bot": "AGO - Agente Inmobiliario",
        "version": "1.1.0",
        "features": [
            "Personalización por nombre",
            "Búsqueda inteligente de inmuebles",
            "Requisitos por inmueble",
            "Link de estudio El Libertador",
            "Datos de inmobiliaria",
            "Solo muestra inmuebles disponibles"
        ]
    }), 200


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    logger.info(f"🚀 Bot AGO v1.1 iniciando en puerto {port}")
    app.run(host='0.0.0.0', port=port, debug=True)
