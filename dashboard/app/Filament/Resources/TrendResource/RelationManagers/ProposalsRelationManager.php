<?php

namespace App\Filament\Resources\TrendResource\RelationManagers;

use Filament\Forms;
use Filament\Forms\Form;
use Filament\Resources\RelationManagers\RelationManager;
use Filament\Tables;
use Filament\Tables\Table;
use Illuminate\Database\Eloquent\Builder;
use Illuminate\Database\Eloquent\SoftDeletingScope;

class ProposalsRelationManager extends RelationManager
{
    protected static string $relationship = 'proposals';

    public function form(Form $form): Form
    {
        return $form
            ->schema([
                Forms\Components\TextInput::make('aliexpress_url')
                    ->required()
                    ->maxLength(255),
            ]);
    }

    public function table(Table $table): Table
    {
        return $table
            ->recordTitleAttribute('title')
            ->columns([
                Tables\Columns\ImageColumn::make('image_url')
                    ->label('Miniature')
                    ->size(60),
                Tables\Columns\TextColumn::make('title')
                    ->label('Titre AliExpress')
                    ->limit(40)
                    ->tooltip(fn ($record) => $record->title)
                    ->searchable(),
                Tables\Columns\TextColumn::make('price')
                    ->label('Prix Fournisseur')
                    ->sortable()
                    ->badge()
                    ->color('gray')
                    ->money('USD'),
                Tables\Columns\TextColumn::make('estimated_sell_price')
                    ->label('Prix de vente (x3)')
                    ->getStateUsing(fn ($record) => $record->price * 3)
                    ->money('USD')
                    ->color('info'),
                Tables\Columns\TextColumn::make('estimated_profit')
                    ->label('Bénéfice Net Estimé')
                    ->getStateUsing(fn ($record) => ($record->price * 3) - $record->price - (($record->price * 3) * 0.15))
                    ->money('USD')
                    ->badge()
                    ->color('success')
                    ->tooltip('Calculé avec marge x3 moins 15% de frais (Stripe/Shopify)'),
                Tables\Columns\TextColumn::make('orders')
                    ->label('Commandes')
                    ->sortable()
                    ->badge()
                    ->color('primary'),
            ])
            ->filters([
                //
            ])
            ->headerActions([
                // Optionnel: Ajouter manuellement une proposition
            ])
            ->actions([
                Tables\Actions\Action::make('import')
                    ->label('Importer ce Produit')
                    ->icon('heroicon-o-arrow-down-tray')
                    ->color('success')
                    ->requiresConfirmation()
                    ->modalHeading('Importer et configurer l\'IA')
                    ->modalDescription('Tu t\'apprêtes à importer ce produit dans ton catalogue officiel. Tu peux ajouter des instructions spécifiques pour la génération vidéo.')
                    ->form([
                        Forms\Components\Textarea::make('ai_prompt')
                            ->label('Directives IA Manuelles')
                            ->placeholder('Ex: Le script doit insister sur la livraison gratuite...'),
                    ])
                    ->action(function (\App\Models\TrendProposal $record, array $data, RelationManager $livewire) {
                        // 1. Créer le Produit
                        $product = \App\Models\Product::create([
                            'name' => $record->title,
                            'description' => "Importé depuis AliExpress (Radar).\nURL: " . $record->aliexpress_url,
                            'status' => 'testing',
                            'ai_custom_prompt' => $data['ai_prompt'] ?? null,
                        ]);

                        // 2. Mettre à jour le statut du Trend parent
                        $trend = $livewire->getOwnerRecord();
                        $trend->update(['status' => 'imported']);

                        // 3. Génération Automatique du Script via Ollama
                        $prompt = "Tu es un copywriter expert TikTok et Shorts. Écris un script viral très dynamique (15s) pour vendre ce produit : '{$product->name}'.\n"
                                . "Voici les spécifications et la description du produit :\n{$product->description}\n\n"
                                . "RÈGLES STRICTES POUR LA VOIX IA (TTS) :\n"
                                . "1. NE LIS JAMAIS le nom complet du produit tel quel. Invente un petit nom naturel (ex: 'cette brosse magique', 'ce gadget').\n"
                                . "2. Le texte doit être en français parlé, naturel, dynamique.\n"
                                . "3. INTERDICTION d'utiliser des points de suspension (...) ou des emojis. Ils font bugger l'audio. Utilise des points normaux.\n"
                                . "4. " . ($product->ai_custom_prompt ?? "Rends le texte hyper engageant.") . "\n\n"
                                . "FORMAT OBLIGATOIRE:\n[HOOK]: <1 phrase choc>\n[BODY]: <2 phrases courtes sur le problème résolu>\n[CTA]: <1 phrase d'action>\n\n"
                                . "Réponds UNIQUEMENT avec ce format, rien d'autre.";

                        try {
                            $response = \Illuminate\Support\Facades\Http::timeout(60)->post('http://host.docker.internal:11434/api/generate', [
                                'model' => 'qwen2.5:7b',
                                'prompt' => $prompt,
                                'stream' => false,
                            ]);

                            if ($response->successful()) {
                                $text = $response->json('response');
                                
                                // Nettoyage strict (supprimer emojis et points de suspension)
                                $text = preg_replace('/[\x{1F600}-\x{1F64F}\x{1F300}-\x{1F5FF}\x{1F680}-\x{1F6FF}\x{2600}-\x{26FF}\x{2700}-\x{27BF}]/u', '', $text);
                                $text = str_replace('...', '.', $text);
                                
                                $hook = str_contains($text, '[HOOK]:') ? explode('[BODY]:', explode('[HOOK]:', $text)[1])[0] : 'Hook auto';
                                $body = str_contains($text, '[BODY]:') ? explode('[CTA]:', explode('[BODY]:', $text)[1])[0] : $text;
                                $cta = str_contains($text, '[CTA]:') ? explode('[CTA]:', $text)[1] : 'Lien en bio!';

                                $fullText = trim(str_replace(['[HOOK]:', '[BODY]:', '[CTA]:'], '', $text));

                                $product->scripts()->create([
                                    'hook' => trim($hook),
                                    'body' => trim($body),
                                    'cta' => trim($cta),
                                    'full_text' => $fullText,
                                    'status' => 'draft',
                                ]);

                                \Filament\Notifications\Notification::make()
                                    ->title('Produit importé ET Script Brouillon généré !')
                                    ->body('Tu peux aller valider le script dans l\'onglet Produits.')
                                    ->success()
                                    ->sendToDatabase(auth()->user());
                            }
                        } catch (\Exception $e) {
                            \Filament\Notifications\Notification::make()
                                ->title('Produit importé, mais erreur IA')
                                ->body('Le produit a été créé, mais Ollama n\'a pas pu générer le script automatiquement.')
                                ->warning()
                                ->sendToDatabase(auth()->user());
                        }
                    }),
                Tables\Actions\Action::make('view_link')
                    ->label('Ouvrir lien')
                    ->icon('heroicon-o-link')
                    ->url(fn (\App\Models\TrendProposal $record) => $record->aliexpress_url)
                    ->openUrlInNewTab(),
            ])
            ->bulkActions([
                Tables\Actions\BulkActionGroup::make([
                    Tables\Actions\DeleteBulkAction::make(),
                ]),
            ]);
    }
}
