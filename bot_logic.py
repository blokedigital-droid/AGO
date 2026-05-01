import sqlite3, json, datetime
from sheets_service import search_properties, format_property_response, format_property_list, filter_properties

DB_PATH = "/tmp/ago_v21.db"
OWNER_NUMBER = "573024929820"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("CREATE TABLE IF NOT EXISTS users (phone TEXT PRIMARY KEY, name TEXT, state TEXT, last_results TEXT, last_property TEXT, last_type_desc TEXT)")
    conn.execute("CREATE TABLE IF NOT EXISTS chat_history (id INTEGER PRIMARY KEY AUTOINCREMENT, phone TEXT, sender TEXT, message TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)")
    conn.commit()
    conn.close()

init_db()

def save_chat(phone, sender, message):
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute("INSERT INTO chat_history (phone, sender, message) VALUES (?, ?, ?)", (phone, sender, str(message)))
        conn.commit()
        conn.close()
    except: pass

def get_user(phone):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name, state, last_results, last_property, last_type_desc FROM users WHERE phone = ?", (phone,))
    row = cursor.fetchone()
    conn.close()
    if row: return {"name": row[0], "state": row[1], "last_results": json.loads(row[2]) if row[2] else [], "last_property": row[3], "last_type_desc": row[4]}
    return {"name": None, "state": "new", "last_results": [], "last_property": None, "last_type_desc": None}

def update_user(phone, **kwargs):
    user = get_user(phone)
    for key, value in kwargs.items(): user[key] = value
    conn = sqlite3.connect(DB_PATH)
    conn.execute("INSERT OR REPLACE INTO users (phone, name, state, last_results, last_property, last_type_desc) VALUES (?, ?, ?, ?, ?, ?)", 
                 (phone, user["name"], user["state"], json.dumps(user["last_results"]), user["last_property"], user["last_type_desc"]))
    conn.commit()
    conn.close()

def process_message(phone, message):
    save_chat(phone, "Cliente", message)
    user = get_user(phone)
    msg = message.lower().strip()
    response = ""
    
    # 1. Registro de Nombre
    if user["state"] == "new":
        update_user(phone, state="awaiting_name")
        response = "¡Hola! Soy *AGO*, te voy a ayudar a encontrar tu próximo hogar! 🏠✨\n\n¿Con quién tengo el gusto de hablar? 😊"
    
    elif user["state"] == "awaiting_name":
        name = message.strip().title()
        update_user(phone, name=name, state="ready")
        response = f"¡Un placer, *{name}*! 🤝 ¿Qué buscas hoy? \n\n1. *Apartamentos*\n2. *Apartaestudios*\n3. *Opciones en Cali*\n4. *Opciones en Jamundí*"
    
    else:
        name = user["name"] or "Amigo"
        
        # 2. REQUISITOS (DIFERENCIADOS)
        if any(k in msg for k in ['requisito', 'papeles', 'necesito', 'documento']):
            type_desc = (user["last_type_desc"] or "").lower()
            if "estudio" in type_desc or "aparta" in msg:
                response = f"✅ *Requisitos para Apartaestudio (Proceso Directo):*\n\n1️⃣ Cédula al 150%.\n2️⃣ Extractos bancarios (3 meses) o Carta Laboral.\n3️⃣ Referencias (1 Familiar y 1 Personal).\n4️⃣ Depósito de servicios: $150.000.\n\n⚠️ *Nota:* Primero verificamos documentos, luego firmamos contrato. *{name}*, puedes enviarlos por aquí. 📝"
            else:
                papeleo = f"✅ *Requisitos para Apartamentos:*\n- Cédula al 150%.\n- Carta Laboral y Extractos (3 meses).\n- Codeudor solvente con la misma documentación."
                tramite = f"📄 *¡Aplica ahora mismo!*\n\nRealiza el estudio con **El Libertador** aquí:\n👉 https://www.ellibertador.co/\n\n🏢 *Datos:* 16004 | AGO GRUPO INMOBILIARIO | Asesor: Diego Ramirez | notificaciones@agoinmo.com"
                response = [papeleo, tramite]

        # 3. DESPEDIDA
        elif any(k in msg for k in ['gracias', 'ya agende', 'adiós', 'listo']):
            response = f"¡Con todo el gusto, *{name}*! 😊 ¡Que tengas un excelente día! 🏠✨"

        # 4. REDIRECCIÓN
        elif any(k in msg for k in ['asesor', 'persona', 'humano', 'hablar']):
            desc = user["last_type_desc"] or "un inmueble"
            text = f"Hola, soy {name}. Interesado en {desc} y quiero hablar con un asesor."
            link = f"https://wa.me/573024929820?text={text.replace(' ', '%20')}"
            response = f"¡Claro, *{name}*! 📱 Haz clic aquí para hablar directamente con Diego Ramirez:\n👉 {link}"

        # 5. BÚSQUEDA Y MENÚS
        elif msg.isdigit():
            val = int(msg)
            if user["last_results"] and 1 <= val <= len(user["last_results"]):
                selected = user["last_results"][val-1]
                update_user(phone, last_results=[], last_property=selected.get('ID'), last_type_desc=selected.get('Tipo'))
                response = format_property_response(selected, name)
            elif val == 1: response = process_message(phone, "apartamento")
            elif val == 2: response = process_message(phone, "apartaestudio")
            elif val == 3: response = process_message(phone, "cali")
            elif val == 4: response = process_message(phone, "jamundi")
            else: response = f"*{name}*, por favor elige un número válido. 😊"

        else:
            results = filter_properties(msg) if len(msg.split()) < 3 else []
            if not results: results = search_properties(msg)
            if len(results) == 1:
                update_user(phone, last_results=[], last_property=results[0].get('ID'), last_type_desc=results[0].get('Tipo'))
                response = format_property_response(results[0], name)
            elif len(results) > 1:
                update_user(phone, last_results=results)
                response = format_property_list(results, name, "que coinciden")
            else:
                response = f"*{name}*, no logré encontrar algo exacto. ¿Buscas apartamentos o apartaestudios? 🏠"

    if isinstance(response, list):
        for r in response: save_chat(phone, "AGO", r)
    else:
        save_chat(phone, "AGO", response)
    return response
