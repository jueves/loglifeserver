# API de Logging Simple

API REST minimalista para registrar eventos con estructura clave-valor usando FastAPI y SQLite.

## Características

- 🚀 Ultra-minimalista (~48 líneas de código)
- 🔒 Autenticación mediante API key
- 💾 Base de datos SQLite embebida
- ⏱️ Timestamps automáticos
- 📊 Consulta últimos 100 registros

## Instalación

```bash
# Instalar dependencias
pip install -r requirements.txt
```

## Uso

### Ejecutar servidor

```bash
uvicorn main:app --reload
```

El servidor estará disponible en `http://localhost:8000`

### Guardar un evento

```bash
curl "http://localhost:8000/log?clave=temperatura&valor=25.5&key=mi-clave-secreta"
```

**Respuesta:**
```json
{"ok": true}
```

### Consultar logs

```bash
curl "http://localhost:8000/logs?key=mi-clave-secreta"
```

**Respuesta:**
```json
[
  {
    "id": 1,
    "clave": "temperatura",
    "valor": "25.5",
    "timestamp": "2025-12-19T10:35:00.123456"
  }
]
```

## Configuración

### Cambiar API Key

Edita el archivo `main.py` y modifica la constante:

```python
API_KEY = "tu-clave-secreta-aqui"
```

## Estructura de Base de Datos

```sql
CREATE TABLE eventos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    clave TEXT,
    valor TEXT,
    timestamp DATETIME
)
```

## Endpoints

### GET /log

Guarda un evento en la base de datos.

**Parámetros:**
- `clave` (string): Nombre del evento
- `valor` (string): Valor del evento
- `key` (string): API key para autenticación

**Respuesta:** `{"ok": true}`

### GET /logs

Obtiene los últimos 100 eventos ordenados por timestamp descendente.

**Parámetros:**
- `key` (string): API key para autenticación

**Respuesta:** Array de eventos con `id`, `clave`, `valor`, `timestamp`

## Notas

- La base de datos `eventos.db` se crea automáticamente al iniciar la aplicación
- Diseñado para volumen bajo (~7-10 registros/día)
- Sin dependencias complejas, ideal para aprendizaje e iteración
- SQLite es suficiente para este volumen de datos
