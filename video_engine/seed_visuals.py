import os
import io
import json
import requests
import mysql.connector
from PIL import Image, ImageOps
from config import Config


def download_and_save_photo(url: str, dest_path: str):
    headers = {"User-Agent": "CentifyBot/1.0 (https://centify.local; contact@centify.local)"}
    resp = requests.get(url, headers=headers, timeout=15)
    resp.raise_for_status()
    img = Image.open(io.BytesIO(resp.content)).convert("RGB")
    img = ImageOps.fit(img, (1080, 1350), method=Image.Resampling.LANCZOS)
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    img.save(dest_path, "JPEG", quality=92)
    print(f"Downloaded real photo -> {dest_path}")


def make_4in1_collage(img_paths, output_path):
    collage = Image.new("RGB", (800, 800), (15, 23, 42))
    coords = [(10, 10), (405, 10), (10, 405), (405, 405)]
    for idx, p in enumerate(img_paths[:4]):
        if os.path.exists(p):
            tile = ImageOps.fit(Image.open(p).convert("RGB"), (385, 385), method=Image.Resampling.LANCZOS)
            collage.paste(tile, coords[idx])
    collage.save(output_path, "JPEG", quality=92)


def run():
    lib = Config.LIBRARY_DIR
    os.makedirs(lib, exist_ok=True)

    # 1. Télécharger 4 VRAIES photos HD pour la Brosse / Toilettage Chat (Trend #1 & Product #1)
    cat_urls = [
        ("cat_brush_1.jpg", "https://thumb.wikimedia.org/wikipedia/commons/thumb/0/05/Brushing_a_female_cat%27s_hair_-_panoramio.jpg/1280px-Brushing_a_female_cat%27s_hair_-_panoramio.jpg"),
        ("cat_brush_2.jpg", "https://upload.wikimedia.org/wikipedia/commons/5/5d/Pet_grooming_51.jpg"),
        ("cat_brush_3.jpg", "https://thumb.wikimedia.org/wikipedia/commons/thumb/5/5b/Tabby_cat_relaxing_on_back_of_couch_%2820_03_2011%29.jpg/1280px-Tabby_cat_relaxing_on_back_of_couch_%2820_03_2011%29.jpg"),
        ("cat_brush_4.jpg", "https://thumb.wikimedia.org/wikipedia/commons/thumb/f/f1/Pair_of_domestic_cats_sleeping_on_a_couch_01.jpg/1280px-Pair_of_domestic_cats_sleeping_on_a_couch_01.jpg"),
    ]
    cat_local_paths = []
    for fname, url in cat_urls:
        p = os.path.join(lib, fname)
        download_and_save_photo(url, p)
        cat_local_paths.append(p)

    make_4in1_collage(cat_local_paths, os.path.join(lib, "collage_trend_1.jpg"))

    # 2. Télécharger 4 VRAIES photos HD pour le Projecteur Galaxie (Trend #2)
    astro_urls = [
        ("astro_1.jpg", "https://thumb.wikimedia.org/wikipedia/commons/thumb/4/45/ESO_-_The_Carina_Nebula_%28by%29.jpg/1280px-ESO_-_The_Carina_Nebula_%28by%29.jpg"),
        ("astro_2.jpg", "https://thumb.wikimedia.org/wikipedia/commons/thumb/9/9e/A_New_View_of_the_Tarantula_Nebula.jpg/1280px-A_New_View_of_the_Tarantula_Nebula.jpg"),
        ("astro_3.jpg", "https://thumb.wikimedia.org/wikipedia/commons/thumb/b/b3/Andromeda_Galaxy_M31_-_Heic1502a_Full_resolution.jpg/1280px-Andromeda_Galaxy_M31_-_Heic1502a_Full_resolution.jpg"),
        ("astro_4.jpg", "https://thumb.wikimedia.org/wikipedia/commons/thumb/6/60/Galaxie_d%27Androm%C3%A8de_M31.jpg/1280px-Galaxie_d%27Androm%C3%A8de_M31.jpg"),
    ]
    astro_local_paths = []
    for fname, url in astro_urls:
        p = os.path.join(lib, fname)
        download_and_save_photo(url, p)
        astro_local_paths.append(p)

    make_4in1_collage(astro_local_paths, os.path.join(lib, "collage_trend_2.jpg"))

    # 3. Mise à jour BDD avec la galerie de 4 vraies photos et relance du rendu de la Vidéo #1
    conn = mysql.connector.connect(
        host=os.getenv("DB_HOST", "db"),
        user=os.getenv("DB_USER", "centify_user"),
        password=os.getenv("DB_PASSWORD", "centify_pass"),
        database=os.getenv("DB_NAME", "centify_db")
    )
    cursor = conn.cursor(dictionary=True)

    gallery_json = json.dumps([
        "/medias/library/cat_brush_1.jpg",
        "/medias/library/cat_brush_2.jpg",
        "/medias/library/cat_brush_3.jpg",
        "/medias/library/cat_brush_4.jpg",
    ])

    cursor.execute(
        """
        UPDATE products
        SET image_url = '/medias/library/cat_brush_1.jpg',
            gallery_images = %s,
            updated_at = NOW()
        WHERE id = 1
        """,
        (gallery_json,)
    )

    cursor.execute(
        "UPDATE videos SET status = 'rendering', updated_at = NOW() WHERE id = 1"
    )

    conn.commit()
    cursor.close()
    conn.close()
    print("Real photos downloaded & Video #1 queued for multi-scene dynamic render!")


if __name__ == "__main__":
    run()
