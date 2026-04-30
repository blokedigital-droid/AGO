import os, json, time
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from bot_logic import process_message
from whatsapp_service import send_text_message

load_dotenv()
app = Flask(__name__)

@app.route('/webhook', methods=['GET'])
def verify_webhook():
    if request.args.get("hub.verify_token") == os.getenv('WHATSAPP_VERIFY_TOKEN'):
        return request.args.get("hub.challenge"), 200
    return 'Forbidden', 403

@app.route('/webhook', methods=['POST'])
def handle_webhook():
    body = request.get_json()
    try:
        if body.get('entry', [{}])[0].get('changes', [{}])[0].get('value', {}).get('messages'):
            message = body['entry'][0]['changes'][0]['value']['messages'][0]
            phone = message['from']
            text = message.get('text', {}).get('body', '').strip()
            
            if text:
                responses = process_message(phone, text)
                # Si la lógica nos devuelve una lista de mensajes, los enviamos uno por uno
                if isinstance(responses, list):
                    for i, resp in enumerate(responses):
                        send_text_message(phone, resp)
                        if i == 0: time.sleep(4) # Espera 4 segundos entre el mensaje 1 y el 2
                else:
                    send_text_message(phone, responses)
    except Exception as e:
        print(f"Error: {e}")
    return jsonify({"status": "ok"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)))
