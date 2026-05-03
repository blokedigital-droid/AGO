import os, json, time, sqlite3, threading
from flask import Flask, request, jsonify, render_template_string
from dotenv import load_dotenv
from bot_logic import process_message, DB_PATH, get_user
from whatsapp_service import send_text_message

load_dotenv()
app = Flask(__name__)

# --- DASHBOARD HTML ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>AGO - Monitor de Chats</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: 'Segoe UI', sans-serif; background: #f0f2f5; margin: 0; display: flex; height: 100vh; }
        .sidebar { width: 280px; background: #075e54; color: white; overflow-y: auto; padding: 15px; border-right: 1px solid #ddd; }
        .client-link { display: block; padding: 12px; color: white; text-decoration: none; border-bottom: 1px solid #ffffff11; margin-bottom: 5px; border-radius: 5px; }
        .client-link:hover { background: #128c7e; }
        .client-link.active { background: #25d366; font-weight: bold; }
        .main { flex-grow: 1; display: flex; flex-direction: column; background: #e5ddd5; }
        .chat-box { flex-grow: 1; overflow-y: auto; padding: 20px; display: flex; flex-direction: column; }
        .msg { margin-bottom: 12px; padding: 10px 15px; border-radius: 8px; max-width: 75%; line-height: 1.4; box-shadow: 0 1px 1px rgba(0,0,0,0.1); }
        .msg-AGO { align-self: flex-start; background: white; color: #333; border-top-left-radius: 0; }
        .msg-Cliente { align-self: flex-end; background: #dcf8c6; color: #333; border-top-right-radius: 0; }
        .time { font-size: 0.7em; color: #999; display: block; text-align: right; margin-top: 4px; }
        .header { background: #075e54; color: white; padding: 15px; font-weight: bold; text-align: center; }
    </style>
</head>
<body>
    <div class="sidebar">
        <h3>📱 Clientes</h3>
        {% for phone in clients %}
        <a href="/dashboard?key=ago2026&phone={{ phone }}" class="client-link {% if phone == selected_phone %}active{% endif %}">
            {{ phone }}
        </a>
        {% endfor %}
    </div>
    <div class="main">
        <div class="header">{% if selected_phone %} Conversación: {{ selected_phone }} {% else %} AGO - Panel de Control {% endif %}</div>
        <div class="chat-box">
            {% for chat in chats %}
            <div class="msg msg-{{ chat[2] }}">
                <div style="white-space: pre-wrap;">{{ chat[3] }}</div>
                <span class="time">{{ chat[4] }}</span>
            </div>
            {% endfor %}
        </div>
    </div>
</body>
</html>
"""

@app.route('/health')
def health(): return jsonify({"status": "active", "version": "1.24"}), 200

@app.route('/dashboard')
def dashboard():
    if request.args.get('key') != "ago2026": return "Acceso Denegado", 403
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
    # TIEMPO DE ESPERA: 5s si es inicio, 1s si ya hay charla
    wait_time = 5 if is_initial else 1
    time.sleep(wait_time)
    
    if phone in message_buffer:
        full_text = " ".join(message_buffer[phone])
        del message_buffer[phone]
        responses = process_message(phone, full_text)
        
        if isinstance(responses, list):
            for i, r in enumerate(responses):
                send_text_message(phone, r)
                if i < len(responses)-1: time.sleep(2)
        else:
            send_text_message(phone, responses)

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
            phone = message['from']
            text = message.get('text', {}).get('body', '').strip()
            
            if text:
                user = get_user(phone)
                is_initial = (user["state"] == "new")
                
                if phone not in message_buffer:
                    message_buffer[phone] = [text]
                    threading.Thread(target=process_and_send, args=(phone, is_initial)).start()
                else:
                    message_buffer[phone].append(text)
    except: pass
    return jsonify({"status": "ok"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)))
