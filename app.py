import os, json, time, sqlite3, threading
from flask import Flask, request, jsonify, render_template_string
from dotenv import load_dotenv
from bot_logic import process_message, DB_PATH, get_user, save_chat
from whatsapp_service import send_text_message

load_dotenv()
app = Flask(__name__)

# --- DASHBOARD HTML (CON BOTÓN DE RESCATE) ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>AGO - Monitor Inmobiliario</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        :root { --whatsapp-green: #075e54; --light-green: #dcf8c6; --bg-gray: #e5ddd5; }
        body { font-family: 'Segoe UI', sans-serif; background: #f0f2f5; margin: 0; display: flex; height: 100vh; }
        .sidebar { width: 300px; background: var(--whatsapp-green); color: white; display: flex; flex-direction: column; }
        .sidebar-header { padding: 20px; background: #128c7e; text-align: center; font-weight: bold; border-bottom: 1px solid #ffffff22; }
        .client-list { flex-grow: 1; overflow-y: auto; }
        .client-link { display: block; padding: 15px 20px; color: white; text-decoration: none; border-bottom: 1px solid #ffffff11; }
        .client-link.active { background: #25d366; border-left: 5px solid white; }
        .main { flex-grow: 1; display: flex; flex-direction: column; background: var(--bg-gray); }
        .chat-header { background: var(--whatsapp-green); color: white; padding: 15px; font-weight: bold; display: flex; justify-content: space-between; align-items: center; }
        .chat-box { flex-grow: 1; overflow-y: auto; padding: 20px; display: flex; flex-direction: column; }
        .msg { margin-bottom: 10px; padding: 8px 12px; border-radius: 8px; max-width: 85%; font-size: 0.95em; box-shadow: 0 1px 1px rgba(0,0,0,0.1); }
        .msg-AGO { align-self: flex-start; background: white; }
        .msg-Cliente { align-self: flex-end; background: var(--light-green); }
        .btn-rescue { background: #ff5722; color: white; border: none; padding: 8px 15px; border-radius: 5px; cursor: pointer; text-decoration: none; font-size: 0.8em; }
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
        <div class="chat-header">
            <span>{% if selected_phone %} Chat: {{ selected_phone }} {% else %} Monitor AGO {% endif %}</span>
            <a href="/rescue?key=ago2026" class="btn-rescue" onclick="return confirm('¿Quieres enviar un mensaje de seguimiento a los clientes no contactados?')">🚀 Rescatar Chats</a>
        </div>
        <div class="chat-box">
            {% for chat in chats %}
            <div class="msg msg-{{ chat[2] }}"><div>{{ chat[3] }}</div><small style="color:#999;font-size:0.7em;">{{ chat[4] }}</small></div>
            {% endfor %}
        </div>
    </div>
</body>
</html>
"""

@app.route('/rescue')
def rescue_chats():
    if request.args.get('key') != "ago2026": return "Denegado", 403
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        # Buscamos números donde el último mensaje NO fue de AGO
        cursor.execute('''
            SELECT phone FROM chat_history 
            GROUP BY phone 
            HAVING id = MAX(id) AND sender = 'Cliente'
            LIMIT 5
        ''')
        unanswered = cursor.fetchall()
        count = 0
        for row in unanswered:
            phone = row[0]
            msg = "¡Hola! Soy *AGO* de la inmobiliaria. 👋 Mil disculpas, tuvimos un pequeño problema técnico y no pudimos responderte a tiempo. 🏠✨\n\nYa estoy aquí de nuevo, ¿en qué te puedo ayudar hoy?"
            send_text_message(phone, msg)
            save_chat(phone, "AGO", msg)
            count += 1
            time.sleep(2)
        conn.close()
        return f"Éxito: Se contactaron {count} clientes olvidados. 🎉"
    except Exception as e: return f"Error: {e}"

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
    time.sleep(5 if is_initial else 0.5) # 5s SOLO AL INICIO
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
            msg = body['entry'][0]['changes'][0]['value']['messages'][0]
            phone, text = msg['from'], msg.get('text', {}).get('body', '').strip()
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
