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
                        ->label('URL du produit (Shopify ou AliExpress)')
                        ->url()
                        ->required(),
                ])
                ->action(function (array $data) {
                    $url = $data['url'];
                    $name = '';
                    $description = '';
                    $imageUrl = '';

                    try {
                        if (str_contains($url, 'aliexpress.com')) {
                            $response = \Illuminate\Support\Facades\Http::timeout(8)
                                ->withHeaders(['User-Agent' => 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'])
                                ->get($url);
                            $html = $response->body();

                            if ($html && preg_match('/<title>(.*?)<\/title>/is', $html, $matches)) {
                                $name = explode('|', $matches[1])[0] ?? 'Produit AliExpress';
                                $name = trim(str_replace(['AliExpress', 'Achetez'], '', $name));
                            }
                            if ($html && preg_match('/property=["\']og:image["\']\s+content=["\'](.*?)["\']/i', $html, $imgMatches)) {
                                $imageUrl = $imgMatches[1];
                            }
                            if ($html && preg_match('/name=["\']description["\']\s+content=["\'](.*?)["\']/i', $html, $descMatches)) {
                                $description = html_entity_decode($descMatches[1]);
                            }
                            if (!$description) {
                                $description = "Produit importé depuis AliExpress : {$name}\nURL: {$url}";
                            }
                        } else {
                            $jsonUrl = strtok($url, '?');
                            if (!str_ends_with($jsonUrl, '.json')) {
                                $jsonUrl .= '.json';
                            }
                            $response = \Illuminate\Support\Facades\Http::timeout(6)->get($jsonUrl);
                            if ($response->successful()) {
                                $product = $response->json('product');
                                if ($product) {
                                    $name = $product['title'] ?? 'Produit Inconnu';
                                    $description = trim(strip_tags($product['body_html'] ?? ''));
                                    $imageUrl = $product['image']['src'] ?? ($product['images'][0]['src'] ?? '');
                                }
                            }
                        }
                    } catch (\Exception $e) {
                    }

                    if ($name) {
                        $this->record->update([
                            'name' => $name,
                            'supplier_url' => $url,
                            'image_url' => $imageUrl ?: $this->record->image_url,
                            'description' => $description ?: $this->record->description,
                        ]);
                        $this->fillForm();

                        \Filament\Notifications\Notification::make()
                            ->title('Produit (Nom, Image & Specs) mis à jour !')
                            ->success()
                            ->sendToDatabase(auth()->user());
                    }
                }),
            Actions\DeleteAction::make(),
        ];
    }
}
