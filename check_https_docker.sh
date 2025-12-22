#!/bin/bash
# Script para diagnosticar problemas de HTTPS con Docker

echo "🔍 Diagnóstico de configuración HTTPS con Docker"
echo "================================================"
echo ""

# Check 1: .env file exists and has SSL variables
echo "1. Verificando archivo .env..."
if [ -f .env ]; then
    echo "   ✓ Archivo .env existe"

    if grep -q "^SSL_CERT_PATH=" .env 2>/dev/null; then
        SSL_CERT=$(grep "^SSL_CERT_PATH=" .env | cut -d= -f2)
        echo "   ✓ SSL_CERT_PATH configurado: $SSL_CERT"
    else
        echo "   ✗ SSL_CERT_PATH no encontrado en .env"
    fi

    if grep -q "^SSL_KEY_PATH=" .env 2>/dev/null; then
        SSL_KEY=$(grep "^SSL_KEY_PATH=" .env | cut -d= -f2)
        echo "   ✓ SSL_KEY_PATH configurado: $SSL_KEY"
    else
        echo "   ✗ SSL_KEY_PATH no encontrado en .env"
    fi
else
    echo "   ✗ Archivo .env no encontrado"
    echo ""
    echo "   Crea el archivo .env con:"
    echo "   cat > .env << EOF"
    echo "   LOGLIFE_API_KEY=tu-clave"
    echo "   DB_PATH=data/events.db"
    echo "   PORT=3001"
    echo "   SSL_CERT_PATH=certs/cert.pem"
    echo "   SSL_KEY_PATH=certs/key.pem"
    echo "   EOF"
fi

echo ""

# Check 2: Certificate files exist
echo "2. Verificando certificados..."
if [ -f "certs/cert.pem" ]; then
    echo "   ✓ certs/cert.pem existe"
else
    echo "   ✗ certs/cert.pem no encontrado"
    echo "     Ejecuta: ./generate_cert.sh"
fi

if [ -f "certs/key.pem" ]; then
    echo "   ✓ certs/key.pem existe"
else
    echo "   ✗ certs/key.pem no encontrado"
    echo "     Ejecuta: ./generate_cert.sh"
fi

echo ""

# Check 3: Docker container status
echo "3. Verificando contenedores Docker..."
if command -v docker &> /dev/null; then
    container_id=$(docker ps -q -f "name=api")

    if [ -n "$container_id" ]; then
        echo "   ✓ Contenedor 'api' está corriendo (ID: $container_id)"

        # Check container logs for HTTPS message
        echo ""
        echo "4. Verificando logs del contenedor..."
        if docker logs $container_id 2>&1 | grep -q "Iniciando servidor HTTPS"; then
            echo "   ✓ Servidor iniciado con HTTPS"
            docker logs $container_id 2>&1 | grep "Iniciando servidor" | tail -1
        elif docker logs $container_id 2>&1 | grep -q "Iniciando servidor HTTP"; then
            echo "   ✗ Servidor iniciado con HTTP (no HTTPS)"
            docker logs $container_id 2>&1 | grep "Iniciando servidor" | tail -1
            echo ""
            echo "   Solución:"
            echo "   1. Verifica que .env tenga SSL_CERT_PATH y SSL_KEY_PATH"
            echo "   2. Ejecuta: docker-compose down"
            echo "   3. Ejecuta: docker-compose build"
            echo "   4. Ejecuta: docker-compose up -d"
        else
            echo "   ⚠ No se pudo determinar el modo del servidor"
            echo "   Últimas 10 líneas de logs:"
            docker logs $container_id 2>&1 | tail -10
        fi

        # Check if python-dotenv is installed
        echo ""
        echo "5. Verificando dependencias..."
        if docker exec $container_id pip list 2>/dev/null | grep -q "python-dotenv"; then
            echo "   ✓ python-dotenv está instalado en el contenedor"
        else
            echo "   ✗ python-dotenv NO está instalado en el contenedor"
            echo "     Ejecuta: docker-compose build --no-cache"
        fi

    else
        echo "   ✗ No hay contenedor 'api' corriendo"
        echo ""
        echo "   Inicia el contenedor con:"
        echo "   docker-compose up -d"
    fi
else
    echo "   ✗ Docker no está instalado o no es accesible"
fi

echo ""
echo "================================================"
echo ""

# Provide recommendations
echo "📋 Pasos recomendados para activar HTTPS:"
echo ""
echo "1. Asegúrate de tener los certificados:"
echo "   ./generate_cert.sh"
echo ""
echo "2. Verifica tu archivo .env:"
echo "   cat .env"
echo "   # Debe contener:"
echo "   # SSL_CERT_PATH=certs/cert.pem"
echo "   # SSL_KEY_PATH=certs/key.pem"
echo ""
echo "3. Reconstruye el contenedor Docker:"
echo "   docker-compose down"
echo "   docker-compose build"
echo "   docker-compose up -d"
echo ""
echo "4. Verifica los logs:"
echo "   docker-compose logs api"
echo "   # Deberías ver: 🔒 Iniciando servidor HTTPS en https://0.0.0.0:3001"
echo ""
echo "5. Prueba la conexión:"
echo "   curl -k https://localhost:3001/logs?key=tu-api-key"
echo ""
