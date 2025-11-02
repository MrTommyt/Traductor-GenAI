#!/bin/bash

# Script para publicar en Docker Hub
# Uso: ./publish_to_dockerhub.sh tu_usuario_dockerhub

set -e

if [ -z "$1" ]; then
    echo "Error: No se proporciono usuario de Docker Hub"
    echo "Uso: ./publish_to_dockerhub.sh tu_usuario_dockerhub"
    exit 1
fi

DOCKERHUB_USER="$1"
IMAGE_NAME="traductor-genai"
TAG="1.0.0"
FULL_IMAGE="${DOCKERHUB_USER}/${IMAGE_NAME}:${TAG}"

echo "========================================"
echo "Publicando en Docker Hub"
echo "========================================"
echo ""

# Verificar imagen
if ! docker images | grep -q "traductor-genai"; then
    echo "Error: Imagen local no encontrada"
    echo "Ejecuta: docker build -t traductor-genai:1.0.0 ."
    exit 1
fi
echo "Imagen local OK"

# Login
echo ""
echo "Iniciando sesion en Docker Hub..."
if docker login; then
    echo "Login exitoso"
else
    echo "Error al hacer login"
    exit 1
fi

# Tag
echo ""
echo "Taggeando imagen..."
docker tag traductor-genai:1.0.0 "$FULL_IMAGE"
echo "Imagen taggeada: $FULL_IMAGE"

# Push
echo ""
echo "Publicando (esto puede tardar)..."
if docker push "$FULL_IMAGE"; then
    echo "Publicacion exitosa"
else
    echo "Error al publicar"
    exit 1
fi

echo ""
echo "========================================"
echo "Publicado: $FULL_IMAGE"
echo "========================================"
echo ""
echo "Ver en: https://hub.docker.com/r/$DOCKERHUB_USER/$IMAGE_NAME"
echo ""
