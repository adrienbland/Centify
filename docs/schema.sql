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
