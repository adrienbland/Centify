<?php

namespace App\Filament\Resources\ProductResource\RelationManagers;

use Filament\Forms;
use Filament\Forms\Form;
use Filament\Resources\RelationManagers\RelationManager;
use Filament\Tables;
use Filament\Tables\Table;
use Illuminate\Database\Eloquent\Builder;
use Illuminate\Database\Eloquent\SoftDeletingScope;

class ScriptsRelationManager extends RelationManager
{
    protected static string $relationship = 'scripts';
    protected static ?string $title = 'Scripts IA (Le Cerveau)';
    protected static ?string $icon = 'heroicon-o-chat-bubble-left-ellipsis';

    public function form(Form $form): Form
    {
        return $form
            ->schema([
                Forms\Components\Textarea::make('hook')
                    ->label('L\'Accroche (Les 3 premières secondes)')
                    ->required()
                    ->rows(2)
                    ->columnSpanFull(),
                Forms\Components\Textarea::make('body')
                    ->label('Le Corps (La valeur du produit)')
                    ->required()
                    ->rows(4)
                    ->columnSpanFull(),
                Forms\Components\Textarea::make('cta')
                    ->label('L\'Appel à l\'action (CTA)')
                    ->required()
                    ->rows(2)
                    ->columnSpanFull(),
                Forms\Components\Textarea::make('full_text')
                    ->label('Texte complet généré (Pour le TTS)')
                    ->required()
                    ->rows(4)
                    ->columnSpanFull(),
                Forms\Components\Select::make('status')
                    ->label('Statut')
                    ->options([
                        'draft' => 'Brouillon',
                        'approved' => 'Approuvé (Prêt pour vidéo)',
                        'rejected' => 'Rejeté',
                    ])
                    ->default('draft')
                    ->required(),
            ]);
    }

    public function table(Table $table): Table
    {
        return $table
            ->recordTitleAttribute('hook')
            ->columns([
                Tables\Columns\TextColumn::make('hook')
                    ->label('Accroche')
                    ->limit(50)
                    ->searchable(),
                Tables\Columns\TextColumn::make('status')
                    ->label('Statut')
                    ->badge()
                    ->colors([
                        'warning' => 'draft',
                        'success' => 'approved',
                        'danger' => 'rejected',
                    ]),
                Tables\Columns\TextColumn::make('created_at')
                    ->label('Généré le')
                    ->dateTime('d/m/Y H:i')
                    ->sortable(),
            ])
            ->filters([
                //
            ])
            ->headerActions([
                Tables\Actions\CreateAction::make()->label('Nouveau (Manuel)'),
                Tables\Actions\Action::make('generate_ai')
                    ->label('🧠 Générer via Ollama')
                    ->color('primary')
                    ->requiresConfirmation()
                    ->modalHeading('Génération du script vidéo')
                    ->modalDescription('Ollama va écrire un script agressif basé sur les infos de ce produit et tes directives manuelles.')
                    ->form([
                        Forms\Components\Textarea::make('ai_prompt')
                            ->label('Directives IA Manuelles')
                            ->placeholder('Ex: Insiste sur le fait que ça résout la douleur rapidement...')
                    ])
                    ->action(function (RelationManager $livewire, array $data) {
                        $product = $livewire->getOwnerRecord();
                        $manualPrompt = $data['ai_prompt'] ?? ($product->ai_custom_prompt ?? "Rends ça hyper engageant.");
                        
                        $prompt = "Tu es un copywriter expert TikTok et Shorts. Écris un script viral très dynamique (15s) pour vendre ce produit : '{$product->name}'.\n\n"
                                . "Voici les spécifications et la description du produit :\n{$product->description}\n\n"
                                . "La niche est: {$product->niche}.\n"
                                . "RÈGLES STRICTES POUR LA VOIX IA (TTS) :\n"
                                . "1. NE LIS JAMAIS le nom complet du produit tel quel. Invente un petit nom naturel (ex: 'cette brosse magique', 'ce gadget').\n"
                                . "2. Le texte doit être en français parlé, naturel, dynamique.\n"
                                . "3. INTERDICTION ABSOLUE d'utiliser des points de suspension (...) ou des emojis. Ils font bugger l'audio. Utilise des points normaux.\n"
                                . "4. Directives manuelles: " . $manualPrompt . "\n\n"
                                . "FORMAT OBLIGATOIRE:\n[HOOK]: <1 phrase choc>\n[BODY]: <2 phrases courtes sur le problème résolu>\n[CTA]: <1 phrase d'action>\n\n"
                                . "Réponds UNIQUEMENT avec ce format, sans commentaires.";

                        try {
                            $response = \Illuminate\Support\Facades\Http::timeout(60)->post('http://host.docker.internal:11434/api/generate', [
                                'model' => 'qwen2.5:7b', // Model local Ollama
                                'prompt' => $prompt,
                                'stream' => false,
                            ]);

                            if ($response->successful()) {
                                $text = $response->json('response');
                                
                                // Nettoyage strict (supprimer emojis et points de suspension)
                                $text = preg_replace('/[\x{1F600}-\x{1F64F}\x{1F300}-\x{1F5FF}\x{1F680}-\x{1F6FF}\x{2600}-\x{26FF}\x{2700}-\x{27BF}]/u', '', $text);
                                $text = str_replace('...', '.', $text);
                                
                                // Parsing basique du format demandé
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
                                    ->title('Script généré avec succès !')
                                    ->success()
                                    ->sendToDatabase(auth()->user());
                            } else {
                                throw new \Exception("Erreur serveur Ollama");
                            }
                        } catch (\Exception $e) {
                            \Filament\Notifications\Notification::make()
                                ->title('Erreur Ollama')
                                ->body($e->getMessage() . '. Vérifie que Ollama tourne sur host.docker.internal:11434')
                                ->danger()
                                ->sendToDatabase(auth()->user());
                        }
                    }),
            ])
            ->actions([
                Tables\Actions\EditAction::make(),
                Tables\Actions\DeleteAction::make(),
                Tables\Actions\Action::make('approve')
                    ->label('Approuver (Lancer la vidéo)')
                    ->icon('heroicon-o-play-circle')
                    ->color('success')
                    ->hidden(fn ($record) => $record->status === 'approved')
                    ->action(function ($record, RelationManager $livewire) {
                        $record->update(['status' => 'approved']);
                        // Envoyer à la table `videos` pour que le worker python commence le rendu TTS+Montage
                        \App\Models\Video::create([
                            'script_id' => $record->id,
                            'product_id' => $livewire->getOwnerRecord()->id,
                            'status' => 'rendering',
                            'social_network' => 'tiktok',
                            'file_path' => 'processing...',
                        ]);
                        \Filament\Notifications\Notification::make()
                            ->title('Vidéo envoyée au montage IA !')
                            ->success()
                            ->sendToDatabase(auth()->user());
                    }),
            ]);
    }
}
