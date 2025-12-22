# Instalar certificado SSL en clientes (Opcional)

Esta guía es **opcional**. El script `./loglife` ya funciona con certificados autofirmados usando el flag `-k`.

## ¿Cuándo usar esto?

- Quieres evitar advertencias de SSL en clientes
- Quieres validación SSL real en lugar de `-k`
- Estás en un entorno corporativo con políticas de seguridad estrictas

## Paso 1: Copiar el certificado del servidor al cliente

**En el servidor:**
```bash
# El certificado público está en certs/cert.pem
cat certs/cert.pem
```

**En el cliente:**
```bash
# Crear directorio para certificados personalizados
sudo mkdir -p /usr/local/share/ca-certificates/loglife

# Copiar el certificado (desde el servidor)
scp usuario@10.69.0.3:/ruta/a/loglifeserver/certs/cert.pem \
    /tmp/loglife-cert.crt

# Moverlo al directorio de certificados
sudo mv /tmp/loglife-cert.crt /usr/local/share/ca-certificates/loglife/loglife.crt
```

## Paso 2: Instalar el certificado según el sistema operativo

### Ubuntu/Debian
```bash
# Actualizar certificados del sistema
sudo update-ca-certificates

# Deberías ver:
# 1 added, 0 removed; done.
```

### RedHat/CentOS/Fedora
```bash
# Copiar a directorio de CAs
sudo cp /usr/local/share/ca-certificates/loglife/loglife.crt \
    /etc/pki/ca-trust/source/anchors/

# Actualizar certificados
sudo update-ca-trust
```

### macOS
```bash
# Agregar al keychain
sudo security add-trusted-cert -d -r trustRoot \
    -k /Library/Keychains/System.keychain \
    /usr/local/share/ca-certificates/loglife/loglife.crt
```

## Paso 3: Verificar instalación

```bash
# Ahora debería funcionar SIN -k
curl "https://10.69.0.3:3001/logs?key=algo"

# Si aún falla, puede ser por el hostname
# El certificado está generado para "localhost", no para la IP
```

## Limitación importante: Nombre del host

Los certificados autofirmados generados con `./generate_cert.sh` tienen `CN=localhost`,
por lo que **solo funcionarán** para conexiones a `https://localhost:3001`.

Si quieres usarlos con una IP (como `10.69.0.3`) o un dominio, necesitas regenerar el certificado:

### Generar certificado con IP específica

```bash
# En el servidor, edita generate_cert.sh y agrega SAN (Subject Alternative Name)
# O usa este comando directo:

openssl req -x509 -newkey rsa:4096 -nodes \
  -keyout ./certs/key.pem \
  -out ./certs/cert.pem \
  -days 365 \
  -subj "/C=ES/ST=State/L=City/O=Organization/CN=10.69.0.3" \
  -addext "subjectAltName=IP:10.69.0.3,DNS:localhost"

chmod 600 ./certs/key.pem
chmod 644 ./certs/cert.pem
```

Luego reinicia el servidor Docker:
```bash
docker-compose restart api
```

## Recomendación

**Para la mayoría de casos, no necesitas instalar el certificado.**

El script `./loglife` y curl con `-k` funcionan perfectamente para servidores privados.

Solo instala el certificado si:
- Tienes requisitos de seguridad específicos
- Quieres evitar advertencias en navegadores
- Estás configurando múltiples clientes en un entorno corporativo
