from fastapi import FastAPI, HTTPException
from datetime import datetime
import sqlite3

app = FastAPI()
API_KEY = "mi-clave-secreta"

# Inicializar base de datos
def init_db():
    conn = sqlite3.connect("eventos.db")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS eventos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            clave TEXT,
            valor TEXT,
            timestamp DATETIME
        )
    """)
    conn.commit()
    conn.close()

init_db()

def verify_key(key: str):
    if key != API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")

@app.get("/log")
def log_evento(clave: str, valor: str, key: str):
    verify_key(key)
    conn = sqlite3.connect("eventos.db")
    timestamp = datetime.now().isoformat()
    conn.execute("INSERT INTO eventos (clave, valor, timestamp) VALUES (?, ?, ?)",
                 (clave, valor, timestamp))
    conn.commit()
    conn.close()
    return {"ok": True}

@app.get("/logs")
def get_logs(key: str):
    verify_key(key)
    conn = sqlite3.connect("eventos.db")
    cursor = conn.execute(
        "SELECT id, clave, valor, timestamp FROM eventos ORDER BY timestamp DESC LIMIT 100"
    )
    logs = [{"id": row[0], "clave": row[1], "valor": row[2], "timestamp": row[3]}
            for row in cursor.fetchall()]
    conn.close()
    return logs
