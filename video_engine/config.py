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
    
    # Dossiers Médias partagés avec Laravel
    WORKSPACE_DIR = os.getenv("WORKSPACE_DIR", "/app/medias")
    LIBRARY_DIR = os.path.join(WORKSPACE_DIR, "library")
    RENDERS_DIR = os.path.join(WORKSPACE_DIR, "renders")
    
    # Vidéo (Format TikTok / Shorts / Reels 9:16)
    TARGET_RESOLUTION = (
        int(os.getenv("VIDEO_TARGET_W", 1080)),
        int(os.getenv("VIDEO_TARGET_H", 1920))
    )
    SPEED_RAMP_MIN = float(os.getenv("SPEED_RAMP_MIN", 0.96))
    SPEED_RAMP_MAX = float(os.getenv("SPEED_RAMP_MAX", 1.04))
    
    # Police pour les sous-titres dynamiques
    SUBTITLE_FONT = os.getenv(
        "SUBTITLE_FONT",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    )
    
    # Whisper (Fallback local si pas de WordBoundary)
    WHISPER_MODEL = os.getenv("WHISPER_MODEL", "small")
    WHISPER_COMPUTE_TYPE = os.getenv("WHISPER_COMPUTE_TYPE", "int8")
