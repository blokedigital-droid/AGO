import os, json, time, sqlite3, threading
from flask import Flask, request, jsonify, render_template_string
from dotenv import load_dotenv
from bot_logic import process_message, DB_PATH, get_user, save_chat
from whatsapp_service import send_text_message

load_dotenv()
app = Flask(__name__)

# --- MONITOR DE VENTAS RESPONSIVO (MOBILE-FIRST) ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>AGO - Monitor Inmobiliario</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        :root { --wa-green: #075e54; --wa-light: #dcf8c6; --wa-bg: #e5ddd5; }
        body { font-family: 'Segoe UI', sans-serif; background: #f0f2f5; margin: 0; display: flex; height: 100vh; overflow: hidden; }
        
        /* Sidebar para PC y Tablet */
        .sidebar { width: 320px; background: var(--wa-green); color: white; display: flex; flex-direction: column; flex-shrink: 0; }
        .sidebar-header { padding: 20px; background: #128c7e; text-align: center; font-weight: bold; border-bottom: 1px solid #ffffff22; }
        .client-list { flex-grow: 1; overflow-y: auto; }
        .client-link { display: block; padding: 15px 20px; color: white; text-decoration: none; border-bottom: 1px solid #ffffff11; transition: 0.3s; }
        .client-link:hover { background: #128c7e; }
        .client-link.active { background: #25d366; font-weight: bold; border-left: 6px solid white; }
        
        /* Contenido Principal */
        .main { flex-grow: 1; display: flex; flex-direction: column; background: var(--wa-bg); }
        .chat-header { background: var(--wa-green); color: white; padding: 15px; font-weight: bold; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
        .chat-box { flex-grow: 1; overflow-y: auto; padding: 20px; display: flex; flex-direction: column; }
        
        /* Burbujas de Chat */
        .msg { margin-bottom: 15px; padding: 10px 15px; border-radius: 10px; max-width: 80%; line-height: 1.4; position: relative; box-shadow: 0 1px 2px rgba(0,0,0,0.15); font-size: 0.95em; }
        .msg-AGO { align-self: flex-start; background: white; color: #333; border-top-left-radius: 0; }
        .msg-Cliente { align-self: flex-end; background: var(--wa-light); color: #333; border-top-right-radius: 0; }
        .time { font-size: 0.65em; color: #999; display: block; text-align: right; margin-top: 5px; }
        
        /* Botón de Rescate */
        .btn-rescue { background: #ff5722; color: white; border: none; padding: 8px 12px; border-radius: 5px; cursor: pointer; text-decoration: none; font-size: 0.8em; font-weight: bold; }
        .btn-rescue:hover { background: #f4511e; }

        /* Adaptación para Celulares */
        @media (max-width: 768px) {
            body { flex-direction: column; }
            .sidebar { width: 100%; height: 35vh; }
            .main { height: 65vh; }
            .sidebar-header { padding: 10px; font-size: 1em; }
            .msg { max-width: 90%; }
        }
    </style>
</head>
<body>
    <div class="sidebar">
        <div class="sidebar-header">AGO - Panel de Clientes 📱</div>
        <div class="client-list">
            {% for phone in clients %}
            <a href="/dashboard?key=ago2026&phone={{ phone }}" class="client-link {% if phone == selected_phone %}active{% endif %}">
                👤 {{ phone }}
            </a>
            {% endfor %}
        </div>
    </div>
    <div class="main">
        <div class="chat-header">
            <span>{% if selected_phone %} {{ selected_phone }} {% else %} Selecciona un chat {% endif %}</span>
            <a href="/rescue?key=ago2026" class="btn-rescue" onclick="return confirm('¿Enviar seguimiento a clientes no respondidos?')">🚀 RESCATAR CHATS</a>
        </div>
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
def health(): return jsonify({"status": "active", "version": "1.29"}), 200

@app.route('/rescue')
def rescue_chats():
    if request.args.get('key') != "ago2026": return "Acceso Denegado", 403
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        # Seleccionamos últimos mensajes que son del Cliente (No contestados)
        cursor.execute('''
            SELECT phone FROM chat_history 
            GROUP BY phone 
            HAVING id = MAX(id) AND sender = 'Cliente'
            LIMIT 5
        ''')
        rows = cursor.fetchall()
        count = 0
        for row in rows:
            phone = row[0]
            follow_up = "¡Hola! Soy *AGO*. 👋 Mil disculpas, tuve un inconveniente técnico y no pude responderte a tiempo. 🏠✨\n\nYa estoy de vuelta, ¿cuéntame en qué te puedo ayudar hoy?"
            send_text_message(phone, follow_up)
            save_chat(phone, "AGO", follow_up)
            count += 1
            time.sleep(2)
        conn.close()
        return f"Éxito: Se contactaron {count} clientes. 🎉"
    except Exception as e: return f"Error en Rescate: {e}"

@app.route('/dashboard')
def dashboard():
    if request.args.get('key') != "ago2026": return "Acceso Denegado", 403
    selected_phone = request.args.get('phone')
    try:
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
    except: return "Aún no hay conversaciones grabadas."

# --- BUFFER PARA MENSAJES INICIALES (DELAY 5S) ---
message_buffer = {}

def process_and_send(phone, is_initial):
    # Espera 5s solo si es el primer mensaje de la historia
    time.sleep(5 if is_initial else 0.5)
    if phone in message_buffer:
        full_text = " ".join(message_buffer[phone])
        del message_buffer[phone]
        responses = process_message(phone, full_text)
        if isinstance(responses, list):
            for i, r in enumerate(responses):
                send_text_message(phone, r)
                if i < len(responses)-1: time.sleep(2)
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
