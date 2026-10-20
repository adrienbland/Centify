import os
import io
import json
import math
import random
import subprocess
import numpy as np
import requests
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageFilter
from moviepy import VideoClip, VideoFileClip, AudioFileClip, CompositeAudioClip, vfx
from config import Config
from logger import setup_logger

logger = setup_logger("VideoProcessor")


class VideoProcessor:
    """
    Moteur de rendu vidéo TikTok / Shorts Haute Conversion (MoviePy 2.x + NumPy/PIL).
    Génère un montage dynamique multi-scènes plein écran 9:16 :
    - Changements d'angles / photos toutes les 2.8 secondes
    - Mouvements de caméra continus (Ken Burns Zoom-In, Zoom-Out, Panoramique)
    - Transitions Flash / Punch entre chaque scène
    - Sticker Hook natif TikTok (3.5 premières secondes) + Badge CTA final
    - Sous-titres dynamiques avec fond contrasté en une seule passe ultra-rapide (~8s).
    """
    def __init__(self):
        self.target_resolution = Config.TARGET_RESOLUTION
        self.font_path = Config.SUBTITLE_FONT
        if not os.path.exists(self.font_path):
            self.font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

    def _get_font(self, size: int):
        try:
            return ImageFont.truetype(self.font_path, size)
        except Exception:
            return ImageFont.load_default()

    @staticmethod
    def ensure_default_broll(default_broll_path):
        if os.path.exists(default_broll_path) and os.path.getsize(default_broll_path) > 10000:
            return default_broll_path

        os.makedirs(os.path.dirname(default_broll_path), exist_ok=True)
        cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi",
            "-i", "color=c=0x1e1b4b:s=1080x1920:r=24:d=20",
            "-vf", "geq=r='30+25*sin(2*PI*(T/4+Y/1920))':g='15+10*cos(2*PI*(T/5+X/1080))':b='65+45*sin(2*PI*(T/3+(X+Y)/3000))'",
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-preset", "ultrafast",
            default_broll_path
        ]
        subprocess.run(cmd, check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return default_broll_path

    @staticmethod
    def load_pil_image(image_source: str):
        if not image_source:
            return None
        try:
            if image_source.startswith("/medias/"):
                local_path = os.path.join(Config.WORKSPACE_DIR, image_source[len("/medias/"):])
                if os.path.exists(local_path):
                    return Image.open(local_path).convert("RGB")

            if os.path.exists(image_source):
                return Image.open(image_source).convert("RGB")

            candidate = os.path.join(Config.WORKSPACE_DIR, image_source.lstrip("/"))
            if os.path.exists(candidate):
                return Image.open(candidate).convert("RGB")

            if image_source.startswith("http://") or image_source.startswith("https://"):
                resp = requests.get(
                    image_source,
                    headers={"User-Agent": "CentifyBot/1.0 (Mozilla/5.0)"},
                    timeout=10
                )
                resp.raise_for_status()
                return Image.open(io.BytesIO(resp.content)).convert("RGB")
        except Exception as e:
            logger.warning(f"Impossible de charger l'image '{image_source}': {e}")
        return None

    def _prepare_overscan_scenes(self, pil_images: list, product_name: str):
        """
        Prépare 4 canevas plein écran 9:16 en overscan (1350x2400) pour permettre
        des mouvements fluides de caméra (Zoom & Pan) sans aucune bordure vide.
        Si une seule image est fournie, génère 4 cadrages variés (Large, Zoom Détail, Haut, Bas).
        """
        overscan_w, overscan_h = 1350, 2400

        if len(pil_images) == 1:
            base = pil_images[0]
            bw, bh = base.size
            pil_images = [
                base,
                base.crop((int(bw * 0.12), int(bh * 0.12), int(bw * 0.88), int(bh * 0.88))),
                base.crop((0, 0, int(bw * 0.85), int(bh * 0.85))),
                base.crop((int(bw * 0.15), int(bh * 0.15), bw, bh)),
            ]

        scene_badges = [
            ("TENDANCE TIKTOK #1", (220, 38, 38)),
            ("ACTION IMMEDIATE", (147, 51, 234)),
            ("QUALITE PREMIUM", (37, 99, 235)),
            ("OFFRE LIMITEE -50%", (22, 163, 74)),
        ]

        scenes_np = []
        for idx, img in enumerate(pil_images[:6]):
            # 1. Fond plein écran flouté et assombri (Ambilight immersif)
            bg = ImageOps.fit(img, (overscan_w, overscan_h), method=Image.Resampling.BILINEAR)
            bg = bg.filter(ImageFilter.GaussianBlur(radius=28))
            enhancer_dark = Image.new("RGB", (overscan_w, overscan_h), (10, 10, 18))
            bg = Image.blend(bg, enhancer_dark, alpha=0.45)

            # 2. Image principale grand format (1220x1620) au centre avec coins arrondis
            fg_w, fg_h = 1220, 1620
            fg = ImageOps.fit(img, (fg_w, fg_h), method=Image.Resampling.LANCZOS)

            mask = Image.new("L", (fg_w, fg_h), 0)
            mask_draw = ImageDraw.Draw(mask)
            mask_draw.rounded_rectangle([(0, 0), (fg_w - 1, fg_h - 1)], radius=48, fill=255)

            paste_x = (overscan_w - fg_w) // 2
            paste_y = 340
            bg.paste(fg, (paste_x, paste_y), mask)

            # Bordure lumineuse subtile autour de la photo
            draw = ImageDraw.Draw(bg)
            draw.rounded_rectangle(
                [(paste_x, paste_y), (paste_x + fg_w - 1, paste_y + fg_h - 1)],
                radius=48,
                outline=(255, 255, 255),
                width=5
            )

            # Petit badge d'angle dynamique sur la photo
            badge_label, badge_color = scene_badges[idx % len(scene_badges)]
            font_badge = self._get_font(34)
            draw.rounded_rectangle(
                [(paste_x + 40, paste_y + 40), (paste_x + 520, paste_y + 115)],
                radius=24,
                fill=badge_color
            )
            draw.text(
                (paste_x + 280, paste_y + 77),
                badge_label,
                fill=(255, 255, 255),
                font=font_badge,
                anchor="mm"
            )

            scenes_np.append(np.array(bg, dtype=np.uint8))

        return scenes_np

    def _render_top_hook_overlay(self, product_name: str, hook_text: str):
        """
        Crée le sticker blanc/rouge typique des vidéos virales TikTok affiché pendant les 3.5 premières secondes.
        """
        w, h = 960, 230
        img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Carte blanche arrondie avec ombre
        draw.rounded_rectangle([(8, 28), (w - 8, h - 8)], radius=34, fill=(255, 255, 255, 245))
        # Bandeau rouge supérieur "VIRAL SUR TIKTOK"
        draw.rounded_rectangle([(260, 4), (w - 260, 56)], radius=18, fill=(239, 68, 68, 255))

        font_tag = self._get_font(26)
        font_hook = self._get_font(34)

        draw.text((w // 2, 30), "VIRAL SUR TIKTOK", fill=(255, 255, 255, 255), font=font_tag, anchor="mm")

        # Découper le hook ou le nom du produit sur 2 lignes max
        clean_hook = (hook_text or product_name or "Découvre cette pépite !").strip()
        words = clean_hook.split()
        line1 = " ".join(words[:6])
        line2 = " ".join(words[6:12])
        if len(words) > 12:
            line2 += " !"

        if line2:
            draw.text((w // 2, 108), line1, fill=(15, 23, 42, 255), font=font_hook, anchor="mm")
            draw.text((w // 2, 162), line2, fill=(15, 23, 42, 255), font=font_hook, anchor="mm")
        else:
            draw.text((w // 2, 135), line1, fill=(15, 23, 42, 255), font=font_hook, anchor="mm")

        return np.array(img, dtype=np.uint8)

    def _render_cta_overlay(self):
        """
        Crée le bandeau d'appel à l'action affiché pendant les 3.8 dernières secondes.
        """
        w, h = 920, 130
        img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        draw.rounded_rectangle([(0, 0), (w - 1, h - 1)], radius=32, fill=(22, 163, 74, 245), outline=(255, 255, 255, 255), width=4)
        font_cta = self._get_font(38)
        draw.text((w // 2, h // 2), "OFFRE -50% AUJOURD'HUI • LIEN EN BIO", fill=(255, 255, 255, 255), font=font_cta, anchor="mm")
        return np.array(img, dtype=np.uint8)

    def _render_subtitle_chunk_rgba(self, text: str, is_yellow: bool):
        """
        Pré-rend un carton de sous-titre en RGBA (fond pilule sombre semi-transparent + texte gras contouré).
        """
        w, h = 980, 200
        img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        font = self._get_font(68)
        text_color = (255, 215, 0, 255) if is_yellow else (255, 255, 255, 255)

        # Mesurer le texte pour ajuster la pilule de fond
        bbox = draw.textbbox((w // 2, h // 2), text, font=font, anchor="mm", stroke_width=6)
        pad_x, pad_y = 38, 24
        box_x1 = max(10, bbox[0] - pad_x)
        box_y1 = max(10, bbox[1] - pad_y)
        box_x2 = min(w - 10, bbox[2] + pad_x)
        box_y2 = min(h - 10, bbox[3] + pad_y)

        draw.rounded_rectangle(
            [(box_x1, box_y1), (box_x2, box_y2)],
            radius=28,
            fill=(10, 10, 20, 195),
            outline=(168, 85, 247, 180),
            width=3
        )

        draw.text(
            (w // 2, h // 2),
            text,
            font=font,
            fill=text_color,
            stroke_fill=(0, 0, 0, 255),
            stroke_width=6,
            anchor="mm"
        )
        return np.array(img, dtype=np.uint8)

    @staticmethod
    def _alpha_paste(frame_rgb: np.ndarray, overlay_rgba: np.ndarray, x: int, y: int):
        """
        Incrustation alpha ultra-rapide en NumPy.
        """
        oh, ow = overlay_rgba.shape[:2]
        fh, fw = frame_rgb.shape[:2]

        if x < 0 or y < 0 or x + ow > fw or y + oh > fh:
            return frame_rgb

        roi = frame_rgb[y:y + oh, x:x + ow].astype(np.float32)
        fg = overlay_rgba[:, :, :3].astype(np.float32)
        alpha = (overlay_rgba[:, :, 3:4].astype(np.float32)) / 255.0

        blended = roi * (1.0 - alpha) + fg * alpha
        frame_rgb[y:y + oh, x:x + ow] = blended.astype(np.uint8)
        return frame_rgb

    def assemble_video(
        self,
        source_video_path,
        voiceover_path,
        output_path,
        subtitle_chunks=None,
        bg_music_path=None,
        product_image_url=None,
        gallery_images=None,
        product_name=None,
        hook_text=None
    ):
        """
        Assemble la vidéo finale 9:16 (1080x1920) avec :
        - Montage multi-scènes animé (Zoom Ken Burns, Panoramique, Transitions Flash toutes les 2.8s)
        - Sticker Hook TikTok en haut + Badge CTA final
        - Sous-titres dynamiques synchronisés
        - Voix-off IA + musique de fond optionnelle
        """
        audio_clip = None
        bg_music_clip = None
        final_clip = None

        try:
            audio_clip = AudioFileClip(voiceover_path)
            target_duration = max(audio_clip.duration + 0.3, 1.0)

            # Collecter toutes les images disponibles du produit
            image_sources = []
            if gallery_images:
                if isinstance(gallery_images, str):
                    try:
                        gallery_images = json.loads(gallery_images)
                    except Exception:
                        gallery_images = [gallery_images]
                if isinstance(gallery_images, list):
                    image_sources.extend([img for img in gallery_images if img])

            if product_image_url and product_image_url not in image_sources:
                image_sources.insert(0, product_image_url)

            loaded_images = []
            for src in image_sources:
                pil_im = self.load_pil_image(src)
                if pil_im is not None:
                    loaded_images.append(pil_im)

            target_w, target_h = self.target_resolution

            # Pré-rendre les sous-titres en RGBA (ultra-rapide)
            prepared_subtitles = []
            for idx, ch in enumerate(subtitle_chunks or []):
                rgba = self._render_subtitle_chunk_rgba(ch["text"], is_yellow=(idx % 2 == 0))
                prepared_subtitles.append({
                    "start": ch["start"],
                    "end": ch["end"],
                    "rgba": rgba
                })

            hook_overlay = self._render_top_hook_overlay(product_name, hook_text)
            cta_overlay = self._render_cta_overlay()

            if loaded_images:
                logger.info(f"Création d'un montage dynamique multi-scènes avec {len(loaded_images)} photo(s) produit...")
                scenes_np = self._prepare_overscan_scenes(loaded_images, product_name)
                scene_duration = 2.8  # Changement de plan dynamique toutes les 2.8 secondes

                def make_frame(t):
                    scene_idx = int(t // scene_duration) % len(scenes_np)
                    local_t = t % scene_duration
                    progress = local_t / scene_duration  # 0.0 -> 1.0

                    canvas = scenes_np[scene_idx]  # (2400, 1350, 3)
                    ch_h, ch_w = canvas.shape[:2]

                    # 4 mouvements de caméra alternés (Zoom-In, Pan Droite, Zoom-Out, Pan Gauche + Zoom)
                    motion_type = scene_idx % 4
                    if motion_type == 0:
                        # Zoom-In progressif au centre
                        scale = 1.0 - 0.16 * progress
                        cx, cy = ch_w / 2, ch_h / 2
                    elif motion_type == 1:
                        # Panoramique Gauche -> Droite
                        scale = 0.84
                        cx = (ch_w * 0.44) + (ch_w * 0.12) * progress
                        cy = ch_h / 2
                    elif motion_type == 2:
                        # Zoom-Out dynamique
                        scale = 0.82 + 0.16 * progress
                        cx, cy = ch_w / 2, ch_h / 2
                    else:
                        # Panoramique Haut -> Bas + léger Zoom
                        scale = 0.88 - 0.06 * progress
                        cx = ch_w / 2
                        cy = (ch_h * 0.45) + (ch_h * 0.10) * progress

                    crop_w = int(target_w * scale)
                    crop_h = int(target_h * scale)
                    x1 = max(0, min(ch_w - crop_w, int(cx - crop_w / 2)))
                    y1 = max(0, min(ch_h - crop_h, int(cy - crop_h / 2)))

                    cropped = canvas[y1:y1 + crop_h, x1:x1 + crop_w]
                    frame = np.array(
                        Image.fromarray(cropped).resize((target_w, target_h), Image.Resampling.BILINEAR),
                        dtype=np.uint8
                    )

                    # Transition Flash blanc au changement de plan (0.15s)
                    if t > 0.1 and local_t < 0.15:
                        flash_intensity = (1.0 - (local_t / 0.15)) * 0.55
                        frame = np.clip(frame.astype(np.float32) + 255.0 * flash_intensity, 0, 255).astype(np.uint8)

                    # Sticker Hook TikTok pendant les 3.5 premières secondes
                    if t <= 3.5:
                        self._alpha_paste(frame, hook_overlay, (target_w - hook_overlay.shape[1]) // 2, 95)
                    # Bandeau CTA pendant les 3.8 dernières secondes
                    elif t >= max(3.6, target_duration - 3.8):
                        self._alpha_paste(frame, cta_overlay, (target_w - cta_overlay.shape[1]) // 2, 120)

                    # Sous-titre actif à l'instant t
                    for sub in prepared_subtitles:
                        if sub["start"] <= t <= sub["end"]:
                            sub_rgba = sub["rgba"]
                            sx = (target_w - sub_rgba.shape[1]) // 2
                            sy = int(target_h * 0.72)
                            self._alpha_paste(frame, sub_rgba, sx, sy)
                            break

                    return frame

                final_clip = VideoClip(make_frame, duration=target_duration)
            else:
                # Fallback B-Roll vidéo si aucune image n'est disponible
                base_clip = VideoFileClip(source_video_path)
                if base_clip.duration < target_duration:
                    base_clip = base_clip.with_effects([vfx.Loop(duration=target_duration)])
                else:
                    base_clip = base_clip.subclipped(0, target_duration)
                final_clip = base_clip

            # Mixage audio : Voix-off + Musique de fond optionnelle
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
                    logger.warning(f"Musique de fond ignorée ({music_err}).")

            final_clip = final_clip.with_audio(final_audio)

            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            temp_audio = os.path.join(os.path.dirname(output_path), f"temp_audio_{random.randint(1000,9999)}.m4a")

            logger.info(f"Encodage MP4 multi-scènes rapide vers {output_path} ({target_duration:.1f}s)...")
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

            logger.info("Rendu vidéo multi-scènes terminé avec succès !")
            return True, int(round(target_duration))

        except Exception as e:
            logger.error(f"Erreur lors de l'assemblage de la vidéo : {e}")
            raise
        finally:
            for c in (final_clip, audio_clip, bg_music_clip):
                if c is not None:
                    try:
                        c.close()
                    except Exception:
                        pass
