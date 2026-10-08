<?php

namespace App\Filament\Resources\ProductResource\Pages;

use App\Filament\Resources\ProductResource;
use Filament\Actions;
use Filament\Resources\Pages\EditRecord;

class EditProduct extends EditRecord
{
    protected static string $resource = ProductResource::class;

    protected function getHeaderActions(): array
    {
        return [
            Actions\Action::make('import_url')
                ->label('Écraser depuis URL (Shopify/AliExpress)')
                ->icon('heroicon-o-cloud-arrow-down')
                ->color('info')
                ->form([
                    \Filament\Forms\Components\TextInput::make('url')
                        ->label('URL du produit')
                        ->url()
                        ->required(),
                ])
                ->action(function (array $data) {
                    $url = $data['url'];
                    $name = '';
                    $description = '';
                    
                    try {
                        if (str_contains($url, 'aliexpress.com')) {
                            $html = @file_get_contents($url);
                            if ($html && preg_match('/<title>(.*?)<\/title>/i', $html, $matches)) {
                                $name = explode('|', $matches[1])[0] ?? 'Produit AliExpress';
                                $name = trim(str_replace(['AliExpress', 'Achetez'], '', $name));
                            }
                            $description = "Produit importé depuis AliExpress.\n\n$url";
                        } else {
                            $jsonUrl = strtok($url, '?');
                            if (!str_ends_with($jsonUrl, '.json')) {
                                $jsonUrl .= '.json';
                            }
                            $response = \Illuminate\Support\Facades\Http::timeout(5)->get($jsonUrl);
                            if ($response->successful()) {
                                $product = $response->json('product');
                                if ($product) {
                                    $name = $product['title'] ?? 'Produit Inconnu';
                                    $description = strip_tags($product['body_html'] ?? '');
                                }
                            }
                        }
                    } catch (\Exception $e) {}

                    // Mise à jour directe du modèle
                    if ($name) {
                        $this->record->update([
                            'name' => $name,
                            'description' => $description ?: $this->record->description,
                        ]);
                        // Rafraichir le formulaire
                        $this->fillForm();

                        \Filament\Notifications\Notification::make()
                            ->title('Produit scrapé et mis à jour')
                            ->success()
                            ->send();
                    }
                }),
            Actions\DeleteAction::make(),
        ];
    }
}
