<?php

namespace App\Services;

use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Log;

class ShopifyService
{
    /**
     * Ce service agit comme un pont entre ton Hub Centify et tes boutiques Shopify.
     * Dès que tu auras créé tes boutiques, tu mettras tes clés API dans le Dashboard.
     */
    
    public function __construct(
        protected string $shopDomain,
        protected string $accessToken
    ) {}

    /**
     * Récupère le chiffre d'affaires (CA) du jour.
     */
    public function getDailyRevenue(): float
    {
        // Appel à l'API GraphQL ou REST de Shopify
        $response = Http::withHeaders([
            'X-Shopify-Access-Token' => $this->accessToken,
            'Content-Type' => 'application/json',
        ])->get("https://{$this->shopDomain}/admin/api/2024-01/orders.json", [
            'status' => 'any',
            'created_at_min' => now()->startOfDay()->toIso8601String(),
        ]);

        if ($response->failed()) {
            Log::error("Erreur Shopify API (Revenus): " . $response->body());
            return 0.0;
        }

        $orders = $response->json('orders');
        $total = 0.0;
        
        foreach ($orders as $order) {
            // On additionne le CA des commandes payées
            if (isset($order['financial_status']) && $order['financial_status'] === 'paid') {
                $total += (float) $order['total_price'];
            }
        }

        return $total;
    }

    /**
     * Pousse un produit du Dashboard directement vers ta boutique Shopify.
     * Idéal pour tester une trend trouvée par le Scraper TikTok en 1 clic !
     */
    public function pushProductToShopify(array $productData)
    {
        $response = Http::withHeaders([
            'X-Shopify-Access-Token' => $this->accessToken,
        ])->post("https://{$this->shopDomain}/admin/api/2024-01/products.json", [
            'product' => [
                'title' => $productData['title'],
                'body_html' => $productData['description'],
                'vendor' => 'Centify Auto-Import',
                'product_type' => $productData['niche'],
                'tags' => 'imported, centify',
            ]
        ]);

        return $response->json();
    }
}
