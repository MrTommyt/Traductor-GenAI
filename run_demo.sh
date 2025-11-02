#!/bin/bash

# Script para ejecutar el sistema completo
# Uso: ./run_demo.sh [tu_api_key]

set -e

echo "========================================"
echo "Traductor Gen-AI - Inicio"
echo "========================================"
echo ""

# Verificar Docker
if ! docker info > /dev/null 2>&1; then
    echo "Error: Docker no esta corriendo"
    exit 1
fi
echo "Docker OK"

# API key
if [ -z "$1" ]; then
    echo "Advertencia: No se proporciono API key"
    API_KEY="${API_KEY:-}"
else
    API_KEY="$1"
    echo "API key proporcionada"
fi

# Limpiar instancias previas
echo ""
echo "Limpiando instancias previas..."
docker stop translation-app mlflow-server 2>/dev/null || true
docker rm translation-app mlflow-server 2>/dev/null || true

# Crear red
echo "Creando red Docker..."
if docker network inspect translation-net > /dev/null 2>&1; then
    echo "Red ya existe"
else
    docker network create translation-net
    echo "Red creada"
fi

# Levantar MLflow
echo ""
echo "Levantando MLflow..."
docker run -d \
  --name mlflow-server \
  --network translation-net \
  -p 5000:5000 \
  -v $(pwd)/mlflow_data:/mlflow \
  python:3.11-slim sh -c "pip install --quiet mlflow && \
    mlflow server --host 0.0.0.0 --port 5000 --backend-store-uri file:/mlflow --allowed-hosts '*'"

sleep 8
echo "MLflow corriendo en http://localhost:5000"

# Verificar imagen
echo ""
echo "Verificando imagen..."
if ! docker images | grep -q "traductor-genai"; then
    echo "Imagen no encontrada, construyendo..."
    docker build -t traductor-genai:1.0.0 .
    echo "Imagen construida"
else
    echo "Imagen encontrada"
fi

# Levantar App
echo ""
echo "Levantando aplicacion..."
if [ -z "$API_KEY" ]; then
    docker run -d \
      --name translation-app \
      --network translation-net \
      -p 7860:7860 \
      -e MLFLOW_TRACKING_URI=http://mlflow-server:5000 \
      traductor-genai:1.0.0
else
    docker run -d \
      --name translation-app \
      --network translation-net \
      -p 7860:7860 \
      -e API_KEY="$API_KEY" \
      -e MLFLOW_TRACKING_URI=http://mlflow-server:5000 \
      traductor-genai:1.0.0
fi

sleep 5
echo "App corriendo en http://localhost:7860"

echo ""
echo "========================================"
echo "Sistema iniciado"
echo "========================================"
echo ""
echo "Gradio: http://localhost:7860"
echo "MLflow: http://localhost:5000"
echo ""
echo "Ver logs: docker logs -f translation-app"
echo "Detener: docker stop translation-app mlflow-server"
echo ""

docker logs -f translation-app
