import os, json, time, sqlite3, threading
from flask import Flask, request, jsonify, render_template_string
from dotenv import load_dotenv
from bot_logic import process_message, DB_PATH, get_user, save_chat
from whatsapp_service import send_text_message

load_dotenv()
app = Flask(__name__)

# --- DASHBOARD PROFESIONAL V1.43 (CON REPORTE DE RESCATE) ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>AGO - Monitor Inmobiliario</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        :root { --wa-green: #075e54; --wa-light: #dcf8c6; --wa-bg: #e5ddd5; }
        body { font-family: 'Segoe UI', sans-serif; background: #f0f2f5; margin: 0; display: flex; height: 100vh; overflow: hidden; flex-direction: row; }
        .sidebar { width: 320px; background: var(--wa-green); color: white; display: flex; flex-direction: column; flex-shrink: 0; overflow-y: auto; }
        .sidebar-header { padding: 20px; background: #128c7e; text-align: center; font-weight: bold; border-bottom: 1px solid #ffffff22; }
        .client-link { display: block; padding: 15px 20px; color: white; text-decoration: none; border-bottom: 1px solid #ffffff11; transition: 0.3s; }
        .client-link.active { background: #25d366; border-left: 6px solid white; font-weight: bold; }
        .main { flex-grow: 1; display: flex; flex-direction: column; background: var(--wa-bg); }
        .chat-header { background: var(--wa-green); color: white; padding: 15px; font-weight: bold; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
        .chat-box { flex-grow: 1; overflow-y: auto; padding: 20px; display: flex; flex-direction: column; }
        .msg { margin-bottom: 12px; padding: 10px 15px; border-radius: 8px; max-width: 80%; line-height: 1.4; box-shadow: 0 1px 2px rgba(0,0,0,0.1); font-size: 0.95em; }
        .msg-AGO { align-self: flex-start; background: white; color: #333; }
        .msg-Cliente { align-self: flex-end; background: var(--wa-light); color: #333; }
        .alert { padding: 12px; background: #fff3cd; color: #856404; text-align: center; font-weight: bold; border-bottom: 2px solid #ffeeba; }
        @media (max-width: 768px) { body { flex-direction: column; } .sidebar { width: 100%; height: 35vh; } .main { height: 65vh; } }
    </style>
</head>
<body>
    <div class="sidebar">
        <div class="sidebar-header">AGO - Panel de Clientes 📱</div>
        <div class="client-list">
            {% for phone in clients %}<a href="/dashboard?key=ago2026&phone={{ phone }}" class="client-link {% if phone == selected_phone %}active{% endif %}">👤 {{ phone }}</a>{% endfor %}
        </div>
    </div>
    <div class="main">
        {% if rescue_report %}<div class="alert">{{ rescue_report }}</div>{% endif %}
        <div class="chat-header">
            <span>{% if selected_phone %} Chat con {{ selected_phone }} {% else %} AGO Monitor Inmobiliario {% endif %}</span>
            <a href="/rescue?key=ago2026" style="background:#ff5722;color:white;padding:10px 18px;border-radius:5px;text-decoration:none;font-size:0.85em;font-weight:bold;box-shadow: 0 2px 4px rgba(0,0,0,0.2);">🚀 RESCATAR CHATS</a>
        </div>
        <div class="chat-box">
            {% for chat in chats %}<div class="msg msg-{{ chat[2] }}"><div>{{ chat[3] }}</div><small style="font-size:0.65em;color:#999;display:block;text-align:right;margin-top:5px;">{{ chat[4] }}</small></div>{% endfor %}
        </div>
    </div>
</body>
</html>
"""

@app.route('/health')
def health(): return jsonify({"status": "active", "version": "1.43"}), 200

@app.route('/rescue')
def rescue_chats():
    if request.args.get('key') != "ago2026": return "Acceso Denegado", 403
    try:
        conn = sqlite3.connect(DB_PATH, timeout=20); cursor = conn.cursor()
        # Seleccionamos números donde el último mensaje fue del Cliente (o sea, AGO no respondió)
        cursor.execute("SELECT phone FROM chat_history GROUP BY phone HAVING id = MAX(id) AND sender = 'Cliente' LIMIT 10")
        rows = cursor.fetchall(); rescued_list = []
        for row in rows:
            phone = row[0]
            follow_up = "¡Hola de nuevo! 👋 Soy *AGO*. Mil disculpas, tuvimos un pequeño inconveniente técnico y no pude responderte a tiempo. Ya estoy aquí, ¿cuéntame en qué te puedo ayudar?"
            send_text_message(phone, follow_up)
            save_chat(phone, "AGO", follow_up)
            rescued_list.append(phone)
            time.sleep(2)
        conn.close()
        msg_report = f"✅ Rescate exitoso para los números: {', '.join(rescued_list)}" if rescued_list else "No se encontraron chats por rescatar (todos están al día)."
        return dashboard(msg_report)
    except Exception as e: return f"Error en Proceso de Rescate: {e}"

@app.route('/dashboard')
def dashboard(rescue_report=None):
    if request.args.get('key') != "ago2026": return "Acceso Denegado", 403
    selected_phone = request.args.get('phone')
    try:
        conn = sqlite3.connect(DB_PATH, timeout=20); cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT phone FROM chat_history ORDER BY timestamp DESC")
        clients = [row[0] for row in cursor.fetchall()]; chats = []
        if selected_phone:
            cursor.execute("SELECT * FROM chat_history WHERE phone = ? ORDER BY timestamp ASC", (selected_phone,))
            chats = cursor.fetchall()
        conn.close()
        return render_template_string(HTML_TEMPLATE, clients=clients, chats=chats, selected_phone=selected_phone, rescue_report=rescue_report)
    except: return "Error cargando monitor. Intenta refrescar la página."

message_buffer = {}

def process_and_send(phone, is_initial):
    time.sleep(5 if is_initial else 0.5)
    if phone in message_buffer:
        full_text = " ".join(message_buffer[phone]); del message_buffer[phone]
        responses = process_message(phone, full_text)
        if isinstance(responses, list):
            for i, r in enumerate(responses):
                if "instagram.com" in str(r): time.sleep(10) # 10s PARA MINIATURA GIGANTE
                send_text_message(phone, r); time.sleep(2)
        else: send_text_message(phone, responses)

@app.route('/webhook', methods=['GET', 'POST'])
def handle_webhook():
    if request.method == 'GET':
        if request.args.get("hub.verify_token") == os.getenv('WHATSAPP_VERIFY_TOKEN'): return request.args.get("hub.challenge"), 200
        return 'Forbidden', 403
    body = request.get_json()
    try:
        if body.get('entry', [{}])[0].get('changes', [{}])[0].get('value', {}).get('messages'):
            msg_obj = body['entry'][0]['changes'][0]['value']['messages'][0]
            phone, text = msg_obj['from'], msg_obj.get('text', {}).get('body', '').strip()
            if text:
                user = get_user(phone); is_initial = (user["state"] == "new")
                if phone not in message_buffer:
                    message_buffer[phone] = [text]; threading.Thread(target=process_and_send, args=(phone, is_initial)).start()
                else: message_buffer[phone].append(text)
    except: pass
    return jsonify({"status": "ok"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)))
