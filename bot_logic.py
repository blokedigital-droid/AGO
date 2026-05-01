import sqlite3, json, datetime
from sheets_service import search_properties, format_property_response, format_property_list, filter_properties

DB_PATH = "/tmp/ago_v21.db"
OWNER_NUMBER = "573024929820"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("CREATE TABLE IF NOT EXISTS users (phone TEXT PRIMARY KEY, name TEXT, state TEXT, last_results TEXT, last_property TEXT, last_type_desc TEXT)")
    conn.execute("CREATE TABLE IF NOT EXISTS chat_history (id INTEGER PRIMARY KEY AUTOINCREMENT, phone TEXT, sender TEXT, message TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)")
    conn.commit(); conn.close()

init_db()

def save_chat(phone, sender, message):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("INSERT INTO chat_history (phone, sender, message) VALUES (?, ?, ?)", (phone, sender, str(message)))
    conn.commit(); conn.close()

def get_user(phone):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name, state, last_results, last_property, last_type_desc FROM users WHERE phone = ?", (phone,))
    row = cursor.fetchone(); conn.close()
    if row: return {"name": row[0], "state": row[1], "last_results": json.loads(row[2]) if row[2] else [], "last_property": row[3], "last_type_desc": row[4]}
    return {"name": None, "state": "new", "last_results": [], "last_property": None, "last_type_desc": None}

def update_user(phone, **kwargs):
    user = get_user(phone)
    for key, value in kwargs.items(): user[key] = value
    conn = sqlite3.connect(DB_PATH)
    conn.execute("INSERT OR REPLACE INTO users (phone, name, state, last_results, last_property, last_type_desc) VALUES (?, ?, ?, ?, ?, ?)", 
                 (phone, user["name"], user["state"], json.dumps(user["last_results"]), user["last_property"], user["last_type_desc"]))
    conn.commit(); conn.close()

def process_message(phone, message):
    save_chat(phone, "Cliente", message)
    user = get_user(phone)
    msg = message.lower().strip()
    
    # ... (Aquí va toda tu lógica de Saludo, Requisitos y Búsqueda que ya tenemos perfecta) ...
    # Por brevedad no la repito, pero asegúrate de que al final de process_message, guardes la respuesta:
    
    # respuesta = "Tu texto de respuesta"
    # save_chat(phone, "AGO", respuesta)
    # return respuesta
