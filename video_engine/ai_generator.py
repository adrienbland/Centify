import asyncio
import re
import edge_tts
import requests
from config import Config
from logger import setup_logger

logger = setup_logger("AIGenerator")

class AIGenerator:
    """
    Gestion des LLM (Ollama) et TTS (Edge-TTS avec extraction WordBoundary).
    """

    @staticmethod
    def clean_text_for_tts(text: str) -> str:
        """
        Nettoie le texte avant envoi au moteur vocal (Edge-TTS) :
        - Supprime les balises [HOOK]:, [BODY]:, [CTA]:
        - Supprime les URLs (pour éviter que la voix lise 'https deux points slash slash')
        - Supprime les emojis résiduels et les points de suspension
        """
        if not text:
            return ""
        cleaned = re.sub(r'\[(HOOK|BODY|CTA)\]\s*:?', '', text, flags=re.IGNORECASE)
        cleaned = re.sub(r'https?://\S+', '', cleaned)
        cleaned = re.sub(r'[\U00010000-\U0010ffff]', '', cleaned)
        cleaned = cleaned.replace('...', '.').replace('*', '').replace('#', '')
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        return cleaned

    @staticmethod
    def generate_script(product_name, niche, description="", custom_prompt=""):
        """
        Génère un script viral avec Ollama.
        """
        logger.info(f"Génération du script pour : {product_name}...")
        prompt = (
            f"Tu es un copywriter expert TikTok et Shorts dans la niche {niche or 'Général'}.\n"
            f"Génère un script vidéo vocal très court (15 secondes max) et dynamique pour vendre : '{product_name}'.\n"
            f"Description du produit : {description}\n"
            f"RÈGLES STRICTES POUR LA VOIX IA (TTS) :\n"
            f"1. NE LIS JAMAIS le titre AliExpress complet. Utilise un nom naturel (ex: 'cet accessoire', 'cette brosse magique').\n"
            f"2. INTERDICTION d'utiliser des emojis, des URLs ou des points de suspension (...).\n"
            f"3. Directives spécifiques : {custom_prompt or 'Rends le texte ultra engageant.'}\n"
            f"Réponds UNIQUEMENT avec le texte à prononcer, sans didascalies."
        )

        payload = {
            "model": Config.OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False
        }

        try:
            response = requests.post(Config.OLLAMA_URL, json=payload, timeout=60)
            response.raise_for_status()
            raw = response.json().get("response", "").strip()
            return AIGenerator.clean_text_for_tts(raw)
        except Exception as e:
            logger.error(f"Erreur Ollama lors de la génération du script : {e}")
            return f"Arrête de scroller ! Cet accessoire incroyable va transformer ton quotidien en quelques secondes. Clique sur le lien en bio pour en profiter !"

    @staticmethod
    def revise_script_with_feedback(original_text, product_name, user_feedback):
        """
        Réécrit un script existant en prenant en compte le commentaire de retouche (Feedback Loop).
        """
        logger.info(f"Révision IA du script pour '{product_name}' avec feedback : {user_feedback}")
        prompt = (
            f"Tu es un copywriter expert TikTok. Voici le script vocal actuel pour le produit '{product_name}' :\n"
            f"\"{original_text}\"\n\n"
            f"L'utilisateur demande la modification suivante :\n"
            f"\"{user_feedback}\"\n\n"
            f"Réécris le script (15 secondes max) en appliquant strictement cette consigne.\n"
            f"RÈGLES : Français naturel, AUCUN emoji, AUCUNE URL, AUCUN point de suspension (...), et pas de balises.\n"
            f"Réponds UNIQUEMENT avec le nouveau texte à prononcer."
        )

        payload = {
            "model": Config.OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False
        }

        try:
            response = requests.post(Config.OLLAMA_URL, json=payload, timeout=60)
            response.raise_for_status()
            revised = response.json().get("response", "").strip()
            cleaned = AIGenerator.clean_text_for_tts(revised)
            return cleaned if cleaned else AIGenerator.clean_text_for_tts(original_text)
        except Exception as e:
            logger.error(f"Erreur Ollama lors de la révision du script : {e}")
            return AIGenerator.clean_text_for_tts(original_text)

    @staticmethod
    async def generate_voiceover_with_timestamps(text, output_path, voice=None):
        """
        Génère l'audio MP3 avec Edge-TTS ET récupère simultanément les horodatages exacts
        de chaque mot (WordBoundary) pour créer des sous-titres TikTok synchronisés au millième près.
        """
        clean_text = AIGenerator.clean_text_for_tts(text)
        if not clean_text:
            clean_text = "Découvrez ce produit exceptionnel dès maintenant, lien en bio !"

        selected_voice = voice or Config.TTS_VOICE
        logger.info(f"Génération de la voix-off ({selected_voice}) vers {output_path}...")

        word_timestamps = []
        try:
            communicate = edge_tts.Communicate(clean_text, selected_voice, boundary="WordBoundary")
            with open(output_path, "wb") as audio_file:
                async for chunk in communicate.stream():
                    if chunk["type"] == "audio":
                        audio_file.write(chunk["data"])
                    elif chunk["type"] == "WordBoundary":
                        start_sec = chunk["offset"] / 10_000_000.0
                        duration_sec = chunk["duration"] / 10_000_000.0
                        word_timestamps.append({
                            "text": chunk["text"].strip(),
                            "start": start_sec,
                            "end": start_sec + duration_sec
                        })

            logger.info(f"Voix-off générée avec succès ({len(word_timestamps)} mots horodatés).")
            return word_timestamps
        except Exception as e:
            logger.error(f"Échec de la génération de la voix-off : {e}")
            raise

    @staticmethod
    async def generate_voiceover(text, output_path):
        """
        Méthode de compatibilité qui génère l'audio et retourne les timestamps.
        """
        return await AIGenerator.generate_voiceover_with_timestamps(text, output_path)
