<?php

namespace App\Filament\Resources\ProductResource\Pages;

use App\Filament\Resources\ProductResource;
use Filament\Actions;
use Filament\Resources\Pages\CreateRecord;

class CreateProduct extends CreateRecord
{
    protected static string $resource = ProductResource::class;

    protected function getHeaderActions(): array
    {
        return [
            Actions\Action::make('import_url')
                ->label('Scraper depuis URL (Shopify/AliExpress)')
                ->icon('heroicon-o-cloud-arrow-down')
                ->color('info')
                ->form([
                    \Filament\Forms\Components\TextInput::make('url')
                        ->label('URL du produit')
                        ->url()
                        ->required()
                        ->placeholder('https://maboutique.com/products/mon-super-produit'),
                ])
                ->action(function (array $data) {
                    $url = $data['url'];
                    $name = '';
                    $description = '';
                    
                    try {
                        // Logique basique de scraping
                        if (str_contains($url, 'aliexpress.com')) {
                            // Scraper le title tag via file_get_contents
                            $html = @file_get_contents($url);
                            if ($html && preg_match('/<title>(.*?)<\/title>/i', $html, $matches)) {
                                $name = explode('|', $matches[1])[0] ?? 'Produit AliExpress';
                                $name = trim(str_replace(['AliExpress', 'Achetez'], '', $name));
                            }
                            $description = "Produit importé depuis AliExpress.\n\n$url";
                        } else {
                            // Supposition: C'est un site Shopify
                            // On ajoute .json à la fin si pas présent
                            $jsonUrl = strtok($url, '?'); // enlever query string
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
                            } else {
                                // Fallback basique title tag
                                $html = @file_get_contents($url);
                                if ($html && preg_match('/<title>(.*?)<\/title>/i', $html, $matches)) {
                                    $name = $matches[1];
                                }
                            }
                        }
                    } catch (\Exception $e) {
                        // Ignore et garde vide
                    }

                    // On remplit le formulaire avec les données scrapées
                    $this->form->fill([
                        'name' => $name,
                        'description' => $description,
                        'status' => 'testing',
                    ]);

                    \Filament\Notifications\Notification::make()
                        ->title('Produit scrapé avec succès')
                        ->success()
                        ->send();
                }),
        ];
    }
}
