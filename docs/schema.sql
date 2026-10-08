-- ==========================================
-- SCHEMA CONCEPTUEL BASE DE DONNÉES (MySQL/MariaDB)
-- Projet: Centify (Automatisation Dropshipping)
-- ==========================================

CREATE TABLE products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    shopify_id VARCHAR(255) NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    niche VARCHAR(100),
    status ENUM('testing', 'scaling', 'dead') DEFAULT 'testing',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE scripts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    product_id INT NOT NULL,
    hook TEXT NOT NULL,
    body TEXT NOT NULL,
    cta TEXT NOT NULL,
    full_text TEXT NOT NULL,
    ai_model VARCHAR(100) DEFAULT 'qwen2.5:7b',
    status ENUM('draft', 'approved', 'rejected') DEFAULT 'draft',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
);

CREATE TABLE videos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    script_id INT NOT NULL,
    product_id INT NOT NULL,
    file_path VARCHAR(255) NOT NULL,
    duration_seconds INT,
    status ENUM('rendering', 'ready', 'scheduled', 'published', 'failed') DEFAULT 'rendering',
    social_network ENUM('tiktok', 'youtube', 'instagram') NOT NULL,
    scheduled_at DATETIME,
    published_at DATETIME,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (script_id) REFERENCES scripts(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
);


-- ==========================================
-- GESTION DES BOUTIQUES SHOPIFY (MULTI-STORES)
-- ==========================================
CREATE TABLE stores (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    domain VARCHAR(255) NOT NULL,
    shopify_api_key VARCHAR(255) NOT NULL,
    shopify_api_secret VARCHAR(255) NOT NULL,
    ga4_measurement_id VARCHAR(255) NULL,
    status ENUM('active', 'inactive') DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Lier les produits aux boutiques
ALTER TABLE products ADD COLUMN store_id INT NULL AFTER id;
ALTER TABLE products ADD FOREIGN KEY (store_id) REFERENCES stores(id) ON DELETE SET NULL;

-- ==========================================
-- GESTION DES TENDANCES SCRAPÉES
-- ==========================================
CREATE TABLE trends (
    id INT AUTO_INCREMENT PRIMARY KEY,
    hashtag VARCHAR(100) NOT NULL,
    video_url VARCHAR(255) NOT NULL,
    views_count VARCHAR(50) NOT NULL,
    description TEXT,
    is_processed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ==========================================
-- GESTION DES RESEAUX SOCIAUX (TIKTOK)
-- ==========================================
CREATE TABLE social_accounts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    store_id INT NOT NULL,
    platform ENUM('tiktok', 'instagram', 'youtube') NOT NULL,
    account_name VARCHAR(255) NOT NULL,
    access_token VARCHAR(500) NOT NULL,
    refresh_token VARCHAR(500) NULL,
    open_id VARCHAR(255) NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (store_id) REFERENCES stores(id) ON DELETE CASCADE
);

-- Suivi des vidéos publiées depuis le Hub
CREATE TABLE tiktok_publications (
    id INT AUTO_INCREMENT PRIMARY KEY,
    social_account_id INT NOT NULL,
    video_id INT NOT NULL, -- Référence à la table videos
    tiktok_post_id VARCHAR(255) NULL,
    description TEXT,
    published_at DATETIME,
    views INT DEFAULT 0,
    likes INT DEFAULT 0,
    status ENUM('pending', 'published', 'failed') DEFAULT 'pending',
    FOREIGN KEY (social_account_id) REFERENCES social_accounts(id) ON DELETE CASCADE,
    FOREIGN KEY (video_id) REFERENCES videos(id) ON DELETE CASCADE
);

-- ==========================================
-- PARAMÈTRES GLOBAUX (SETTINGS)
-- ==========================================
CREATE TABLE settings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    setting_key VARCHAR(255) UNIQUE NOT NULL,
    setting_value TEXT NULL,
    description VARCHAR(255) NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Exemples d'insertion par défaut pour les paramètres modifiables depuis le Hub
INSERT INTO settings (setting_key, setting_value, description) VALUES
('ollama_url', 'http://host.docker.internal:11434/api/generate', 'URL API du serveur Ollama local'),
('ollama_model', 'qwen2.5:7b', 'Modèle IA utilisé pour la génération des scripts'),
('tts_voice', 'fr-FR-HenriNeural', 'Voix Edge-TTS pour les vidéos'),
('video_speed_min', '0.95', 'Vitesse minimum aléatoire pour anti-shadowban'),
('video_speed_max', '1.05', 'Vitesse maximum aléatoire pour anti-shadowban');

-- ==========================================
-- SYSTÈME DE CATÉGORIES
-- ==========================================
CREATE TABLE categories (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    ai_custom_instructions TEXT NULL -- Instructions par défaut pour l'IA dans cette catégorie
);
ALTER TABLE products ADD COLUMN category_id INT NULL AFTER name;
ALTER TABLE products ADD FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE SET NULL;

-- ==========================================
-- REFINEMENTS PRODUITS ET COMPTES SOCIAUX
-- ==========================================
ALTER TABLE products ADD COLUMN ai_custom_prompt TEXT NULL AFTER description; -- Instructions spécifiques de l'utilisateur à l'IA
ALTER TABLE products ADD COLUMN default_tiktok_account_id INT NULL AFTER store_id; -- Lier un produit à un compte TikTok spécifique
ALTER TABLE products ADD FOREIGN KEY (default_tiktok_account_id) REFERENCES social_accounts(id) ON DELETE SET NULL;

-- ==========================================
-- REFINEMENTS VIDÉOS (FEEDBACK ET RETOUCHES)
-- ==========================================
ALTER TABLE videos ADD COLUMN user_feedback TEXT NULL AFTER duration_seconds; -- Retours de l'utilisateur pour refaire la vidéo
ALTER TABLE videos MODIFY COLUMN status ENUM('rendering', 'ready', 'needs_revision', 'scheduled', 'published', 'failed') DEFAULT 'rendering';

-- ==========================================
-- NOTIFICATIONS ET HISTORIQUE (LOGS)
-- ==========================================
CREATE TABLE notifications (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    type ENUM('info', 'success', 'warning', 'error', 'ai_advice') DEFAULT 'info',
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE activity_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    action VARCHAR(255) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
