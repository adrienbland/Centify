import os
import mysql.connector
from PIL import Image, ImageDraw, ImageFont
from config import Config

def draw_product_photo(path, bg_colors, title, subtitle, price_tag, badge_text):
    w, h = 800, 800
    img = Image.new("RGB", (w, h), bg_colors[0])
    draw = ImageDraw.Draw(img)

    # Dégradé vertical moderne
    for y in range(h):
        ratio = y / h
        r = int(bg_colors[0][0] * (1 - ratio) + bg_colors[1][0] * ratio)
        g = int(bg_colors[0][1] * (1 - ratio) + bg_colors[1][1] * ratio)
        b = int(bg_colors[0][2] * (1 - ratio) + bg_colors[1][2] * ratio)
        draw.line([(0, y), (w, y)], fill=(r, g, b))

    # Cercle lumineux central mettant en valeur le produit
    draw.ellipse([(150, 140), (650, 640)], fill=(255, 255, 255, 30), outline=(255, 255, 255), width=5)
    draw.rounded_rectangle([(230, 220), (570, 560)], radius=55, fill=(255, 255, 255), outline=(168, 85, 247), width=8)

    font_path = Config.SUBTITLE_FONT
    try:
        font_lg = ImageFont.truetype(font_path, 44)
        font_md = ImageFont.truetype(font_path, 30)
        font_sm = ImageFont.truetype(font_path, 24)
    except Exception:
        font_lg = font_md = font_sm = ImageFont.load_default()

    # Illustration stylisée au centre
    draw.text((400, 355), title.upper(), fill=(30, 27, 75), font=font_lg, anchor="mm")
    draw.text((400, 425), subtitle, fill=(107, 33, 168), font=font_md, anchor="mm")

    # Badge Prix en bas à droite
    draw.rounded_rectangle([(480, 480), (555, 540)], radius=16, fill=(22, 163, 74))
    draw.text((517, 510), price_tag, fill=(255, 255, 255), font=font_sm, anchor="mm")

    # Bandeau supérieur
    draw.rounded_rectangle([(60, 45), (740, 115)], radius=22, fill=(15, 23, 42))
    draw.text((400, 80), badge_text.upper(), fill=(250, 204, 21), font=font_md, anchor="mm")

    # Bandeau inférieur
    draw.rounded_rectangle([(60, 675), (740, 755)], radius=22, fill=(15, 23, 42))
    draw.text((400, 715), f"{title} - {subtitle}", fill=(255, 255, 255), font=font_md, anchor="mm")

    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.save(path, "JPEG", quality=92)


def make_4in1_collage(img_paths, output_path):
    collage = Image.new("RGB", (800, 800), (15, 23, 42))
    coords = [(10, 10), (405, 10), (10, 405), (405, 405)]
    for idx, p in enumerate(img_paths[:4]):
        if os.path.exists(p):
            tile = Image.open(p).resize((385, 385), Image.Resampling.LANCZOS)
            collage.paste(tile, coords[idx])
    collage.save(output_path, "JPEG", quality=92)


