import os, json, time, sqlite3
from flask import Flask, request, jsonify, render_template_string
from dotenv import load_dotenv
from bot_logic import process_message, DB_PATH
from whatsapp_service import send_text_message

load_dotenv()
app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>AGO - Monitor de Chats</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: sans-serif; background: #f0f2f5; margin: 0; padding: 20px; }
        .container { max-width: 800px; margin: auto; background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
        h2 { color: #1c1e21; border-bottom: 2px solid #075e54; padding-bottom: 10px; text-align: center; }
        .chat-box { border-bottom: 1px solid #eee; padding: 15px 0; }
        .sender { font-weight: bold; font-size: 1.1em; }
        .Cliente { color: #25d366; }
        .AGO { color: #34b7f1; }
        .time { font-size: 0.8em; color: #888; float: right; }
        .msg { margin-top: 8px; white-space: pre-wrap; line-height: 1.4; color: #444; }
    </style>
</head>
<body>
    <div class="container">
        <h2>🏠 AGO - Monitor de Ventas 🤖</h2>
        {% for chat in chats %}
        <div class="chat-box">
            <span class="time">{{ chat[4] }}</span>
            <span class="sender {{ chat[2] }}">{{ chat[2] }} ({{ chat[1] }}):</span>
            <div class="msg">{{ chat[3] }}</div>
        </div>
        {% endfor %}
    </div>
</body>
</html>
"""

@app.route('/health', methods=['GET'])
def health(): return jsonify({"status": "alive"}), 200

@app.route('/dashboard', methods=['GET'])
def dashboard():
    if request.args.get('key') != "ago2026": return "Acceso Denegado", 403
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM chat_history ORDER BY timestamp DESC LIMIT 100")
    chats = cursor.fetchall()
    conn.close()
    return render_template_string(HTML_TEMPLATE, chats=chats)

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
                if isinstance(responses, list):
                    for i, resp in enumerate(responses):
                        send_text_message(phone, resp); time.sleep(3)
                else: send_text_message(phone, responses)
    except: pass
    return jsonify({"status": "ok"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)))
