"""
Traductor Gen-AI con Gradio y MLflow Tracking
"""
import os
import time
import hashlib
import gradio as gr
from openai import OpenAI
from dotenv import load_dotenv
import mlflow

# Cargar variables de entorno
load_dotenv()

# Configuración MLflow
MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000")
mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)

# Crear o obtener experimento
try:
    experiment = mlflow.get_experiment_by_name("translation_genai")
    if experiment is None:
        experiment_id = mlflow.create_experiment("translation_genai")
        print(f"Experimento creado: {experiment_id}")
    else:
        experiment_id = experiment.experiment_id
        print(f"Experimento existe: {experiment_id}")
except Exception as e:
    print(f"Warning: Error al configurar experimento: {e}")
    experiment_id = None

# Configuración OpenAI
API_KEY = os.getenv("API_KEY")
if not API_KEY:
    raise ValueError("API_KEY no está configurada en las variables de entorno")

client = OpenAI(api_key=API_KEY)

# Diccionario de idiomas soportados
LANGUAGES = {
    "Español": "Spanish",
    "Inglés": "English",
    "Francés": "French",
    "Alemán": "German",
    "Italiano": "Italian",
    "Portugués": "Portuguese",
    "Japonés": "Japanese",
    "Chino (Simplificado)": "Chinese (Simplified)",
    "Coreano": "Korean",
    "Ruso": "Russian"
}

def translate_text(text, target_language):
    """Traduce texto usando OpenAI GPT-4o mini y registra en MLflow"""
    if not text.strip():
        return "Por favor ingresa un texto para traducir"
    
    start_time = time.time()
    target_lang_en = LANGUAGES.get(target_language, "English")
    prompt = f"Translate the following text to {target_lang_en}. Return only the translation, no explanations:\n\n{text}"
    prompt_hash = hashlib.md5(prompt.encode()).hexdigest()[:8]
    
    if experiment_id is None:
        return "Error: MLflow no esta configurado correctamente"
    
    try:
        with mlflow.start_run(run_name=f"translation_{int(time.time())}", experiment_id=experiment_id):
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a professional translator."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            
            translated_text = response.choices[0].message.content.strip()
            latency_ms = (time.time() - start_time) * 1000
            len_response = len(translated_text)
            
            mlflow.log_param("target_language", target_language)
            mlflow.log_param("target_language_en", target_lang_en)
            mlflow.log_param("model", "gpt-4o-mini")
            mlflow.log_param("prompt_hash", prompt_hash)
            mlflow.log_param("source_language", "auto-detect")
            
            mlflow.log_metric("latency_ms", latency_ms)
            mlflow.log_metric("len_response", len_response)
            mlflow.log_metric("len_input", len(text))
            
            artifact_dir = "/tmp/mlflow_artifacts"
            os.makedirs(artifact_dir, exist_ok=True)
            
            artifact_file = os.path.join(artifact_dir, f"translation_{prompt_hash}.txt")
            with open(artifact_file, "w", encoding="utf-8") as f:
                f.write("=== TEXTO ORIGINAL ===\n")
                f.write(f"{text}\n\n")
                f.write(f"=== TRADUCCION A {target_language.upper()} ===\n")
                f.write(f"{translated_text}\n\n")
                f.write(f"=== METRICAS ===\n")
                f.write(f"Latencia: {latency_ms:.2f} ms\n")
                f.write(f"Longitud respuesta: {len_response} caracteres\n")
            
            mlflow.log_artifact(artifact_file)
            mlflow.log_param("translated_text_preview", translated_text[:100] + "..." if len(translated_text) > 100 else translated_text)
            
        return translated_text
    
    except Exception as e:
        error_msg = f"Error durante la traduccion: {str(e)}"
        try:
            with mlflow.start_run(run_name=f"error_{int(time.time())}", experiment_id=experiment_id):
                mlflow.log_param("error", str(e))
                mlflow.log_param("target_language", target_language)
        except:
            pass
        return error_msg

# Interfaz Gradio
def create_interface():
    """Crea la interfaz de usuario de Gradio"""
    
    with gr.Blocks(title="Traductor Gen-AI", theme=gr.themes.Soft()) as interface:
        gr.Markdown(
            """
            # Traductor Generativo con IA
            Traduce texto usando GPT-4o mini de OpenAI con seguimiento en MLflow
            """
        )
        
        with gr.Row():
            with gr.Column(scale=2):
                text_input = gr.Textbox(
                    label="Texto a traducir",
                    placeholder="Escribe aquí el texto que deseas traducir...",
                    lines=5,
                    max_lines=10
                )
                
                target_lang = gr.Dropdown(
                    label="Idioma objetivo",
                    choices=list(LANGUAGES.keys()),
                    value="Inglés",
                    interactive=True
                )
                
                translate_btn = gr.Button(
                    "Traducir",
                    variant="primary",
                    size="lg"
                )
            
            with gr.Column(scale=2):
                result_output = gr.Textbox(
                    label="Traduccion",
                    placeholder="Aqui aparecera la traduccion...",
                    lines=5,
                    interactive=False
                )
                
                info_output = gr.Markdown(
                    value="Cada traduccion se registra automaticamente en MLflow"
                )
        
        gr.Markdown(
            """
            ### Ejemplo
            - Original: "Hola, como estas?"
            - Objetivo: Ingles
            - Resultado: "Hello, how are you?"
            
            ### Tracking MLflow
            Cada traduccion genera un run con:
            - Parametros: idioma objetivo, modelo, hash del prompt
            - Metricas: latencia (ms), longitud de respuesta
            - Artifacts: archivo .txt con la traduccion completa
            """
        )
        
        translate_btn.click(
            fn=translate_text,
            inputs=[text_input, target_lang],
            outputs=result_output
        )
    
    return interface

if __name__ == "__main__":
    print("Iniciando aplicacion de traduccion...")
    print(f"MLflow Tracking URI: {MLFLOW_TRACKING_URI}")
    print(f"API Key configurada: Si" if API_KEY else "API Key configurada: No")
    
    interface = create_interface()
    interface.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False
    )

