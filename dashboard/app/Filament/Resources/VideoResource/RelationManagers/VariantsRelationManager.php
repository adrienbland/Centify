<?php

namespace App\Filament\Resources\VideoResource\RelationManagers;

use Filament\Forms;
use Filament\Forms\Form;
use Filament\Resources\RelationManagers\RelationManager;
use Filament\Tables;
use Filament\Tables\Table;

class VariantsRelationManager extends RelationManager
{
    protected static string $relationship = 'variants';
    protected static ?string $title = '🧪 Hook Tester (A/B Testing des 3 premières secondes)';
    protected static ?string $icon = 'heroicon-o-beaker';

    public function form(Form $form): Form
    {
        return $form
            ->schema([
                Forms\Components\Textarea::make('hook_text')
                    ->label('Texte du Hook (Variante d\'accroche)')
                    ->required()
                    ->rows(2)
                    ->columnSpanFull(),
                Forms\Components\TextInput::make('views')
                    ->label('Vues')
                    ->numeric()
                    ->default(0),
                Forms\Components\TextInput::make('likes')
                    ->label('Likes')
                    ->numeric()
                    ->default(0),
                Forms\Components\TextInput::make('retention_3s')
                    ->label('Rétention à 3s (%)')
                    ->numeric()
                    ->suffix('%')
                    ->default(0),
                Forms\Components\Toggle::make('is_winner')
                    ->label('🏆 Hook Gagnant (Winner)')
                    ->default(false),
            ]);
    }

    public function table(Table $table): Table
    {
        return $table
            ->recordTitleAttribute('hook_text')
            ->columns([
                Tables\Columns\TextColumn::make('hook_text')
                    ->label('Variante d\'Accroche (3 premières secondes)')
                    ->weight('bold')
                    ->wrap(),
                Tables\Columns\TextColumn::make('views')
                    ->label('Vues')
                    ->numeric()
                    ->sortable()
                    ->badge()
                    ->color('gray'),
                Tables\Columns\TextColumn::make('likes')
                    ->label('Likes')
                    ->numeric()
                    ->sortable()
                    ->badge()
                    ->color('info'),
                Tables\Columns\TextColumn::make('retention_3s')
                    ->label('Rétention 3s')
                    ->suffix('%')
                    ->sortable()
                    ->badge()
                    ->color(fn ($state) => $state >= 40 ? 'success' : ($state >= 25 ? 'warning' : 'gray')),
                Tables\Columns\IconColumn::make('is_winner')
                    ->label('Winner')
                    ->boolean(),
            ])
            ->headerActions([
                Tables\Actions\CreateAction::make()->label('Ajouter un Hook'),
                Tables\Actions\Action::make('generate_hooks_ai')
                    ->label('🧪 Générer 3 Variantes A/B via Ollama')
                    ->icon('heroicon-o-sparkles')
                    ->color('primary')
                    ->requiresConfirmation()
                    ->modalHeading('Générer 3 variantes d\'accroches (A/B Testing)')
                    ->modalDescription('Ollama va créer 3 angles psychologiques différents (Problème/Douleur, Curiosité Choc, Preuve Sociale) basés sur la fiche technique de ce produit.')
                    ->action(function (RelationManager $livewire) {
                        $video = $livewire->getOwnerRecord();
                        $product = $video->product;

                        $prompt = "Tu es un expert TikTok Ads. Génère exactement 3 phrases d'accroche (Hooks de moins de 3 secondes) ultra-percutantes et différentes pour ce produit :\n"
                                . "Produit : '{$product?->name}'\n"
                                . "Description / Specs : {$product?->description}\n\n"
                                . "RÈGLES : Français parlé, aucun emoji, aucun point de suspension (...), 1 phrase par ligne commençant par [1], [2], [3].\n"
                                . "[1] Angle Problème/Douleur\n"
                                . "[2] Angle Curiosité/Secret\n"
                                . "[3] Angle Preuve Sociale/Choc\n"
                                . "Réponds UNIQUEMENT avec les 3 lignes.";

                        try {
                            $response = \Illuminate\Support\Facades\Http::timeout(60)->post('http://host.docker.internal:11434/api/generate', [
                                'model' => 'qwen2.5:7b',
                                'prompt' => $prompt,
                                'stream' => false,
                            ]);

                            if ($response->successful()) {
                                $lines = array_filter(array_map('trim', explode("\n", $response->json('response'))));
                                $created = 0;
                                foreach ($lines as $line) {
                                    $clean = trim(preg_replace('/^(\[\d+\]|\d+[\.\)]|-)\s*/', '', $line), " \"'");
                                    if (strlen($clean) > 8) {
                                        $video->variants()->create([
                                            'hook_text' => $clean,
                                            'views' => 0,
                                            'likes' => 0,
                                            'retention_3s' => 0,
                                            'is_winner' => false,
                                        ]);
                                        $created++;
                                        if ($created >= 3) {
                                            break;
                                        }
                                    }
                                }

                                \Filament\Notifications\Notification::make()
                                    ->title("{$created} variantes de Hooks générées !")
                                    ->body('Tu peux maintenant lancer le test A/B sur ces accroches.')
                                    ->success()
                                    ->sendToDatabase(auth()->user());
                            }
                        } catch (\Exception $e) {
                            \Filament\Notifications\Notification::make()
                                ->title('Erreur Ollama')
                                ->body($e->getMessage())
                                ->danger()
                                ->sendToDatabase(auth()->user());
                        }
                    }),
            ])
            ->actions([
                Tables\Actions\Action::make('apply_hook')
                    ->label('Utiliser ce Hook & Re-rendre')
                    ->icon('heroicon-o-play')
                    ->color('success')
                    ->requiresConfirmation()
                    ->modalHeading('Remplacer l\'accroche de la vidéo par ce Hook ?')
                    ->modalDescription('Le script de la vidéo utilisera cette accroche et le moteur Python va régénérer la vidéo MP4.')
                    ->action(function ($record, RelationManager $livewire) {
                        $video = $livewire->getOwnerRecord();
                        if ($video->script) {
                            $newFullText = trim($record->hook_text) . " " . trim($video->script->body) . " " . trim($video->script->cta);
                            $video->script->update([
                                'hook' => $record->hook_text,
                                'full_text' => $newFullText,
                            ]);
                        }
                        $video->update([
                            'user_feedback' => null,
                            'status' => 'rendering',
                        ]);

                        \Filament\Notifications\Notification::make()
                            ->title('Nouveau Hook appliqué ! Montage relancé.')
                            ->success()
                            ->sendToDatabase(auth()->user());
                    }),
                Tables\Actions\EditAction::make(),
                Tables\Actions\DeleteAction::make(),
            ]);
    }
}
