# Centify - Debugging & Logging Strategy

Lors de la phase de développement et de scalabilité, il est crucial d'avoir une observabilité totale du système. Centify implémente une stratégie de logs hybride :

## 1. Logs Applicatifs (Le "Sous-Capot" Laravel)
Tous les crashs systèmes (erreurs PHP, erreurs de syntaxe, timeouts) sont enregistrés dans :
- **Fichier principal :** `dashboard/storage/logs/laravel.log`
- **Niveau de log (`.env`) :** `LOG_LEVEL=debug` pendant le développement.

## 2. API & Webhooks Debugger (Base de données)
Pour surveiller les interactions externes (qui sont souvent la source de 90% des bugs en e-commerce), toutes les requêtes sont interceptées et stockées dans la table `api_logs` de la base de données.
- **Shopify :** Enregistrement des Webhooks (Payload complet de la commande, erreurs de signature).
- **TikTok :** Réponses de l'API lors de l'upload des vidéos (erreurs de format, quotas dépassés).
- **Ollama (Local) :** Requêtes de prompts et erreurs de timeouts si le LLM plante.

## 3. Activity Logs (Audit Utilisateur & IA)
La table `activity_logs` trace les événements métier :
- "Script généré pour le Produit X"
- "Vidéo Y envoyée en file d'attente de rendu"
- "Commentaire IA ajouté par l'utilisateur"

## 4. Video Engine (Python)
Le moteur vidéo Python génère ses propres fichiers de logs détaillés pour chaque étape du rendu :
- Emplacement : `video_engine/logs/` (dossier monté sur le conteneur).
- Fichiers clés :
  - `pipeline.log` : Orchestration globale.
  - `video_processor.log` : Erreurs de rendu MoviePy.
  - `trend_scraper.log` : Blocages Playwright / Captchas TikTok.

## Comment débugger efficacement ?
1. **Un webhook Shopify ne passe pas ?** Regarde l'onglet "API Logs" dans Filament. Le payload JSON brut y sera visible.
2. **Une vidéo TikTok ne se publie pas ?** Vérifie le `status` dans `tiktok_publications`, puis croise avec l'onglet "API Logs".
3. **Le rendu vidéo prend trop de temps ?** Ouvre `video_engine/logs/pipeline.log` pour voir à quelle étape (Whisper, Edge-TTS, MoviePy) le script bloque.

