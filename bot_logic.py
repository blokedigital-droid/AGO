import sqlite3, json, datetime, time
from sheets_service import search_properties, format_property_response, format_property_list, filter_properties, fetch_all_properties

# RUTA DEFINITIVA PARA MEMORIA ETERNA
DB_PATH = "/app/data/ago_business_main.db"
OWNER_NUMBER = "573024929820"

def get_db(): return sqlite3.connect(DB_PATH, timeout=30)

def init_db():
    conn = get_db()
    conn.execute("CREATE TABLE IF NOT EXISTS users (phone TEXT PRIMARY KEY, name TEXT, state TEXT, last_results TEXT, last_property_id TEXT, last_type_desc TEXT, last_interaction TIMESTAMP)")
    conn.execute("CREATE TABLE IF NOT EXISTS chat_history (id INTEGER PRIMARY KEY AUTOINCREMENT, phone TEXT, sender TEXT, message TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)")
    conn.commit(); conn.close()

init_db()

def save_chat(phone, sender, message):
    try:
        conn = get_db()
        conn.execute("INSERT INTO chat_history (phone, sender, message) VALUES (?, ?, ?)", (phone, sender, str(message)))
        conn.commit(); conn.close()
    except: pass

def get_user(phone):
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT name, state, last_results, last_property_id, last_type_desc, last_interaction FROM users WHERE phone = ?", (phone,))
        row = cursor.fetchone(); conn.close()
        if row: return {"name": row[0], "state": row[1], "last_results": json.loads(row[2]) if row[2] else [], "last_property_id": row[3], "last_type_desc": row[4], "last_interaction": row[5]}
    except: pass
    return {"name": None, "state": "new", "last_results": [], "last_property_id": None, "last_type_desc": None, "last_interaction": None}

