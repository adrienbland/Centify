import os
import io
import random
import subprocess
import requests
from PIL import Image, ImageDraw, ImageFont, ImageOps
from moviepy import VideoFileClip, AudioFileClip, ImageClip, CompositeVideoClip, CompositeAudioClip, vfx
from config import Config
from logger import setup_logger

logger = setup_logger("VideoProcessor")


class VideoProcessor:
    """
    Moteur de rendu vidéo automatisé (MoviePy 2.x).
    Applique des transformations dynamiques pour éviter le shadowban (contenu dupliqué),
    incruste la carte visuelle du produit (Image Produit + Badge) au-dessus du B-Roll,
    et mixe la voix-off + sous-titres dynamiques en une seule passe.
    """
    def __init__(self):
        self.target_resolution = Config.TARGET_RESOLUTION

    @staticmethod
    def ensure_default_broll(default_broll_path):
        """
        Si aucun B-Roll n'est présent sur le disque, génère automatiquement une vidéo
        verticale (1080x1920) fluide et moderne via FFmpeg.
        """
        if os.path.exists(default_broll_path) and os.path.getsize(default_broll_path) > 10000:
            return default_broll_path

        os.makedirs(os.path.dirname(default_broll_path), exist_ok=True)
        logger.info(f"Génération d'un B-Roll vertical par défaut vers {default_broll_path}...")

        cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi",
            "-i", (
                "gradients=s=1080x1920:r=24:d=20:c0=0x1e1b4b:c1=0x581c87:c2=0x0f172a:c3=0x3b0764:speed=0.03"
            ),
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-preset", "ultrafast",
            default_broll_path
        ]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if res.returncode != 0:
            cmd_fallback = [
                "ffmpeg", "-y",
                "-f", "lavfi",
                "-i", "color=c=0x1e1b4b:s=1080x1920:r=24:d=20",
                "-vf", "geq=r='30+25*sin(2*PI*(T/4+Y/1920))':g='15+10*cos(2*PI*(T/5+X/1080))':b='65+45*sin(2*PI*(T/3+(X+Y)/3000))'",
                "-c:v", "libx264",
                "-pix_fmt", "yuv420p",
                "-preset", "ultrafast",
                default_broll_path
            ]
            subprocess.run(cmd_fallback, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        logger.info("B-Roll vertical par défaut généré avec succès.")
        return default_broll_path

    @staticmethod
    def load_pil_image(image_source: str):
        """
        Charge une image PIL depuis un chemin local (/app/medias/...) ou une URL HTTP(S).
        """
        if not image_source:
            return None

        try:
            # Cas 1 : Chemin relatif web /medias/...
            if image_source.startswith("/medias/"):
                local_path = os.path.join(Config.WORKSPACE_DIR, image_source[len("/medias/"):])
                if os.path.exists(local_path):
                    return Image.open(local_path).convert("RGBA")

            # Cas 2 : Chemin local direct
            if os.path.exists(image_source):
                return Image.open(image_source).convert("RGBA")

            candidate = os.path.join(Config.WORKSPACE_DIR, image_source.lstrip("/"))
            if os.path.exists(candidate):
                return Image.open(candidate).convert("RGBA")

            # Cas 3 : URL HTTP / HTTPS
            if image_source.startswith("http://") or image_source.startswith("https://"):
                resp = requests.get(
                    image_source,
                    headers={"User-Agent": "Mozilla/5.0"},
                    timeout=10
                )
                resp.raise_for_status()
                return Image.open(io.BytesIO(resp.content)).convert("RGBA")
        except Exception as e:
            logger.warning(f"Impossible de charger l'image produit '{image_source}': {e}")
        return None

    def build_product_showcase_clip(self, image_source: str, product_name: str, duration: float, temp_png_path: str):
        """
        Crée un ImageClip MoviePy mettant en valeur la photo du produit dans un cadre moderne
        arrondi avec bordure lumineuse dans la moitié supérieure de l'écran 9:16.
        """
        pil_img = self.load_pil_image(image_source)
        if pil_img is None:
            return None

        try:
            card_w, card_h = 760, 820
            card = Image.new("RGBA", (card_w, card_h), (0, 0, 0, 0))
            draw = ImageDraw.new(card) if hasattr(ImageDraw, "new") else ImageDraw.Draw(card)

            # Fond de carte sombre semi-transparent avec bordure violette
            draw.rounded_rectangle(
                [(0, 0), (card_w - 1, card_h - 1)],
                radius=40,
                fill=(17, 24, 39, 235),
                outline=(168, 85, 247, 255),
                width=6
            )

            # Redimensionner l'image du produit en carré 680x680 centré
            prod_resized = ImageOps.fit(pil_img.convert("RGB"), (680, 680), method=Image.Resampling.LANCZOS)
            mask = Image.new("L", (680, 680), 0)
            mask_draw = ImageDraw.Draw(mask)
            mask_draw.rounded_rectangle([(0, 0), (680, 680)], radius=28, fill=255)

            card.paste(prod_resized, (40, 40), mask)

            # Bandeau titre produit en bas de la carte
            font_path = Config.SUBTITLE_FONT
            try:
                font = ImageFont.truetype(font_path, 30)
            except Exception:
                font = ImageFont.load_default()

            short_title = (product_name or "Produit Tendance")[:34]
            if len(product_name or "") > 34:
                short_title += "..."

            draw.text(
                (card_w // 2, 765),
                short_title.upper(),
                fill=(255, 255, 255, 255),
                font=font,
                anchor="mm"
            )

            card.save(temp_png_path, "PNG")

            img_clip = (
                ImageClip(temp_png_path)
                .with_position(("center", 160))
                .with_start(0)
                .with_duration(duration)
            )
            return img_clip
        except Exception as e:
            logger.warning(f"Impossible de créer la carte visuelle produit : {e}")
            return None

    def apply_transformations(self, clip):
        """
        Applique un ensemble de transformations aléatoires mais esthétiques (MoviePy 2.x)
        pour rendre le hash visuel de chaque vidéo unique (Anti-Shadowban).
        """
        try:
            effects = []
            if random.choice([True, False]):
                effects.append(vfx.MirrorX())

            lum_factor = random.uniform(0.94, 1.06)
            effects.append(vfx.MultiplyColor(lum_factor))

            if effects:
                clip = clip.with_effects(effects)

            return clip
        except Exception as e:
            logger.error(f"Erreur lors de l'application des transformations: {e}")
            return clip

    def crop_to_vertical(self, clip):
        """
        Recadre la vidéo au format vertical (9:16 - 1080x1920) en centrant l'action.
        """
        try:
            w, h = clip.size
            target_w, target_h = self.target_resolution
            if (w, h) == (target_w, target_h):
                return clip

            target_ratio = target_w / target_h
            clip_ratio = w / h

            if clip_ratio > target_ratio:
                new_w = int(h * target_ratio)
                clip = clip.cropped(x_center=w / 2, width=new_w)
            elif clip_ratio < target_ratio:
                new_h = int(w / target_ratio)
                clip = clip.cropped(y_center=h / 2, height=new_h)

            clip = clip.resized(self.target_resolution)
            return clip
        except Exception as e:
            logger.error(f"Erreur lors du recadrage vertical: {e}")
            raise

    def assemble_video(
        self,
        source_video_path,
        voiceover_path,
        output_path,
        subtitle_clips=None,
        bg_music_path=None,
        product_image_url=None,
        product_name=None
    ):
        """
        Assemble en une seule passe :
        - Vidéo B-Roll (bouclée ou coupée à la durée exacte de la voix-off)
        - Carte visuelle du Produit (si le produit possède une image)
        - Voix-off IA (+ musique de fond optionnelle à volume réduit)
        - Sous-titres dynamiques TikTok
        Retourne (success: bool, duration_seconds: int)
        """
        logger.info(f"Assemblage vidéo depuis la source : {source_video_path}...")
        video_clip = None
        audio_clip = None
        bg_music_clip = None
        product_card_clip = None
        final_clip = None
        temp_card_png = os.path.join(
            os.path.dirname(output_path),
            f"temp_card_{random.randint(1000, 9999)}.png"
        )

        try:
            video_clip = VideoFileClip(source_video_path)
            audio_clip = AudioFileClip(voiceover_path)

            target_duration = max(audio_clip.duration + 0.3, 1.0)

            video_clip = self.apply_transformations(video_clip)
            video_clip = self.crop_to_vertical(video_clip)

            if video_clip.duration < target_duration:
                video_clip = video_clip.with_effects([vfx.Loop(duration=target_duration)])
            else:
                video_clip = video_clip.subclipped(0, target_duration)

            final_audio = audio_clip
            if bg_music_path and os.path.exists(bg_music_path):
                try:
                    bg_music_clip = AudioFileClip(bg_music_path)
                    if bg_music_clip.duration < target_duration:
                        loops = int(target_duration // bg_music_clip.duration) + 1
                        from moviepy import concatenate_audioclips
                        bg_music_clip = concatenate_audioclips([bg_music_clip] * loops)
                    bg_music_clip = bg_music_clip.subclipped(0, target_duration).with_volume_scaled(0.12)
                    final_audio = CompositeAudioClip([bg_music_clip, audio_clip])
                except Exception as music_err:
                    logger.warning(f"Musique de fond ignorée ({music_err}), utilisation de la voix-off seule.")

            video_clip = video_clip.with_audio(final_audio)

            layers = [video_clip]

            # Incrustation de l'image du produit au-dessus du B-Roll si disponible
            if product_image_url:
                product_card_clip = self.build_product_showcase_clip(
                    image_source=product_image_url,
                    product_name=product_name,
                    duration=target_duration,
                    temp_png_path=temp_card_png
                )
                if product_card_clip is not None:
                    logger.info(f"Incrustation de l'image produit : {product_image_url}")
                    layers.append(product_card_clip)

            if subtitle_clips:
                layers.extend(subtitle_clips)

            if len(layers) > 1:
                final_clip = CompositeVideoClip(layers).with_duration(target_duration)
            else:
                final_clip = video_clip

            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            temp_audio = os.path.join(os.path.dirname(output_path), f"temp_audio_{random.randint(1000,9999)}.m4a")

            logger.info(f"Encodage MP4 en cours vers {output_path} ({target_duration:.1f}s)...")
            final_clip.write_videofile(
                output_path,
                codec="libx264",
                audio_codec="aac",
                temp_audiofile=temp_audio,
                remove_temp=True,
                fps=24,
                threads=4,
                preset="ultrafast",
                ffmpeg_params=["-pix_fmt", "yuv420p"],
                logger=None
            )

            logger.info("Rendu vidéo terminé avec succès !")
            return True, int(round(target_duration))

        except Exception as e:
            logger.error(f"Erreur lors de l'assemblage de la vidéo : {e}")
            raise
        finally:
            for c in (final_clip, product_card_clip, video_clip, audio_clip, bg_music_clip):
                if c is not None:
                    try:
                        c.close()
                    except Exception:
                        pass
            if os.path.exists(temp_card_png):
                try:
                    os.remove(temp_card_png)
                except Exception:
                    pass
