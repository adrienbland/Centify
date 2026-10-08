import asyncio
import edge_tts
import requests
import json

# URL pointant vers le conteneur Ollama ou l'Ollama local de l'hôte (port 11434 d'après tes specs infra)
OLLAMA_URL = "http://localhost:11434/api/generate"
# J'utilise le modèle spécifié dans ton master infra (Qwen2.5:7b)
MODEL = "qwen2.5:7b" 

def generate_script(product_name):
    """
    Génère un script vidéo avec l'IA locale (Ollama).
    """
    prompt = (
        f"Tu es un expert TikTok. Génère un script vidéo très court et viral (15 secondes) "
        f"pour vendre le produit : {product_name}. "
        f"Le script doit contenir : 1) Un hook (phrase d'accroche), 2) Une description rapide, 3) Un appel à l'action (CTA). "
        f"Ne génère QUE les paroles qui seront dites à l'oral."
    )
    
    payload = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False
    }
    
    try:
        response = requests.post(OLLAMA_URL, json=payload)
        response.raise_for_status()
        return response.json().get("response", "").strip()
    except Exception as e:
        print(f"Erreur lors de la génération avec Ollama: {e}")
        return "Hook ! Regardez ce produit incroyable. Achetez-le maintenant via le lien en bio !"

async def generate_audio(text, output_file):
    """
    Génère un fichier audio à partir du texte avec Edge-TTS (100% gratuit).
    """
    # Voix masculine française dynamique
    voice = "fr-FR-HenriNeural" 
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_file)

async def main():
    product = "Mini Projecteur LED 4K Portable"
    print("====================================")
    print(f"1. Génération du script IA pour : {product}")
    print("====================================")
    
    script_text = generate_script(product)
    print(f"Script généré :\n{script_text}\n")
    
    audio_file = "test_audio.mp3"
    print("====================================")
    print("2. Génération de la voix off dynamique (edge-tts)...")
    print("====================================")
    
    await generate_audio(script_text, audio_file)
    print(f"✅ Audio généré et sauvegardé avec succès sous : {audio_file}")

if __name__ == "__main__":
    asyncio.run(main())

