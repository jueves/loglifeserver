#!/usr/bin/env python3
"""
Script de inicio del servidor con soporte opcional para HTTPS
"""
import os
import sys
import uvicorn

def main():
    # Configuración básica
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "3001"))

    # Configuración SSL (opcional)
    ssl_cert = os.getenv("SSL_CERT_PATH")
    ssl_key = os.getenv("SSL_KEY_PATH")

    config = {
        "app": "main:app",
        "host": host,
        "port": port,
        "reload": os.getenv("RELOAD", "false").lower() == "true"
    }

    # Si hay certificados SSL configurados, habilitar HTTPS
    if ssl_cert and ssl_key:
        if not os.path.exists(ssl_cert):
            print(f"Error: Certificado no encontrado en {ssl_cert}")
            sys.exit(1)
        if not os.path.exists(ssl_key):
            print(f"Error: Clave privada no encontrada en {ssl_key}")
            sys.exit(1)

        config["ssl_certfile"] = ssl_cert
        config["ssl_keyfile"] = ssl_key
        print(f"🔒 Iniciando servidor HTTPS en https://{host}:{port}")
    else:
        print(f"🌐 Iniciando servidor HTTP en http://{host}:{port}")

    # Iniciar servidor
    uvicorn.run(**config)

if __name__ == "__main__":
    main()
