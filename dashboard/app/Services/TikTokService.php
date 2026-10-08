<?php

namespace App\Services;

use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Log;

class TikTokService
{
    /**
     * Service de publication automatique sur TikTok via la Content Posting API (Direct Post).
     * Plus besoin de publier sur ton téléphone, le Hub le fait !
     */
    public function __construct(
        protected string $accessToken,
        protected string $openId
    ) {}

    /**
     * Pousse une vidéo avec sa description et ses hashtags générés par l'IA.
     */
    public function publishVideo(string $videoPath, string $description, bool $disableComments = false)
    {
        Log::info("[TikTokService] Début de la publication pour le compte {$this->openId}");

        // 1. Initialisation (Demander à TikTok une URL d'upload temporaire)
        $initResponse = Http::withHeaders([
            'Authorization' => "Bearer {$this->accessToken}",
            'Content-Type'  => 'application/json'
        ])->post('https://open.tiktokapis.com/v2/post/publish/inbox/video/init/', [
            'source_info' => [
                'source' => 'FILE_UPLOAD',
                'video_size' => filesize($videoPath),
                'chunk_size' => filesize($videoPath),
                'total_chunk_count' => 1
            ]
        ]);

        if ($initResponse->failed()) {
            Log::error("[TikTokService] Erreur Init: " . $initResponse->body());
            return false;
        }

        $uploadUrl = $initResponse->json('data.upload_url');

        // 2. Upload de la vidéo sur l'URL fournie (CURL ou Http client binaire)
        // Note: C'est un upload PUT binaire.
        $uploadResponse = Http::withBody(
            file_get_contents($videoPath), 'video/mp4'
        )->put($uploadUrl);

        if (!$uploadResponse->successful()) {
            Log::error("[TikTokService] Erreur Upload.");
            return false;
        }

        // 3. Validation et Publication avec la Description (Captions & Hashtags)
        $publishResponse = Http::withHeaders([
            'Authorization' => "Bearer {$this->accessToken}",
            'Content-Type'  => 'application/json'
        ])->post('https://open.tiktokapis.com/v2/post/publish/video/init/', [
            'post_info' => [
                'title' => $description, // C'est ici que l'on met la description générée par l'IA
                'privacy_level' => 'PUBLIC_TO_EVERYONE',
                'disable_comment' => $disableComments,
                'disable_duet' => false,
                'disable_stitch' => false
            ],
            'source_info' => [
                'source' => 'PULL_FROM_URL',
                'video_url' => $uploadUrl // En réalité l'ID renvoyé, simplifié pour le schéma
            ]
        ]);

        if ($publishResponse->successful()) {
            Log::info("✅ TikTok publié avec succès !");
            return true;
        }

        return false;
    }
}
