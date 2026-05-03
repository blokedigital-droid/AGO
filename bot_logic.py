import sqlite3, json, datetime
from sheets_service import search_properties, format_property_response, format_property_list, filter_properties, fetch_all_properties

DB_PATH = "/tmp/ago_v25.db" # Cambiamos de DB para inicio limpio
OWNER_NUMBER = "573024929820"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("CREATE TABLE IF NOT EXISTS users (phone TEXT PRIMARY KEY, name TEXT, state TEXT, last_results TEXT, last_property_id TEXT, last_type_desc TEXT)")
    conn.execute("CREATE TABLE IF NOT EXISTS chat_history (id INTEGER PRIMARY KEY AUTOINCREMENT, phone TEXT, sender TEXT, message TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)")
    conn.commit(); conn.close()

init_db()

def save_chat(phone, sender, message):
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute("INSERT INTO chat_history (phone, sender, message) VALUES (?, ?, ?)", (phone, sender, str(message)))
        conn.commit(); conn.close()
    except: pass

def get_user(phone):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name, state, last_results, last_property_id, last_type_desc FROM users WHERE phone = ?", (phone,))
    row = cursor.fetchone(); conn.close()
    if row: return {"name": row[0], "state": row[1], "last_results": json.loads(row[2]) if row[2] else [], "last_property_id": row[3], "last_type_desc": row[4]}
    return {"name": None, "state": "new", "last_results": [], "last_property_id": None, "last_type_desc": None}

def update_user(phone, **kwargs):
    user = get_user(phone)
    for key, value in kwargs.items(): user[key] = value
    conn = sqlite3.connect(DB_PATH)
    conn.execute("INSERT OR REPLACE INTO users (phone, name, state, last_results, last_property_id, last_type_desc) VALUES (?, ?, ?, ?, ?, ?)", 
                 (phone, user["name"], user["state"], json.dumps(user["last_results"]), user["last_property_id"], user["last_type_desc"]))
    conn.commit(); conn.close()

def process_message(phone, message):
    save_chat(phone, "Cliente", message)
    user = get_user(phone)
    msg = message.lower().strip()
    res = ""

    # --- 1. DETECCIÓN DE NOMBRE (CORREGIDO EL BUCLE) ---
    if user["state"] == "new":
        name = extract_name(message)
        if name:
            update_user(phone, name=name, state="ready")
            return [f"¡Hola! Soy *AGO*, tu asistente del Grupo Inmobiliario. 🏠✨", f"¡Qué buen nombre, *{name}*! 🥳 Te ayudaré a encontrar tu hogar ideal hoy mismo.", "¿Qué buscas hoy? \n\n1. *Apartamentos*\n2. *Apartaestudios*\n3. *En Cali*\n4. *En Jamundí*"]
        update_user(phone, state="awaiting_name")
        return "¡Hola! Soy *AGO*, te voy a ayudar a encontrar tu próximo hogar! 🏠✨\n\n¿Con quién tengo el gusto de hablar hoy? 😊"
    
    if user["state"] == "awaiting_name":
        name = extract_name(message) or message.strip().title()
        update_user(phone, name=name, state="ready")
        return f"¡Un placer saludarte, *{name}*! 🤝 Ya tengo todo listo. ¿Qué buscas hoy? \n\n1. *Apartamentos*\n2. *Apartaestudios*\n3. *En Cali*\n4. *En Jamundí*"

    name = user["name"] or "Amigo"

    # --- 2. REQUISITOS (ESPECÍFICOS DEL EXCEL) ---
    if any(k in msg for k in ['requisito', 'papeles', 'necesito', 'documento', 'que piden']):
        props = fetch_all_properties(); target = None
        if user["last_property_id"]:
            for p in props:
                if p.get('ID') == user["last_property_id"]: target = p; break
        if not target:
            matches = search_properties(msg)
            if matches: target = matches[0]
        
        if target:
            reqs = target.get('Requisitos', '').strip() or "Por favor contáctame para los detalles exactos. 😊"
            res = [f"📋 *Requisitos para:* {target.get('Tipo','Inmueble')} ({target.get('ID','')})", reqs]
            if "apartaestudio" not in target.get('Tipo','').lower():
                res.append(f"📄 *Estudio El Libertador:* https://www.ellibertador.co/\n🏢 *Datos:* 16004 | Asesor: Diego Ramirez | notificaciones@agoinmo.com")
            return handle_and_save(phone, res)
        return handle_and_save(phone, f"*{name}*, dime el código o nombre del inmueble que te interesa para darte los requisitos exactos. 🏠")

    # --- 3. CORTESÍA Y DESPEDIDA ---
    if any(k in msg for k in ['gracias', 'ya agende', 'adiós', 'listo', 'chau']) and len(msg.split()) < 6:
        return handle_and_save(phone, f"¡Con todo el gusto, *{name}*! 😊 ¡Que tengas un día maravilloso! 🏠✨")

    # --- 4. REDIRECCIÓN ASESOR ---
    if any(k in msg for k in ['asesor', 'persona', 'humano', 'hablar']):
        text = f"Hola, soy {name}. Interesado en {user['last_type_desc'] or 'un inmueble'}"
        link = f"https://wa.me/573024929820?text={text.replace(' ', '%20')}"
        return handle_and_save(phone, f"¡Excelente decisión, *{name}*! 📱 Te paso con Diego Ramirez para cerrar los detalles. Haz clic aquí:\n👉 {link}")

    # --- 5. BÚSQUEDA Y MENÚS ---
    if msg.isdigit():
        val = int(msg)
        if user["last_results"] and 1 <= val <= len(user["last_results"]):
            selected = user["last_results"][val-1]
            update_user(phone, last_results=[], last_property_id=selected.get('ID'), last_type_desc=selected.get('Tipo'))
            return handle_and_save(phone, handle_property_response(selected, name))
        if val == 1: return process_message(phone, "apartamento")
        if val == 2: return process_message(phone, "apartaestudio")
        if val == 3: return process_message(phone, "cali")
        if val == 4: return process_message(phone, "jamundi")

    results = filter_properties(msg) if len(msg.split()) < 3 else []
    if not results: results = search_properties(msg)
    
    if len(results) == 1:
        update_user(phone, last_results=[], last_property_id=results[0].get('ID'), last_type_desc=results[0].get('Tipo'))
        return handle_and_save(phone, handle_property_response(results[0], name))
    elif len(results) > 1:
        update_user(phone, last_results=results)
        return handle_and_save(phone, format_property_list(results, name, "que coinciden"))

    return handle_and_save(phone, f"¡Ups, *{name}*! 🔍 No encontré algo exacto. ¿Buscas apartamentos o apartaestudios? 🏠")

def handle_and_save(phone, response):
    if isinstance(response, list):
        for r in response: save_chat(phone, "AGO", r)
    else: save_chat(phone, "AGO", response)
    return response

def handle_property_response(prop, name):
    main_text = format_property_response(prop, name)
    video_url = prop.get('Link_Video', '').strip()
    if video_url: return [main_text, f"🎥 *¡Mira el video del inmueble aquí!* 👇\n{video_url}"]
    return main_text

def extract_name(text):
    text = text.lower().strip()
    phrases = ['soy ', 'me llamo ', 'mi nombre es ']
    for p in phrases:
        if p in text:
            parts = text.split(p)
            if len(parts) > 1: return parts[1].split()[0].title()
    return None