def run():
    lib = Config.LIBRARY_DIR
    os.makedirs(lib, exist_ok=True)

    # 1. Générer 4 visuels pour la Brosse Vapeur Chat (Trend #1)
    cat_imgs = [
        (os.path.join(lib, "cat_brush_1.jpg"), ((88, 28, 135), (30, 27, 75)), "Brosse Vapeur", "Silicone & Brume 3-en-1", "$4.50", "Best-Seller 12.5k Ventes"),
        (os.path.join(lib, "cat_brush_2.jpg"), ((49, 46, 129), (15, 23, 42)), "Pet Steam Brush", "Anti-Poils Morts USB-C", "$2.99", "8.4k Commandes"),
        (os.path.join(lib, "cat_brush_3.jpg"), ((112, 26, 117), (30, 27, 75)), "Peigne Massage", "Picots Doux + LED", "$5.10", "3.2k Commandes"),
        (os.path.join(lib, "cat_brush_4.jpg"), ((15, 118, 110), (15, 23, 42)), "Brosse Auto-Nett.", "Bouton Ejection 1-Clic", "$3.80", "6.1k Commandes"),
    ]
    for p, col, t, sub, pr, b in cat_imgs:
        draw_product_photo(p, col, t, sub, pr, b)

    make_4in1_collage([x[0] for x in cat_imgs], os.path.join(lib, "collage_trend_1.jpg"))

    # 2. Générer 4 visuels pour le Projecteur Galaxie Astronaute (Trend #2)
    astro_imgs = [
        (os.path.join(lib, "astro_1.jpg"), ((30, 58, 138), (15, 23, 42)), "Astro Galaxie", "Projecteur Nébuleuse HD", "$6.20", "Viral 24k Ventes"),
        (os.path.join(lib, "astro_2.jpg"), ((76, 29, 149), (9, 9, 11)), "Astronaute Pro", "Télécommande + Timer", "$5.40", "15k Commandes"),
        (os.path.join(lib, "astro_3.jpg"), ((19, 78, 74), (15, 23, 42)), "Mini Astro LED", "Tête Magnétique 360°", "$4.90", "9.8k Commandes"),
        (os.path.join(lib, "astro_4.jpg"), ((124, 45, 18), (24, 24, 27)), "Astro Bluetooth", "Enceinte + Ciel Étoilé", "$8.50", "4.3k Commandes"),
    ]
    for p, col, t, sub, pr, b in astro_imgs:
        draw_product_photo(p, col, t, sub, pr, b)

    make_4in1_collage([x[0] for x in astro_imgs], os.path.join(lib, "collage_trend_2.jpg"))

    # 3. Mise à jour de la Base de Données
    conn = mysql.connector.connect(
        host=os.getenv("DB_HOST", "db"),
        user=os.getenv("DB_USER", "centify_user"),
        password=os.getenv("DB_PASSWORD", "centify_pass"),
        database=os.getenv("DB_NAME", "centify_db")
    )
    cursor = conn.cursor(dictionary=True)

    # Mettre à jour Trend #1 avec son collage 4-en-1
    cursor.execute(
        "UPDATE trends SET collage_image_path = '/medias/library/collage_trend_1.jpg', extracted_keyword = 'Brosse Vapeur Chat 3-en-1' WHERE id = 1"
    )

    # Mettre à jour les propositions de Trend #1 avec vraies images et fiches techniques
    specs_1 = (
        "• Fonction 3-en-1 : Brossage, brume à vapeur tiède anti-statique et massage doux.\n"
        "• Matériau : Picots arrondis en silicone médical (ne griffe pas la peau du chat ou du chien).\n"
        "• Réservoir intégré : 35ml (eau ou lotion sans rinçage), autonomie 7 jours en USB-C.\n"
        "• Bénéfice client : Élimine 95% des poils morts sur le canapé et détend l'animal."
    )
    cursor.execute("UPDATE trend_proposals SET image_url = '/medias/library/cat_brush_1.jpg', description = %s WHERE id = 1", (specs_1,))
    cursor.execute("UPDATE trend_proposals SET image_url = '/medias/library/cat_brush_2.jpg', description = %s WHERE id = 2", (specs_1,))
    cursor.execute("UPDATE trend_proposals SET image_url = '/medias/library/cat_brush_3.jpg', description = %s WHERE id = 3", (specs_1,))

    # Créer une 2ème Tendance TikTok dans "Nouvelles Tendances" (status = 'new') pour que l'utilisateur puisse tester !
    cursor.execute("SELECT id FROM trends WHERE extracted_keyword LIKE '%Astronaute%' LIMIT 1")
    if not cursor.fetchone():
        cursor.execute(
            """
            INSERT INTO trends (hashtag, video_url, views_count, description, is_processed, extracted_keyword, collage_image_path, status, created_at, updated_at)
            VALUES ('tiktokmademebuyit', 'https://www.tiktok.com/@techgadgets/video/987654', '4.8M',
                    'Ce projecteur astronaute transforme ma chambre en galaxie entière ! #ledlights #roomdecor #tiktokmademebuyit',
                    1, 'Projecteur Galaxie Astronaute LED', '/medias/library/collage_trend_2.jpg', 'new', NOW(), NOW())
            """
        )
        t2_id = cursor.lastrowid
        specs_astro = (
            "• Projection HD 360° : 8 effets de nébuleuses colorées + étoiles laser vertes désactivables.\n"
            "• Tête magnétique : Rotation libre à 360° pour projeter au plafond ou sur les murs.\n"
            "• Télécommande incluse : Réglage de la luminosité, vitesse de rotation et minuterie d'extinction auto (45 ou 90 min).\n"
            "• Alimentation : Câble USB standard inclus."
        )
        proposals_t2 = [
            (t2_id, "https://aliexpress.com/item/101", "Projecteur Galaxie Astronaute LED 360° HD + Télécommande", specs_astro, 6.20, 24300, "/medias/library/astro_1.jpg"),
            (t2_id, "https://aliexpress.com/item/102", "Lampe Nébuleuse Ciel Étoilé Astronaute Magnétique Timer", specs_astro, 5.40, 15100, "/medias/library/astro_2.jpg"),
            (t2_id, "https://aliexpress.com/item/103", "Mini Veilleuse Projecteur Cosmos Astronaute USB", specs_astro, 4.90, 9800, "/medias/library/astro_3.jpg"),
            (t2_id, "https://aliexpress.com/item/104", "Projecteur Astronaute Pro + Enceinte Bluetooth Intégrée", specs_astro, 8.50, 4300, "/medias/library/astro_4.jpg"),
        ]
        for p in proposals_t2:
            cursor.execute(
                """
                INSERT INTO trend_proposals (trend_id, aliexpress_url, title, description, price, orders, image_url, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                """,
                p
            )

    # 4. Mettre à jour Product #1 avec son image et ses vraies spécifications de Brosse pour Chat
    cursor.execute(
        """
        UPDATE products
        SET name = 'Brosse Vapeur 3-en-1 pour Chat & Chien',
            niche = 'Animaux & Toilettage',
            image_url = '/medias/library/cat_brush_1.jpg',
            supplier_url = 'https://aliexpress.com/item/1',
            description = %s,
            updated_at = NOW()
        WHERE id = 1
        """,
        (specs_1,)
    )

    # 5. Mettre à jour Script #4 avec un vrai script TikTok sur la brosse à vapeur pour chat !
    hook = "Tu en as marre de retrouver des poils de chat partout sur ton canapé et tes vêtements noirs ?"
    body = "Cette brosse à vapeur 3 en 1 diffuse une brume douce qui retire 95 pourcent des poils morts en un seul passage. Ses picots en silicone massent ton chat sans jamais lui faire mal et il va adorer ça !"
    cta = "Clique sur le lien en bio pour commander la tienne à moitié prix aujourd'hui !"
    full_text = f"{hook} {body} {cta}"

    cursor.execute(
        """
        UPDATE scripts
        SET hook = %s, body = %s, cta = %s, full_text = %s, status = 'approved', updated_at = NOW()
        WHERE id = 4
        """,
        (hook, body, cta, full_text)
    )

    # 6. Relancer automatiquement le rendu de la Vidéo #1 pour qu'elle intègre la vraie carte produit et le vrai script !
    cursor.execute(
        "UPDATE videos SET status = 'rendering', updated_at = NOW() WHERE id = 1"
    )

    conn.commit()
    cursor.close()
    conn.close()
    print("Seed visuals & DB update complete!")


if __name__ == "__main__":
    run()
