import sqlite3
from sheets_service import search_properties, format_property_response, format_property_list

DB_PATH = "ago_memory.db"
OWNER_NUMBER = "573024929820"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("CREATE TABLE IF NOT EXISTS users (phone TEXT PRIMARY KEY, name TEXT, state TEXT)")
    conn.commit()
    conn.close()

init_db()

def get_user(phone):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name, state FROM users WHERE phone = ?", (phone,))
    row = cursor.fetchone()
    conn.close()
    return {"name": row[0], "state": row[1]} if row else {"name": None, "state": "new"}

def update_user(phone, name=None, state=None):
    user = get_user(phone)
    new_name = name if name else user["name"]
    new_state = state if state else user["state"]
    conn = sqlite3.connect(DB_PATH)
    conn.execute("INSERT OR REPLACE INTO users (phone, name, state) VALUES (?, ?, ?)", (phone, new_name, new_state))
    conn.commit()
    conn.close()

def process_message(phone, message):
    user = get_user(phone)
    msg = message.lower().strip()
    
    if user["state"] == "new":
        update_user(phone, state="awaiting_name")
        return "¡Hola! Soy *AGO*, te voy a ayudar a encontrar tu próximo hogar! 🏠✨\n\n¿Con quién tengo el gusto de hablar? 😊"

    if user["state"] == "awaiting_name":
        name = message.strip().title()
        update_user(phone, name=name, state="ready")
        return f"¡Un placer, *{name}*! 🤝 ¿Qué buscas hoy? \n\n1. *Apartamentos*\n2. *Apartaestudios*\n3. *Opciones en Cali*\n4. *Opciones en Jamundí*"

    name = user["name"]
    
    # Intenciones de Cierre
    if any(k in msg for k in ['asesor', 'persona', 'humano', 'hablar']):
        link = f"https://wa.me/{OWNER_NUMBER}?text=Hola,%20soy%20{name}%20y%20quiero%20más%20información."
        return f"¡Entendido, *{name}*! 📱 Haz clic aquí para hablar con un asesor humano:\n👉 {link}"

    # Búsqueda
    results = search_properties(msg)
    if len(results) == 1:
        return format_property_response(results[0], name)
    elif len(results) > 1:
        return format_property_list(results, name, "en esa zona")

    return f"*{name}*, cuéntame qué buscas o escribe *'asesor'* para hablar con una persona. 🏠"
