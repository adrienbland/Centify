import os
from moviepy import TextClip, CompositeVideoClip, VideoFileClip
from config import Config
from logger import setup_logger

logger = setup_logger("SubtitleGenerator")

class SubtitleGenerator:
    """
    Générateur de sous-titres dynamiques style TikTok / Shorts (MoviePy 2.x).
    Utilise en priorité les horodatages WordBoundary d'Edge-TTS (ultra-rapide, 0 RAM),
    avec fallback automatique sur Faster-Whisper si nécessaire.
    """
    def __init__(self, model_size="small", compute_type="int8"):
        self.model_size = model_size
        self.compute_type = compute_type
        self._whisper_model = None
        self.font_path = Config.SUBTITLE_FONT
        if not os.path.exists(self.font_path):
            # Fallback sur une police DejaVu standard si le chemin custom n'existe pas
            self.font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

    def _get_whisper_model(self):
        if self._whisper_model is None:
            from faster_whisper import WhisperModel
            logger.info(f"Chargement à la demande du modèle Faster-Whisper ({self.model_size})...")
            self._whisper_model = WhisperModel(self.model_size, device="cpu", compute_type=self.compute_type)
        return self._whisper_model

    def extract_word_timestamps(self, audio_path):
        """
        Fallback : Transcrit l'audio avec Faster-Whisper et renvoie la liste des mots horodatés.
        """
        logger.info(f"Transcription Whisper de l'audio : {audio_path}")
        model = self._get_whisper_model()
        segments, _ = model.transcribe(audio_path, word_timestamps=True, language="fr")
        
        words = []
        for segment in segments:
            for word in segment.words:
                words.append({
                    "text": word.word.strip(),
                    "start": float(word.start),
                    "end": float(word.end)
                })
        return words

    @staticmethod
    def group_words_into_chunks(words, max_words=3, max_chars=22):
        """
        Regroupe les mots individuels en groupes dynamiques de 2 à 3 mots
        (style Hormozi / TikTok viral) pour une lecture fluide et percutante.
        """
        if not words:
            return []

        chunks = []
        current_words = []
        chunk_start = words[0]["start"]
        chunk_end = words[0]["end"]

        for w in words:
            word_text = w["text"].strip()
            if not word_text:
                continue

            current_len = sum(len(x) for x in current_words) + len(current_words)
            if current_words and (len(current_words) >= max_words or (current_len + len(word_text)) > max_chars):
                chunks.append({
                    "text": " ".join(current_words).upper(),
                    "start": chunk_start,
                    "end": max(chunk_end, chunk_start + 0.15)
                })
                current_words = [word_text]
                chunk_start = w["start"]
                chunk_end = w["end"]
            else:
                if not current_words:
                    chunk_start = w["start"]
                current_words.append(word_text)
                chunk_end = w["end"]

        if current_words:
            chunks.append({
                "text": " ".join(current_words).upper(),
                "start": chunk_start,
                "end": max(chunk_end, chunk_start + 0.2)
            })

        # Éviter tout chevauchement entre deux chunks consécutifs
        for i in range(len(chunks) - 1):
            if chunks[i]["end"] > chunks[i + 1]["start"]:
                chunks[i]["end"] = chunks[i + 1]["start"]

        return chunks

    def build_subtitle_clips(self, word_timestamps, video_size, audio_path=None):
        """
        Construit la liste des TextClips MoviePy 2.x à superposer sur la vidéo.
        """
        words = word_timestamps
        if not words and audio_path and os.path.exists(audio_path):
            words = self.extract_word_timestamps(audio_path)

        chunks = self.group_words_into_chunks(words, max_words=3, max_chars=20)
        logger.info(f"Génération de {len(chunks)} cartons de sous-titres dynamiques...")

        video_w, video_h = video_size
        subtitle_clips = []

        for idx, chunk in enumerate(chunks):
            duration = max(chunk["end"] - chunk["start"], 0.12)
            # Alternance Jaune / Blanc pour dynamiser la rétention visuelle
            text_color = "#FFD700" if idx % 2 == 0 else "#FFFFFF"

            txt_clip = (
                TextClip(
                    font=self.font_path,
                    text=chunk["text"],
                    font_size=76,
                    color=text_color,
                    stroke_color="black",
                    stroke_width=5,
                    method="caption",
                    size=(int(video_w * 0.86), None),
                    text_align="center",
                    margin=(12, 16),
                )
                .with_position(("center", int(video_h * 0.62)))
                .with_start(chunk["start"])
                .with_duration(duration)
            )
            subtitle_clips.append(txt_clip)

        return subtitle_clips

    def overlay_subtitles_on_video(self, video_path, audio_path, output_path, word_timestamps=None):
        """
        Méthode standalone pour incruster les sous-titres sur une vidéo existante.
        """
        video = VideoFileClip(video_path)
        subtitle_clips = self.build_subtitle_clips(word_timestamps, video.size, audio_path=audio_path)
        final_video = CompositeVideoClip([video] + subtitle_clips)

        logger.info(f"Rendu avec sous-titres : {output_path}")
        final_video.write_videofile(
            output_path,
            codec="libx264",
            audio_codec="aac",
            fps=24,
            preset="ultrafast",
            logger=None
        )
        video.close()
        final_video.close()
        logger.info("Sous-titrage terminé avec succès !")
