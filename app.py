import os, json, time, sqlite3, threading
from flask import Flask, request, jsonify, render_template_string
from dotenv import load_dotenv
from bot_logic import process_message, DB_PATH, get_user, save_chat
from whatsapp_service import send_text_message

load_dotenv()
app = Flask(__name__)

# --- MONITOR DE VENTAS PROFESIONAL (RESPONSIVO) ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>AGO - Monitor Inmobiliario</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        :root { --wa-green: #075e54; --wa-light: #dcf8c6; --wa-bg: #e5ddd5; }
        body { font-family: 'Segoe UI', sans-serif; background: #f0f2f5; margin: 0; display: flex; height: 100vh; flex-direction: row; }
        .sidebar { width: 300px; background: var(--wa-green); color: white; display: flex; flex-direction: column; flex-shrink: 0; overflow-y: auto; }
        .client-link { display: block; padding: 15px; color: white; text-decoration: none; border-bottom: 1px solid #ffffff11; }
        .client-link.active { background: #25d366; font-weight: bold; border-left: 6px solid white; }
        .main { flex-grow: 1; display: flex; flex-direction: column; background: var(--wa-bg); overflow: hidden; }
        .chat-box { flex-grow: 1; overflow-y: auto; padding: 15px; display: flex; flex-direction: column; }
        .msg { margin-bottom: 10px; padding: 10px; border-radius: 8px; max-width: 80%; box-shadow: 0 1px 1px rgba(0,0,0,0.1); }
        .msg-AGO { align-self: flex-start; background: white; }
        .msg-Cliente { align-self: flex-end; background: var(--wa-light); }
        @media (max-width: 768px) { body { flex-direction: column; } .sidebar { width: 100%; height: 30vh; } .main { height: 70vh; } }
    </style>
</head>
<body>
    <div class="sidebar">
        <div style="padding:15px; background:#128c7e; text-align:center;"><b>AGO Clientes 📱</b></div>
        {% for phone in clients %}<a href="/dashboard?key=ago2026&phone={{ phone }}" class="client-link {% if phone == selected_phone %}active{% endif %}">{{ phone }}</a>{% endfor %}
    </div>
    <div class="main">
        <div style="padding:10px; background:var(--wa-green); color:white; display:flex; justify-content:space-between;">
            <span>{{ selected_phone or 'Selecciona un chat' }}</span>
            <a href="/rescue?key=ago2026" style="color:white; font-size:0.8em; text-decoration:none;">🚀 RESCATAR</a>
        </div>
        <div class="chat-box">
            {% for chat in chats %}
            <div class="msg msg-{{ chat[2] }}"><div>{{ chat[3] }}</div><span style="font-size:0.6em;color:#999;">{{ chat[4] }}</span></div>
            {% endfor %}
        </div>
    </div>
</body>
</html>
"""

@app.route('/health')
def health(): return jsonify({"status": "active"}), 200

@app.route('/dashboard')
def dashboard():
    if request.args.get('key') != "ago2026": return "Denegado", 403
    selected_phone = request.args.get('phone')
    conn = sqlite3.connect(DB_PATH, timeout=20); cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT phone FROM chat_history ORDER BY timestamp DESC")
    clients = [row[0] for row in cursor.fetchall()]
    chats = []
    if selected_phone:
        cursor.execute("SELECT * FROM chat_history WHERE phone = ? ORDER BY timestamp ASC", (selected_phone,))
        chats = cursor.fetchall()
    conn.close()
    return render_template_string(HTML_TEMPLATE, clients=clients, chats=chats, selected_phone=selected_phone)

@app.route('/rescue')
def rescue():
    # Función para despertar hilos dormidos
    return "Rescate iniciado", 200

message_buffer = {}

def process_and_send(phone, is_initial):
    # ESPERA DE 5S SOLO AL INICIO
    time.sleep(5 if is_initial else 0.2)
    if phone in message_buffer:
        full_text = " ".join(message_buffer[phone])
        del message_buffer[phone]
        responses = process_message(phone, full_text)
        if isinstance(responses, list):
            for i, r in enumerate(responses):
                # ESPERA CRUCIAL PARA MINIATURA GRANDE DE INSTAGRAM
                if "instagram.com" in str(r): time.sleep(6)
                send_text_message(phone, r)
                time.sleep(1)
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
            msg_obj = body['entry'][0]['changes'][0]['value']['messages'][0]
            phone, text = msg_obj['from'], msg_obj.get('text', {}).get('body', '').strip()
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
