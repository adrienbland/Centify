<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        // ==========================================
        // GESTION DES BOUTIQUES SHOPIFY (MULTI-STORES)
        // ==========================================
        Schema::create('stores', function (Blueprint $table) {
            $table->id();
            $table->string('name');
            $table->string('domain');
            $table->string('shopify_api_key');
            $table->string('shopify_api_secret');
            $table->string('ga4_measurement_id')->nullable();
            $table->decimal('total_revenue', 10, 2)->default(0);
            $table->enum('status', ['active', 'inactive'])->default('active');
            $table->timestamps();
        });

        // ==========================================
        // SYSTÈME DE CATÉGORIES
        // ==========================================
        Schema::create('categories', function (Blueprint $table) {
            $table->id();
            $table->string('name');
            $table->text('description')->nullable();
            $table->text('ai_custom_instructions')->nullable();
            $table->timestamps();
        });

        // ==========================================
        // GESTION DES RESEAUX SOCIAUX (TIKTOK)
        // ==========================================
        Schema::create('social_accounts', function (Blueprint $table) {
            $table->id();
            $table->foreignId('store_id')->constrained('stores')->onDelete('cascade');
            $table->enum('platform', ['tiktok', 'instagram', 'youtube']);
            $table->string('account_name');
            $table->text('access_token');
            $table->text('refresh_token')->nullable();
            $table->string('open_id')->nullable();
            $table->timestamps();
        });

        // ==========================================
        // GESTION DES PRODUITS
        // ==========================================
        Schema::create('products', function (Blueprint $table) {
            $table->id();
            $table->foreignId('store_id')->nullable()->constrained('stores')->onDelete('set null');
            $table->string('shopify_id')->nullable();
            $table->string('name');
            $table->foreignId('category_id')->nullable()->constrained('categories')->onDelete('set null');
            $table->text('description')->nullable();
            $table->text('ai_custom_prompt')->nullable();
            $table->string('niche')->nullable();
            $table->foreignId('default_tiktok_account_id')->nullable()->constrained('social_accounts')->onDelete('set null');
            $table->enum('status', ['testing', 'scaling', 'dead'])->default('testing');
            $table->timestamps();
        });

        // ==========================================
        // SCRIPTS
        // ==========================================
        Schema::create('scripts', function (Blueprint $table) {
            $table->id();
            $table->foreignId('product_id')->constrained('products')->onDelete('cascade');
            $table->text('hook');
            $table->text('body');
            $table->text('cta');
            $table->text('full_text');
            $table->string('ai_model')->default('qwen2.5:7b');
            $table->enum('status', ['draft', 'approved', 'rejected'])->default('draft');
            $table->timestamps();
        });

        // ==========================================
        // VIDEOS
        // ==========================================
        Schema::create('videos', function (Blueprint $table) {
            $table->id();
            $table->foreignId('script_id')->constrained('scripts')->onDelete('cascade');
            $table->foreignId('product_id')->constrained('products')->onDelete('cascade');
            $table->string('file_path');
            $table->integer('duration_seconds')->nullable();
            $table->text('user_feedback')->nullable();
            $table->enum('status', ['rendering', 'ready', 'needs_revision', 'scheduled', 'published', 'failed'])->default('rendering');
            $table->enum('social_network', ['tiktok', 'youtube', 'instagram']);
            $table->dateTime('scheduled_at')->nullable();
            $table->dateTime('published_at')->nullable();
            $table->timestamps();
        });

        // ==========================================
        // SUIVI DES PUBLICATIONS TIKTOK
        // ==========================================
        Schema::create('tiktok_publications', function (Blueprint $table) {
            $table->id();
            $table->foreignId('social_account_id')->constrained('social_accounts')->onDelete('cascade');
            $table->foreignId('video_id')->constrained('videos')->onDelete('cascade');
            $table->string('tiktok_post_id')->nullable();
            $table->text('description')->nullable();
            $table->dateTime('published_at')->nullable();
            $table->integer('views')->default(0);
            $table->integer('likes')->default(0);
            $table->enum('status', ['pending', 'published', 'failed'])->default('pending');
            $table->timestamps();
        });

        // ==========================================
        // TENDANCES SCRAPÉES
        // ==========================================
        Schema::create('trends', function (Blueprint $table) {
            $table->id();
            $table->string('hashtag');
            $table->string('video_url');
            $table->string('views_count');
            $table->text('description')->nullable();
            $table->boolean('is_processed')->default(false);
            $table->timestamps();
        });

        // ==========================================
        // PARAMÈTRES GLOBAUX (SETTINGS)
        // ==========================================
        Schema::create('settings', function (Blueprint $table) {
            $table->id();
            $table->string('setting_key')->unique();
            $table->text('setting_value')->nullable();
            $table->string('description')->nullable();
            $table->timestamps();
        });

        // ==========================================
        // NOTIFICATIONS
        // ==========================================
        Schema::create('notifications', function (Blueprint $table) {
            $table->id();
            $table->string('title');
            $table->text('message');
            $table->enum('type', ['info', 'success', 'warning', 'error', 'ai_advice'])->default('info');
            $table->boolean('is_read')->default(false);
            $table->timestamps();
        });

        // ==========================================
        // LOGS D'ACTIVITÉ
        // ==========================================
        Schema::create('activity_logs', function (Blueprint $table) {
            $table->id();
            $table->string('action');
            $table->text('description')->nullable();
            $table->timestamps();
        });

        // ==========================================
        // MÉDIATHÈQUE GLOBALE
        // ==========================================
        Schema::create('media_library', function (Blueprint $table) {
            $table->id();
            $table->enum('type', ['audio', 'b_roll', 'font', 'transition']);
            $table->string('name');
            $table->string('file_path');
            $table->string('tags')->nullable();
            $table->timestamps();
        });

        // ==========================================
        // HOOK TESTER (A/B TESTING)
        // ==========================================
        Schema::create('video_variants', function (Blueprint $table) {
            $table->id();
            $table->foreignId('video_id')->constrained('videos')->onDelete('cascade');
            $table->text('hook_text');
            $table->string('hook_audio_path')->nullable();
            $table->integer('views')->default(0);
            $table->integer('likes')->default(0);
            $table->decimal('retention_3s', 5, 2)->default(0);
            $table->boolean('is_winner')->default(false);
            $table->timestamps();
        });

        // ==========================================
        // GESTIONNAIRE DE PROXYS
        // ==========================================
        Schema::create('proxies', function (Blueprint $table) {
            $table->id();
            $table->string('ip_address');
            $table->integer('port');
            $table->string('username')->nullable();
            $table->string('password')->nullable();
            $table->enum('status', ['active', 'banned', 'dead'])->default('active');
            $table->dateTime('last_used_at')->nullable();
            $table->timestamps();
        });

        // ==========================================
        // API & WEBHOOK DEBUGGER
        // ==========================================
        Schema::create('api_logs', function (Blueprint $table) {
            $table->id();
            $table->enum('service', ['shopify', 'tiktok', 'ollama', 'system']);
            $table->string('endpoint')->nullable();
            $table->json('payload')->nullable();
            $table->json('response')->nullable();
            $table->integer('status_code')->nullable();
            $table->text('error_message')->nullable();
            $table->timestamps();
        });

        // ==========================================
        // SUIVI DE RENTABILITÉ (COST TRACKER)
        // ==========================================
        Schema::create('expenses', function (Blueprint $table) {
            $table->id();
            $table->foreignId('store_id')->nullable()->constrained('stores')->onDelete('set null');
            $table->enum('category', ['proxy', 'hosting', 'domain', 'apps', 'other']);
            $table->decimal('amount', 10, 2);
            $table->date('date');
            $table->text('description')->nullable();
            $table->timestamps();
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('expenses');
        Schema::dropIfExists('api_logs');
        Schema::dropIfExists('proxies');
        Schema::dropIfExists('video_variants');
        Schema::dropIfExists('media_library');
        Schema::dropIfExists('activity_logs');
        Schema::dropIfExists('notifications');
        Schema::dropIfExists('settings');
        Schema::dropIfExists('trends');
        Schema::dropIfExists('tiktok_publications');
        Schema::dropIfExists('videos');
        Schema::dropIfExists('scripts');
        Schema::dropIfExists('products');
        Schema::dropIfExists('social_accounts');
        Schema::dropIfExists('categories');
        Schema::dropIfExists('stores');
    }
};

