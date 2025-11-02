# Dockerfile para la aplicación de traducción
FROM python:3.11-slim

WORKDIR /app

# Copiar requirements e instalar dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar aplicación
COPY app.py .

# Exponer puerto de Gradio
EXPOSE 7860

# Comando por defecto
CMD ["python", "app.py"]

