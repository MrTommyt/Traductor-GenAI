# Proyecto: Traductor Gen-AI con MLflow Tracking
- Camilo Benavides (2021114019)
- Carlos Castrillon (2021214042)

## Descripción

Sistema de traducción de texto utilizando modelos generativos de inteligencia artificial (Gen-AI) a través de OpenAI GPT-4o mini, con interfaz web desarrollada en Gradio y tracking completo de interacciones mediante MLflow.

## Arquitectura del Sistema

El sistema implementa una arquitectura de microservicios en contenedores Docker independientes, sin utilizar docker-compose. La comunicación entre servicios se establece mediante una red Docker dedicada.

```
┌──────────────────────────────────────────────────────────────┐
│                    Docker Network: translation-net          │
│                                                              │
│  ┌─────────────────────────┐         ┌────────────────────┐ │
│  │   translation-app       │         │   mlflow-server    │ │
│  │   (Puerto 7860)         │         │   (Puerto 5000)    │ │
│  │                         │         │                    │ │
│  │  • Gradio UI            │◄───────►│  • MLflow Track    │ │
│  │  • OpenAI SDK           │  HTTP   │  • SQLite Backend  │ │
│  │  • MLflow Client        │         │                    │ │
│  │                         │         │                    │ │
│  └─────────────────────────┘         └────────────────────┘ │
│           │                                      │           │
└───────────┼──────────────────────────────────────┼───────────┘
            │                                      │
    ┌───────┴────────┐                    ┌───────┴─────────┐
    │ Host:7860      │                    │ Host:5000       │
    │ (Acceso Web)   │                    │ (MLflow UI)     │
    └────────────────┘                    └─────────────────┘
```

### Componentes

**Contenedor App** (translation-app):
- Puerto 7860: Interfaz web Gradio
- Integración con OpenAI API
- Cliente MLflow para tracking

**Contenedor MLflow** (mlflow-server):
- Puerto 5000: Interfaz MLflow
- Backend SQLite para persistencia
- Tracking de parámetros, métricas y artifacts

## Instalación y Configuración

### Prerequisitos

- Docker instalado y funcionando
- API Key de OpenAI
- Cuenta de Docker Hub (opcional, para publicación)

### Configuración de API Key

La API key debe pasarse como variable de entorno al ejecutar el contenedor. NUNCA se debe incluir en el Dockerfile ni en archivos públicos del repositorio.

```bash
docker run -e API_KEY="sk-proj-..." ...
```

### Construcción y Ejecución

**Paso 1: Crear red Docker**

```bash
docker network create translation-net
```

**Paso 2: Levantar servidor MLflow**

```bash
docker run -d \
  --name mlflow-server \
  --network translation-net \
  -p 5000:5000 \
  -v $(pwd)/mlflow_data:/mlflow \
  python:3.11-slim sh -c "pip install mlflow && \
    mlflow server --host 0.0.0.0 --port 5000 --backend-store-uri file:/mlflow --allowed-hosts '*'"
```

**Paso 3: Construir imagen de la aplicación**

```bash
docker build -t traductor-genai:1.0.0 .
```

**Paso 4: Ejecutar aplicación**

```bash
docker run -d \
  --name translation-app \
  --network translation-net \
  -p 7860:7860 \
  -e API_KEY="sk-proj-tu-api-key" \
  -e MLFLOW_TRACKING_URI=http://mlflow-server:5000 \
  traductor-genai:1.0.0
```

**Paso 5: Acceso**

- Interfaz Gradio: http://localhost:7860
- Interfaz MLflow: http://localhost:5000

### Verificación

```bash
# Ver logs de la aplicación
docker logs -f translation-app

# Ver logs de MLflow
docker logs -f mlflow-server

# Verificar contenedores en ejecución
docker ps

# Verificar conectividad
curl http://localhost:7860
curl http://localhost:5000
```

## Tracking en MLflow

Cada traducción realizada es registrada automáticamente en MLflow con la siguiente información:

**Parámetros registrados:**
- target_language: Idioma objetivo seleccionado
- target_language_en: Nombre del idioma en inglés
- model: "gpt-4o-mini"
- prompt_hash: Hash MD5 del prompt (8 caracteres)
- source_language: "auto-detect"
- translated_text_preview: Primeros 100 caracteres de la traducción

**Métricas registradas:**
- latency_ms: Latencia total en milisegundos
- len_response: Longitud de la respuesta traducida
- len_input: Longitud del texto original

**Artifacts guardados:**
- Archivo .txt con el texto original, traducción y métricas

## Publicación en Docker Hub

Para publicar la imagen en Docker Hub:

**Paso 1: Login**

```bash
docker login
```

**Paso 2: Tagguear imagen**

```bash
docker tag traductor-genai:1.0.0 tu_usuario/traductor-genai:1.0.0
```

**Paso 3: Publicar**

```bash
docker push tu_usuario/traductor-genai:1.0.0
```

**Verificar publicación:**

Acceder a: https://hub.docker.com/r/tu_usuario/traductor-genai

## Ejecución Remota

Para ejecutar la aplicación en otra máquina:

