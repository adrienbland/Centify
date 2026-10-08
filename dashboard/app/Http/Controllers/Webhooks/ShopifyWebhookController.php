<?php

namespace App\Http\Controllers\Webhooks;

use App\Http\Controllers\Controller;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Log;

class ShopifyWebhookController extends Controller
{
    /**
     * Reçoit les webhooks en temps réel depuis Shopify.
     * Dès qu'un client achète sur l'une de tes boutiques, ce code s'exécute.
     */
    public function handleOrderCreation(Request $request)
    {
        // 1. Vérification de sécurité HMAC (pour être sûr que ça vient bien de Shopify)
        // $this->verifyShopifyHmac($request);
        
        $payload = $request->all();
        
        $orderId = $payload['id'] ?? null;
        $totalPrice = $payload['total_price'] ?? 0;
        $shopDomain = $request->header('X-Shopify-Shop-Domain');

        // 2. Logique de Dashboard (Mise à jour du CA en temps réel)
        Log::info("🎉 Nouvelle vente détectée sur la boutique {$shopDomain} ! Montant: {$totalPrice} €");
        
        // TODO: Insérer dans la base de données (Table Orders ou Analytics)
        // Order::create([...]);
        
        return response()->json(['status' => 'Webhook traité avec succès'], 200);
    }
}
