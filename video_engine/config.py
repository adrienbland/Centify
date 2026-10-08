import os

class Config:
    """
    Gestionnaire central des paramètres.
    Lit depuis les variables d'environnement ou utilise des valeurs par défaut robustes.
    Ces valeurs pourront être dynamiquement modifiées par le Hub Laravel en base de données.
    """
    # IA et TTS
    OLLAMA_URL = os.getenv("OLLAMA_URL", "http://host.docker.internal:11434/api/generate")
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")
    TTS_VOICE = os.getenv("TTS_VOICE", "fr-FR-HenriNeural")
    
    # Vidéo
    TARGET_RESOLUTION = (
        int(os.getenv("VIDEO_TARGET_W", 1080)),
        int(os.getenv("VIDEO_TARGET_H", 1920))
    )
    SPEED_RAMP_MIN = float(os.getenv("SPEED_RAMP_MIN", 0.95))
    SPEED_RAMP_MAX = float(os.getenv("SPEED_RAMP_MAX", 1.05))
    
    # Whisper
    WHISPER_MODEL = os.getenv("WHISPER_MODEL", "small")
    WHISPER_COMPUTE_TYPE = os.getenv("WHISPER_COMPUTE_TYPE", "int8")
