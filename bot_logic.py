import sqlite3, json, datetime, time
from sheets_service import search_properties, format_property_response, format_property_list, filter_properties, fetch_all_properties

DB_PATH = "/app/data/ago_database_final.db"
OWNER_NUMBER = "573024929820"

def get_db():
    conn = sqlite3.connect(DB_PATH, timeout=30); conn.row_factory = sqlite3.Row; return conn

def init_db():
    conn = get_db()
    conn.execute("CREATE TABLE IF NOT EXISTS users (phone TEXT PRIMARY KEY, name TEXT, state TEXT, last_results TEXT, last_property_id TEXT, last_type_desc TEXT, last_interaction TIMESTAMP)")
    conn.execute("CREATE TABLE IF NOT EXISTS chat_history (id INTEGER PRIMARY KEY AUTOINCREMENT, phone TEXT, sender TEXT, message TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)")
    conn.commit(); conn.close()

init_db()

def save_chat(phone, sender, message):
    try:
        conn = get_db(); conn.execute("INSERT INTO chat_history (phone, sender, message) VALUES (?, ?, ?)", (phone, sender, str(message)))
        conn.commit(); conn.close()
    except: pass

def get_user(phone):
    try:
        conn = get_db(); row = conn.execute("SELECT * FROM users WHERE phone = ?", (phone,)).fetchone(); conn.close()
        if row: return dict(row)
    except: pass
    return {"name": None, "state": "new", "last_results": "[]", "last_property_id": None, "last_type_desc": None, "last_interaction": None}

def update_user(phone, **kwargs):
    user = get_user(phone)
    for key, value in kwargs.items(): user[key] = value
    if isinstance(user.get("last_results"), list): user["last_results"] = json.dumps(user["last_results"])
    try:
        conn = get_db(); conn.execute("INSERT OR REPLACE INTO users (phone, name, state, last_results, last_property_id, last_type_desc, last_interaction) VALUES (?, ?, ?, ?, ?, ?, ?)", 
            (phone, user["name"], user["state"], user["last_results"], user["last_property_id"], user["last_type_desc"], datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')))
        conn.commit(); conn.close()
    except: pass

def process_message(phone, message):
    save_chat(phone, "Cliente", message); user = get_user(phone); msg = message.lower().strip()
    
    if user["state"] == "new":
        name = extract_name(message)
        has_intent = any(k in msg for k in ['apartamento', 'apto', 'estudio', 'casa', 'cali', 'jamundi'])
        if name:
            update_user(phone, name=name, state="ready")
            welcome = [f"¡Hola! Soy *AGO*, tu asistente personal. 🏠✨", f"¡Qué buen nombre, *{name}*! 🥳 Te ayudaré a encontrar tu hogar hoy mismo."]
            if has_intent: return welcome + [handle_search(message, name, phone)]
            return welcome + ["¿Qué buscas hoy? \n\n1. *Apartamentos*\n2. *Apartaestudios*\n3. *Casas*\n4. *Cali*\n5. *Jamundí*"]
        update_user(phone, state="awaiting_name")
        return "¡Hola! Soy *AGO*, te voy a ayudar a encontrar tu próximo hogar! 🏠✨\n\n¿Con quién tengo el gusto de hablar hoy? 😊"

    if user["state"] == "awaiting_name":
        name = extract_name(message) or message.strip().title()
        if len(name.split()) > 2: name = name.split()[0]
        update_user(phone, name=name, state="ready")
        return f"¡Un placer, *{name}*! 🤝 Ya tengo todo listo. ¿Qué buscas hoy? \n\n1. *Apartamentos*\n2. *Apartaestudios*\n3. *Casas*\n4. *Cali*\n5. *Jamundí*"

    name = user["name"] or "Amigo"
    if any(k in msg for k in ['requisito', 'papeles', 'necesito', 'documento']):
        props = fetch_all_properties(); target = None
        if user["last_property_id"]:
            for p in props:
                if p.get('ID') == user["last_property_id"]: target = p; break
        if not target:
            matches = search_properties(msg)
            if matches: target = matches[0]
        if target:
            res = [f"📋 *Requisitos para:* {target.get('Tipo','Inmueble')} ({target.get('ID','')})", target.get('Requisitos', 'Contáctame para detalles. 😊')]
            if "apartaestudio" not in target.get('Tipo','').lower(): res.append(f"📄 *Estudio El Libertador:* https://www.ellibertador.co/\n🏢 *Datos:* 16004 | Asesor: Diego Ramirez | notificaciones@agoinmo.com")
            return handle_and_save(phone, res)
        return handle_and_save(phone, f"*{name}*, dime el código del inmueble para darte los requisitos exactos. 🏠")

    if any(k in msg for k in ['gracias', 'ya agende', 'adiós', 'listo']) and len(msg.split()) < 5:
        return handle_and_save(phone, f"¡Con todo el gusto, *{name}*! 😊 ¡Que tengas un día maravilloso! 🏠✨")

    if any(k in msg for k in ['asesor', 'persona', 'humano']):
        text = f"Hola, soy {name}. Interesado en {user['last_type_desc'] or 'un inmueble'}"
        link = f"https://wa.me/573024929820?text={text.replace(' ', '%20')}"
        return handle_and_save(phone, f"¡Excelente decisión, *{name}*! 📱 Te paso con Diego Ramirez:\n👉 {link}")

    if msg.isdigit():
        val = int(msg); results_list = json.loads(user["last_results"])
        if results_list and 1 <= val <= len(results_list):
            selected = results_list[val-1]; update_user(phone, last_results="[]", last_property_id=selected.get('ID'), last_type_desc=selected.get('Tipo'))
            return handle_and_save(phone, handle_property_response(selected, name))
        if val == 1: return handle_search("apartamento", name, phone)
        if val == 2: return handle_search("apartaestudio", name, phone)
        if val == 3: return handle_search("casa", name, phone)
        if val == 4: return handle_search("cali", name, phone)
        if val == 5: return handle_search("jamundi", name, phone)

    return handle_and_save(phone, handle_search(msg, name, phone))

def handle_search(query, name, phone):
    results = filter_properties(query) if len(query.split()) < 3 else []
    if not results: results = search_properties(query)
    if len(results) == 1:
        update_user(phone, last_results="[]", last_property_id=results[0].get('ID'), last_type_desc=results[0].get('Tipo'))
        return handle_property_response(results[0], name)
    elif len(results) > 1:
        update_user(phone, last_results=json.dumps(results)); return format_property_list(results, name, "que coinciden")
    return f"¡Ups, *{name}*! 🔍 No encontré algo exacto. ¿Buscas apartamentos, casas o apartaestudios? 🏠"

def handle_and_save(phone, response):
    if isinstance(response, list):
        for r in response: save_chat(phone, "AGO", r)
    else: save_chat(phone, "AGO", response)
    return response

def handle_property_response(prop, name):
    from sheets_service import format_property_response
    main_text = format_property_response(prop, name)
    video_url = prop.get('Link_Video', '').strip()
    if video_url: return [main_text, f"🎥 *¡Mira el video del inmueble aquí!* 👇\n{video_url}"]
    return main_text

def extract_name(text):
    text = text.lower().strip(); phrases = ['soy ', 'me llamo ', 'mi nombre es ', 'habla ']
    for p in phrases:
        if p in text:
            parts = text.split(p); return parts[1].split()[0].title() if len(parts) > 1 else None
    return None