def update_user(phone, **kwargs):
    user = get_user(phone)
    for key, value in kwargs.items(): user[key] = value
    try:
        conn = get_db()
        conn.execute("INSERT OR REPLACE INTO users (phone, name, state, last_results, last_property_id, last_type_desc, last_interaction) VALUES (?, ?, ?, ?, ?, ?, ?)", 
                     (phone, user["name"], user["state"], json.dumps(user["last_results"]), user["last_property_id"], user["last_type_desc"], datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')))
        conn.commit(); conn.close()
    except: pass

def process_message(phone, message):
    save_chat(phone, "Cliente", message)
    user = get_user(phone)
    msg = message.lower().strip()
    res = ""

    # 1. RE-BIENVENIDA (40 MINUTOS)
    if user["last_interaction"] and user["state"] == "ready":
        last_time = datetime.datetime.strptime(user["last_interaction"], '%Y-%m-%d %H:%M:%S')
        diff = (datetime.datetime.utcnow() - last_time).total_seconds() / 60
        if diff > 40 and user["name"]:
            update_user(phone)
            res = f"¡Hola de nuevo, *{user['name']}*! 😊 Me alegra que vuelvas. ¿En qué te puedo ayudar ahora?\n\n1. *Apartamentos*\n2. *Apartaestudios*\n3. *Casas*\n4. *Cali*\n5. *Jamundí*"
            save_chat(phone, "AGO", res)
            return res

    # 2. BIENVENIDA INICIAL
    if user["state"] == "new" or not user["name"]:
        extracted = extract_name(message)
        if extracted:
            update_user(phone, name=extracted, state="ready")
            res = [f"¡Hola! Soy *AGO*, tu asistente personal. 🏠✨", f"¡Qué buen nombre, *{extracted}*! 🥳 Te ayudaré a encontrar tu próximo hogar hoy mismo. ¿Qué buscas hoy?", "1. *Apartamentos*\n2. *Apartaestudios*\n3. *Casas*\n4. *Cali*\n5. *Jamundí*"]
        else:
            update_user(phone, state="awaiting_name")
            res = "¡Hola! Soy *AGO*, te voy a ayudar a encontrar tu próximo hogar! 🏠✨\n\n¿Con quién tengo el gusto de hablar hoy? 😊"
    
    elif user["state"] == "awaiting_name":
        name = extract_name(message) or message.strip().title()
        if len(name.split()) > 2: name = name.split()[0]
        update_user(phone, name=name, state="ready")
        res = f"¡Un placer saludarte, *{name}*! 🤝 Ya tengo todo listo. ¿Qué buscas hoy? \n\n1. *Apartamentos*\n2. *Apartaestudios*\n3. *Casas*\n4. *Cali*\n5. *Jamundí*"
    
    else:
        name = user["name"] or "Amigo"
        # REQUISITOS
        if any(k in msg for k in ['requisito', 'papeles', 'necesito', 'documento', 'que piden']):
            props = fetch_all_properties(); target = None
            if user["last_property_id"]:
                for p in props:
                    if p.get('ID') == user["last_property_id"]: target = p; break
            if target:
                reqs = target.get('Requisitos', '').strip() or "Escríbeme para darte los requisitos exactos. 😊"
                res = [f"📋 *Requisitos para:* {target.get('Tipo','Inmueble')} ({target.get('ID','')})", reqs]
                if "apartaestudio" not in target.get('Tipo','').lower():
                    res.append(f"📄 *Estudio El Libertador:* https://www.ellibertador.co/\n🏢 *Datos:* 16004 | Asesor: Diego Ramirez | notificaciones@agoinmo.com")
            else: res = f"*{name}*, dime el código del inmueble para darte los requisitos exactos. 🏠"
        elif any(k in msg for k in ['gracias', 'ya agende', 'adiós', 'listo', 'chau']) and len(msg.split()) < 5:
            res = f"¡Con todo el gusto, *{name}*! 😊 ¡Que tengas un día maravilloso! 🏠✨"
        elif any(k in msg for k in ['asesor', 'persona', 'humano', 'hablar']):
            text = f"Hola, soy {name}. Interesado en {user['last_type_desc'] or 'un inmueble'}"
            link = f"https://wa.me/573024929820?text={text.replace(' ', '%20')}"
            res = f"¡Excelente decisión, *{name}*! 📱 Te paso con Diego Ramirez para cerrar los detalles:\n👉 {link}"
        elif msg.isdigit():
            val = int(msg)
            if user["last_results"] and 1 <= val <= len(user["last_results"]):
                selected = user["last_results"][val-1]
                update_user(phone, last_results=[], last_property_id=selected.get('ID'), last_type_desc=selected.get('Tipo'))
                res = handle_property_response(selected, name)
            elif val == 1: return process_message(phone, "apartamento")
            elif val == 2: return process_message(phone, "apartaestudio")
            elif val == 3: return process_message(phone, "casa")
            elif val == 4: return process_message(phone, "cali")
            elif val == 5: return process_message(phone, "jamundi")
        else:
            results = filter_properties(msg) if len(msg.split()) < 3 else []
            if not results: results = search_properties(msg)
            if len(results) == 1:
                update_user(phone, last_results=[], last_property_id=results[0].get('ID'), last_type_desc=results[0].get('Tipo'))
                res = handle_property_response(results[0], name)
            elif len(results) > 1:
                update_user(phone, last_results=results); res = format_property_list(results, name, "que coinciden")
            else: res = f"¡Ups, *{name}*! 🔍 No encontré algo exacto. ¿Buscas apartamentos o apartaestudios? 🏠"

    update_user(phone)
    if isinstance(res, list):
        for r in res: save_chat(phone, "AGO", r)
    else: save_chat(phone, "AGO", res)
    return res

def handle_property_response(prop, name):
    from sheets_service import format_property_response
    main_text = format_property_response(prop, name)
    video_url = prop.get('Link_Video', '').strip()
    if video_url:
        video_msg = f"🎥 *¡Mira este recorrido increíble!* Te vas a enamorar. Dale clic aquí: 👇\n\n{video_url}"
        return [main_text, video_msg]
    return main_text

def extract_name(text):
    text = text.lower().strip(); phrases = ['soy ', 'me llamo ', 'mi nombre es ']
    for p in phrases:
        if p in text:
            parts = text.split(p); return parts[1].split()[0].title() if len(parts) > 1 else None
    return None
