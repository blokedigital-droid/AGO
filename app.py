import os, json, time, sqlite3, threading
from flask import Flask, request, jsonify, render_template_string
from dotenv import load_dotenv
from bot_logic import process_message, DB_PATH, get_user, save_chat, handle_and_save
from whatsapp_service import send_text_message

load_dotenv()
app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>AGO - Monitor Inmobiliario</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        :root { --whatsapp-green: #075e54; --light-green: #dcf8c6; --bg-gray: #e5ddd5; }
        body { font-family: 'Segoe UI', sans-serif; background: #f0f2f5; margin: 0; display: flex; height: 100vh; flex-direction: row; }
        .sidebar { width: 300px; background: var(--whatsapp-green); color: white; display: flex; flex-direction: column; transition: 0.3s; }
        .sidebar-header { padding: 20px; background: #128c7e; text-align: center; font-weight: bold; font-size: 1.2em; border-bottom: 1px solid #ffffff22; }
        .client-list { flex-grow: 1; overflow-y: auto; }
        .client-link { display: block; padding: 15px 20px; color: white; text-decoration: none; border-bottom: 1px solid #ffffff11; }
        .client-link.active { background: #25d366; border-left: 5px solid white; }
        .main { flex-grow: 1; display: flex; flex-direction: column; background: var(--bg-gray); position: relative; }
        .chat-header { background: var(--whatsapp-green); color: white; padding: 15px; font-weight: bold; box-shadow: 0 2px 5px rgba(0,0,0,0.1); z-index: 10; }
        .chat-box { flex-grow: 1; overflow-y: auto; padding: 20px; display: flex; flex-direction: column; }
        .msg { margin-bottom: 10px; padding: 8px 12px; border-radius: 8px; max-width: 85%; font-size: 0.95em; position: relative; box-shadow: 0 1px 1px rgba(0,0,0,0.1); }
        .msg-AGO { align-self: flex-start; background: white; color: #333; }
        .msg-Cliente { align-self: flex-end; background: var(--light-green); color: #333; }
        .time { font-size: 0.65em; color: #999; display: block; text-align: right; margin-top: 4px; }
        @media (max-width: 768px) {
            body { flex-direction: column; }
            .sidebar { width: 100%; height: 30vh; }
            .main { height: 70vh; }
        }
    </style>
</head>
<body>
    <div class="sidebar">
        <div class="sidebar-header">AGO - Clientes</div>
        <div class="client-list">
            {% for phone in clients %}
            <a href="/dashboard?key=ago2026&phone={{ phone }}" class="client-link {% if phone == selected_phone %}active{% endif %}">📱 {{ phone }}</a>
            {% endfor %}
        </div>
    </div>
    <div class="main">
        {% if selected_phone %}
        <div class="chat-header">Conversación con {{ selected_phone }}</div>
        <div class="chat-box">
            {% for chat in chats %}
            <div class="msg msg-{{ chat[2] }}"><div style="white-space: pre-wrap;">{{ chat[3] }}</div><span class="time">{{ chat[4] }}</span></div>
            {% endfor %}
        </div>
        {% else %}
        <div style="display:flex; align-items:center; justify-content:center; height:100%; color:#888;"><h3>Selecciona un cliente</h3></div>
        {% endif %}
    </div>
</body>
</html>
"""

@app.route('/dashboard')
def dashboard():
    if request.args.get('key') != "ago2026": return "Denegado", 403
    selected_phone = request.args.get('phone')
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT phone FROM chat_history ORDER BY timestamp DESC")
    clients = [row[0] for row in cursor.fetchall()]
    chats = []
    if selected_phone:
        cursor.execute("SELECT * FROM chat_history WHERE phone = ? ORDER BY timestamp ASC", (selected_phone,))
        chats = cursor.fetchall()
    conn.close()
    return render_template_string(HTML_TEMPLATE, clients=clients, chats=chats, selected_phone=selected_phone)

message_buffer = {}

def process_and_send(phone, is_initial):
    time.sleep(5 if is_initial else 0.5)
    if phone in message_buffer:
        full_text = " ".join(message_buffer[phone])
        del message_buffer[phone]
        responses = process_message(phone, full_text)
        if isinstance(responses, list):
            for r in responses: send_text_message(phone, r); time.sleep(2)
        else: send_text_message(phone, responses)

@app.route('/webhook', methods=['GET', 'POST'])
def handle_webhook():
    if request.method == 'GET':
        if request.args.get("hub.verify_token") == os.getenv('WHATSAPP_VERIFY_TOKEN'):
            return request.args.get("hub.challenge"), 200
        return 'Forbidden', 403
    body = request.get_json()
    try:
        if body.get('entry', [{}])[0].get('changes', [{}])[0].get('value', {}).get('messages'):
            message = body['entry'][0]['changes'][0]['value']['messages'][0]
            phone, text = message['from'], message.get('text', {}).get('body', '').strip()
            if text:
                user = get_user(phone)
                is_initial = (user["state"] == "new")
                if phone not in message_buffer:
                    message_buffer[phone] = [text]
                    threading.Thread(target=process_and_send, args=(phone, is_initial)).start()
                else: message_buffer[phone].append(text)
    except: pass
    return jsonify({"status": "ok"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)))