**Paso 1: Setup inicial**

```bash
docker network create translation-net
mkdir -p mlflow_data
```

**Paso 2: Levantar MLflow**

```bash
docker run -d \
  --name mlflow-server \
  --network translation-net \
  -p 5000:5000 \
  -v $(pwd)/mlflow_data:/mlflow \
  python:3.11-slim sh -c "pip install mlflow && \
    mlflow server --host 0.0.0.0 --port 5000 --backend-store-uri file:/mlflow --allowed-hosts '*'"
```

**Paso 3: Descargar y ejecutar aplicación**

```bash
docker pull tu_usuario/traductor-genai:1.0.0

docker run -d \
  --name translation-app \
  --network translation-net \
  -p 7860:7860 \
  -e API_KEY="sk-proj-tu-api-key" \
  -e MLFLOW_TRACKING_URI=http://mlflow-server:5000 \
  tu_usuario/traductor-genai:1.0.0
```

**Verificar:**

```bash
docker logs -f translation-app
```

Acceder a http://localhost:7860 para la interfaz de Gradio.

## Idiomas Soportados

El sistema soporta traducción bidireccional entre los siguientes idiomas:
- Español
- Inglés
- Francés
- Alemán
- Italiano
- Portugués
- Japonés
- Chino (Simplificado)
- Coreano
- Ruso

El modelo detecta automáticamente el idioma de origen.

## Observaciones

### Latencia

La latencia promedio de traducción oscila entre 1.5 y 3 segundos. Este tiempo depende de:
- Tamaño del texto a traducir
- Complejidad del idioma objetivo
- Carga actual de los servidores de OpenAI
- Latencia de red

### Calidad de Traducción

El modelo GPT-4o mini ofrece traducciones de alta calidad para textos generales, documentos y conversaciones. Para textos técnicos altamente especializados puede requerir ajustes.

### Registro de Métricas

Cada interacción queda registrada con timestamp automático, permitiendo análisis histórico de latencia y comparación entre diferentes lenguajes.

## Comandos de Mantenimiento

**Ver estado de contenedores:**

```bash
docker ps
docker ps -a
```

**Ver logs:**

```bash
docker logs translation-app
docker logs mlflow-server
docker logs -f translation-app  # Seguir en tiempo real
```

**Ver métricas de recursos:**

```bash
docker stats translation-app mlflow-server
```

**Detener contenedores:**

```bash
docker stop translation-app mlflow-server
```

**Iniciar contenedores detenidos:**

```bash
docker start translation-app mlflow-server
```

**Reiniciar contenedores:**

```bash
docker restart translation-app mlflow-server
```

**Limpiar todo:**

```bash
docker stop translation-app mlflow-server
docker rm translation-app mlflow-server
docker network rm translation-net
docker rmi traductor-genai:1.0.0
rm -rf mlflow_data/*
```

## Troubleshooting

**Error: "Cannot connect to MLflow"**

Verificar que ambos contenedores estén en la misma red:

```bash
docker network inspect translation-net
docker ps | grep mlflow
```

**Error: "API_KEY no está configurada"**

Asegurarse de pasar la variable de entorno al ejecutar:

```bash
docker run -e API_KEY="sk-..." ...
```

**Error: "Puerto ya en uso"**

Cambiar los puertos en el docker run:

```bash
-p 7861:7860  # Para Gradio
-p 5001:5000  # Para MLflow
```

**La imagen en Docker Hub no se actualiza**

Forzar rebuild sin cache:

```bash
docker build --no-cache -t traductor-genai:1.0.0 .
```

**Error: "Invalid Host header - possible DNS rebinding attack detected"**

Este error ocurre cuando MLflow rechaza conexiones desde otros contenedores. La solucion es usar el flag `--allowed-hosts '*'` al iniciar el servidor MLflow para permitir conexiones desde cualquier host.

## Estructura del Proyecto

```
.
├── app.py                    # Aplicación principal con Gradio y MLflow
├── requirements.txt          # Dependencias Python
├── Dockerfile               # Configuración de imagen Docker
├── .dockerignore           # Archivos excluidos del build
├── .dockerenv.example      # Ejemplo de configuración
├── run_demo.sh            # Script de ejecución automática
├── publish_to_dockerhub.sh # Script de publicación
└── mlflow_data/          # Datos de MLflow (generado automáticamente)
```

## Dependencias

- Python 3.11
- Gradio 4.7.1
- OpenAI SDK 2.6.1
- MLflow 2.11.0
- python-dotenv 1.0.0

## Consideraciones de Seguridad

El proyecto implementa las siguientes medidas de seguridad:

- Las API keys se pasan únicamente como variables de entorno
- No se incluyen credenciales en imágenes Docker
- No se incluyen secretos en archivos versionados
- La comunicación entre contenedores ocurre en una red aislada
- Los datos de MLflow se persisten en volúmenes locales

## Autores
Proyecto desarrollado como parte del curso de MLOps por:
- Camilo Benavides (2021114019)
- Carlos Castrillon (2021214042)

## Licencia

Este proyecto es parte de una demostración educativa sobre MLOps.
