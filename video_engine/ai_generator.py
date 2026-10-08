import asyncio
import edge_tts
import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "qwen2.5:7b"

class AIGenerator:
    """
    Gestion des LLM (Ollama) et TTS (Edge-TTS).
    """
    
    @staticmethod
    def generate_script(product_name, niche):
        """
        Génère un script viral avec Ollama.
        """
        print(f"[AIGenerator] Génération du script pour : {product_name}...")
        prompt = (
            f"Tu es un expert TikTok dans la niche {niche}. "
            f"Génère un script vidéo vocal très court (15 secondes max) et agressif "
            f"pour vendre : {product_name}. "
            f"Structure : 1 Hook choc. 2 Description rapide du problème résolu. 3 Appel à l'action. "
            f"Réponds UNIQUEMENT avec le texte à prononcer, sans didascalies, sans emojis."
        )
        
        payload = {
            "model": MODEL,
            "prompt": prompt,
            "stream": False
        }
        
        try:
            response = requests.post(OLLAMA_URL, json=payload, timeout=60)
            response.raise_for_status()
            return response.json().get("response", "").strip()
        except Exception as e:
            print(f"[AIGenerator] Erreur Ollama: {e}")
            return f"Incroyable ! Ce {product_name} va changer votre vie. Lien en bio !"

    @staticmethod
    async def generate_voiceover(text, output_path):
        """
        Génère l'audio avec Edge-TTS.
        """
        print(f"[AIGenerator] Génération de la voix-off vers {output_path}...")
        # Voix masculine dynamique française
        voice = "fr-FR-HenriNeural" 
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(output_path)
        print("[AIGenerator] Voix-off générée avec succès.")

