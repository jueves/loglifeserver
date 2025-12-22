# Troubleshooting HTTPS

Esta guía ayuda a resolver problemas comunes con la configuración HTTPS.

## Problema: "Send failure: Tubería rota" al conectar con curl

### Síntomas
```bash
$ curl -k "https://localhost:3001/logs?key=algo"
curl: (35) Send failure: Tubería rota
```

### Causa
El contenedor Docker no está usando HTTPS, probablemente porque:
1. El contenedor no fue reconstruido después de actualizar `docker-compose.yml`
2. La imagen Docker no tiene `python-dotenv` instalado
3. Las variables SSL no están en el archivo `.env`

### Solución

#### Paso 1: Verificar diagnóstico automático
```bash
./check_https_docker.sh
```

Este script te dirá exactamente qué está mal.

#### Paso 2: Solución completa
```bash
# 1. Detener contenedor actual
docker-compose down

# 2. Asegurarse de que .env tiene las variables SSL
cat .env
# Debe contener:
# SSL_CERT_PATH=certs/cert.pem
# SSL_KEY_PATH=certs/key.pem

# Si no existe o está incompleto, créalo:
cat > .env << EOF
LOGLIFE_API_KEY=tu-clave-secreta
DB_PATH=data/events.db
PORT=3001
SSL_CERT_PATH=certs/cert.pem
SSL_KEY_PATH=certs/key.pem
EOF

# 3. Generar certificados si no existen
./generate_cert.sh

# 4. Reconstruir imagen Docker (importante!)
docker-compose build --no-cache

# 5. Iniciar contenedor
docker-compose up -d

# 6. Verificar logs
docker-compose logs api
# Deberías ver: 🔒 Iniciando servidor HTTPS en https://0.0.0.0:3001
```

#### Paso 3: Probar conexión
```bash
# Desde el host
curl -k "https://localhost:3001/logs?key=tu-api-key"

# Debe responder con: []
```

---

## Problema: Docker usa HTTP en lugar de HTTPS

### Síntomas
```bash
$ docker-compose logs api
api-1  | 🌐 Iniciando servidor HTTP en http://0.0.0.0:3001
```

### Causa
Las variables `SSL_CERT_PATH` y `SSL_KEY_PATH` no están siendo pasadas al contenedor.

### Solución
```bash
# 1. Verificar que .env existe y tiene las variables
cat .env | grep SSL

# 2. Verificar que docker-compose.yml NO tiene comentadas las variables SSL
cat docker-compose.yml | grep SSL
# Debe mostrar (sin #):
# - SSL_CERT_PATH=${SSL_CERT_PATH}
# - SSL_KEY_PATH=${SSL_KEY_PATH}

# 3. Si están comentadas, actualizarlas:
# Editar docker-compose.yml y asegurarse de que las líneas NO tengan # al inicio

# 4. Reiniciar contenedor
docker-compose down
docker-compose up -d
```

---

## Problema: Certificados no encontrados

### Síntomas
```bash
$ docker-compose logs api
Error: Certificado no encontrado en certs/cert.pem
```

### Causa
Los certificados SSL no existen en el directorio `certs/`.

### Solución
```bash
# Generar certificados
./generate_cert.sh

# Verificar que se crearon
ls -la certs/
# Debe mostrar:
# cert.pem
# key.pem

# Reiniciar contenedor
docker-compose restart api
```

---

## Problema: "python-dotenv not found"

### Síntomas
El servidor no lee las variables del archivo `.env`.

### Causa
La imagen Docker fue construida antes de agregar `python-dotenv` a `requirements.txt`.

### Solución
```bash
# Reconstruir imagen sin cache
docker-compose build --no-cache

# Reiniciar
docker-compose up -d

# Verificar que se instaló
docker-compose exec api pip list | grep dotenv
```

---

## Problema: Puerto equivocado (8000 en lugar de 3001)

### Síntomas
```bash
$ docker-compose logs api
Uvicorn running on http://0.0.0.0:8000
```

### Causa
La variable `PORT` no está siendo leída del archivo `.env`.

### Solución
```bash
# 1. Verificar que .env tiene PORT=3001
cat .env | grep PORT

# 2. Verificar docker-compose.yml
cat docker-compose.yml | grep PORT
# Debe mostrar:
# - PORT=${PORT:-3001}

# 3. Reconstruir
docker-compose down
docker-compose build
docker-compose up -d
```

---

## Verificación final exitosa

Cuando todo funciona correctamente, deberías ver:

```bash
$ ./check_https_docker.sh
🔍 Diagnóstico de configuración HTTPS con Docker
================================================

1. Verificando archivo .env...
   ✓ Archivo .env existe
   ✓ SSL_CERT_PATH configurado: certs/cert.pem
   ✓ SSL_KEY_PATH configurado: certs/key.pem

2. Verificando certificados...
   ✓ certs/cert.pem existe
   ✓ certs/key.pem existe

3. Verificando contenedores Docker...
   ✓ Contenedor 'api' está corriendo

4. Verificando logs del contenedor...
   ✓ Servidor iniciado con HTTPS
   🔒 Iniciando servidor HTTPS en https://0.0.0.0:3001

5. Verificando dependencias...
   ✓ python-dotenv está instalado en el contenedor
```

```bash
$ curl -k "https://localhost:3001/logs?key=algo"
[]
```

---

## Comando rápido para resetear todo

Si nada funciona, resetea completamente:

```bash
# Detener y eliminar todo
docker-compose down -v

# Eliminar imagen
docker rmi loglifeserver-api 2>/dev/null || true

# Generar certificados frescos
rm -rf certs/
./generate_cert.sh

# Crear .env fresco
cat > .env << 'EOF'
LOGLIFE_API_KEY=mi-clave-secreta
DB_PATH=data/events.db
PORT=3001
SSL_CERT_PATH=certs/cert.pem
SSL_KEY_PATH=certs/key.pem
EOF

# Reconstruir todo desde cero
docker-compose build --no-cache
docker-compose up -d

# Esperar 3 segundos
sleep 3

# Verificar
docker-compose logs api
curl -k "https://localhost:3001/logs?key=mi-clave-secreta"
```
