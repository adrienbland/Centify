import os
from faster_whisper import WhisperModel
from moviepy.editor import TextClip, CompositeVideoClip, VideoFileClip

class SubtitleGenerator:
    """
    Générateur de sous-titres dynamiques 100% local (Faster-Whisper).
    """
    def __init__(self, model_size="small", compute_type="int8"):
        # "small" ou "base" est suffisant pour des vidéos courtes et rapides.
        # compute_type="int8" permet de consommer très peu de RAM/VRAM.
        print(f"[SubtitleGenerator] Chargement du modèle Whisper ({model_size})...")
        self.model = WhisperModel(model_size, device="cpu", compute_type=compute_type)

    def extract_word_timestamps(self, audio_path):
        """
        Transcrit l'audio et renvoie une liste de dictionnaires pour chaque mot avec start et end.
        """
        print(f"[SubtitleGenerator] Transcription de l'audio : {audio_path}")
        segments, info = self.model.transcribe(audio_path, word_timestamps=True, language="fr")
        
        words = []
        for segment in segments:
            for word in segment.words:
                words.append({
                    "text": word.word.strip(),
                    "start": word.start,
                    "end": word.end
                })
        return words

    def overlay_subtitles_on_video(self, video_path, audio_path, output_path):
        """
        Génère les mots, crée les clips textuels avec MoviePy, et les superpose à la vidéo.
        """
        # 1. Obtenir les mots horodatés
        words = self.extract_word_timestamps(audio_path)
        
        # 2. Charger la vidéo
        video = VideoFileClip(video_path)
        
        # 3. Créer un TextClip pour chaque mot
        subtitle_clips = []
        
        # Astuce : Pour TikTok/Reels, le texte doit être gros, centré, jaune ou blanc,
        # avec un contour noir pour ressortir.
        for w in words:
            # Durée minimum pour éviter un bug de TextClip sur des mots ultra-courts
            duration = max(w["end"] - w["start"], 0.1)
            
            # ATTENTION : Nécessite ImageMagick d'installé sur le système pour TextClip
            txt_clip = (TextClip(w["text"], fontsize=90, color='yellow', font='Arial-Bold',
                                 stroke_color='black', stroke_width=3, method='caption', 
                                 size=(video.w * 0.8, None))
                        .set_position(('center', 'center'))
                        .set_start(w["start"])
                        .set_duration(duration))
            
            subtitle_clips.append(txt_clip)
            
        # 4. Superposer sur la vidéo originale
        final_video = CompositeVideoClip([video] + subtitle_clips)
        
        print(f"[SubtitleGenerator] Rendu avec sous-titres : {output_path}")
        final_video.write_videofile(
            output_path, 
            codec="libx264", 
            audio_codec="aac",
            fps=30,
            preset="ultrafast"
        )
        
        video.close()
        final_video.close()
        print("[SubtitleGenerator] Terminé avec succès !")

if __name__ == "__main__":
    # Test local
    print("Initialisation du module de sous-titrage...")
    # sg = SubtitleGenerator(model_size="small")
    # sg.overlay_subtitles_on_video("rendu_tiktok.mp4", "test_audio.mp3", "rendu_final_subbed.mp4")
