import asyncio
import edge_tts
import requests
from config import Config
from logger import setup_logger

logger = setup_logger("AIGenerator")

class AIGenerator:
    """
    Gestion des LLM (Ollama) et TTS (Edge-TTS).
    """
    
    @staticmethod
    def generate_script(product_name, niche):
        """
        Génère un script viral avec Ollama.
        """
        logger.info(f"Génération du script pour : {product_name}...")
        prompt = (
            f"Tu es un expert TikTok dans la niche {niche}. "
            f"Génère un script vidéo vocal très court (15 secondes max) et agressif "
            f"pour vendre : {product_name}. "
            f"Structure : 1 Hook choc. 2 Description rapide du problème résolu. 3 Appel à l'action. "
            f"Réponds UNIQUEMENT avec le texte à prononcer, sans didascalies, sans emojis."
        )
        
        payload = {
            "model": Config.OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False
        }
        
        try:
            response = requests.post(Config.OLLAMA_URL, json=payload, timeout=60)
            response.raise_for_status()
            return response.json().get("response", "").strip()
        except requests.exceptions.Timeout:
            logger.error("Timeout : Le serveur Ollama a mis trop de temps à répondre.")
            return f"Incroyable ! Ce {product_name} va changer votre vie. Lien en bio !"
        except Exception as e:
            logger.error(f"Erreur Ollama: {e}")
            return f"Incroyable ! Ce {product_name} va changer votre vie. Lien en bio !"

    @staticmethod
    async def generate_voiceover(text, output_path):
        """
        Génère l'audio avec Edge-TTS.
        """
        logger.info(f"Génération de la voix-off vers {output_path}...")
        try:
            communicate = edge_tts.Communicate(text, Config.TTS_VOICE)
            await communicate.save(output_path)
            logger.info("Voix-off générée avec succès.")
        except Exception as e:
            logger.error(f"Échec de la génération de la voix-off : {e}")
            raise

