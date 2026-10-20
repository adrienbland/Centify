<?php

namespace App\Filament\Resources\TrendResource\RelationManagers;

use Filament\Forms;
use Filament\Forms\Form;
use Filament\Resources\RelationManagers\RelationManager;
use Filament\Tables;
use Filament\Tables\Table;
use Illuminate\Support\HtmlString;

class ProposalsRelationManager extends RelationManager
{
    protected static string $relationship = 'proposals';
    protected static ?string $title = 'Propositions Fournisseurs (AliExpress)';

    public function form(Form $form): Form
    {
        return $form
            ->schema([
                Forms\Components\TextInput::make('title')
                    ->label('Titre du produit')
                    ->required()
                    ->maxLength(255),
                Forms\Components\TextInput::make('price')
                    ->label('Prix Fournisseur ($)')
                    ->numeric()
                    ->required(),
                Forms\Components\TextInput::make('orders')
                    ->label('Nombre de commandes')
                    ->numeric()
                    ->default(0),
                Forms\Components\TextInput::make('image_url')
                    ->label('URL de l\'image')
                    ->maxLength(255),
                Forms\Components\TextInput::make('aliexpress_url')
                    ->label('Lien AliExpress')
                    ->maxLength(255)
                    ->columnSpanFull(),
                Forms\Components\Textarea::make('description')
                    ->label('Spécifications techniques & Détails')
                    ->rows(4)
                    ->columnSpanFull(),
            ]);
    }

    public function table(Table $table): Table
    {
        return $table
            ->recordTitleAttribute('title')
            ->columns([
                Tables\Columns\ImageColumn::make('image_url')
                    ->label('Aperçu')
                    ->size(70)
                    ->square(),
                Tables\Columns\TextColumn::make('title')
                    ->label('Produit & Spécifications')
                    ->limit(42)
                    ->description(fn ($record) => \Illuminate\Support\Str::limit($record->description ?? 'Clique sur Détails pour voir la fiche technique', 65))
                    ->tooltip(fn ($record) => $record->title)
                    ->searchable()
                    ->weight('bold'),
                Tables\Columns\TextColumn::make('price')
                    ->label('Coût Achat')
                    ->sortable()
                    ->badge()
                    ->color('gray')
                    ->money('USD'),
                Tables\Columns\TextColumn::make('estimated_sell_price')
                    ->label('Prix Vente (x3)')
                    ->getStateUsing(fn ($record) => $record->price * 3)
                    ->money('USD')
                    ->color('info'),
                Tables\Columns\TextColumn::make('estimated_profit')
                    ->label('Bénéfice Net / Vente')
                    ->getStateUsing(fn ($record) => ($record->price * 3) - $record->price - (($record->price * 3) * 0.15))
                    ->money('USD')
                    ->badge()
                    ->color('success')
                    ->tooltip('Calculé avec marge x3 moins 15% de frais (Stripe/Shopify)'),
                Tables\Columns\TextColumn::make('orders')
                    ->label('Ventes AliExpress')
                    ->sortable()
                    ->badge()
                    ->color('primary'),
            ])
            ->headerActions([
                Tables\Actions\CreateAction::make()->label('Ajouter une proposition'),
            ])
            ->actions([
                Tables\Actions\Action::make('details')
                    ->label('Infos & Specs')
                    ->icon('heroicon-o-eye')
                    ->color('info')
                    ->modalHeading(fn ($record) => $record->title)
                    ->modalSubmitAction(false)
                    ->modalCancelActionLabel('Fermer')
                    ->modalContent(function (\App\Models\TrendProposal $record): HtmlString {
                        $img = htmlspecialchars($record->image_url ?? '', ENT_QUOTES, 'UTF-8');
                        $specs = nl2br(htmlspecialchars($record->description ?? 'Aucune spécification technique renseignée.', ENT_QUOTES, 'UTF-8'));
                        $buy = number_format((float) $record->price, 2);
                        $sell = number_format((float) $record->price * 3, 2);
                        $profit = number_format((float) (($record->price * 3) - $record->price - (($record->price * 3) * 0.15)), 2);

                        return new HtmlString("
                            <div class='grid grid-cols-1 md:grid-cols-3 gap-4 p-2'>
                                <div class='flex flex-col items-center'>
                                    <img src='{$img}' class='rounded-xl w-48 h-48 object-cover border border-purple-500/40 shadow-lg' alt='Produit' />
                                </div>
                                <div class='md:col-span-2 space-y-3 text-sm'>
                                    <div class='flex gap-3 flex-wrap'>
                                        <span class='px-3 py-1 rounded-lg bg-gray-800 text-gray-300'>Achat : <strong>\${$buy}</strong></span>
                                        <span class='px-3 py-1 rounded-lg bg-blue-900/40 text-blue-300'>Revente conseillée : <strong>\${$sell}</strong></span>
                                        <span class='px-3 py-1 rounded-lg bg-green-900/40 text-green-300'>Bénéfice Net : <strong>+\${$profit}/vente</strong></span>
                                        <span class='px-3 py-1 rounded-lg bg-purple-900/40 text-purple-300'>📦 <strong>{$record->orders}</strong> commandes</span>
                                    </div>
                                    <div class='p-3 rounded-lg bg-gray-900/80 border border-gray-800 text-gray-200 leading-relaxed'>
                                        <div class='text-xs uppercase tracking-wider text-purple-400 font-bold mb-1'>Fiche Technique & Caractéristiques :</div>
                                        {$specs}
                                    </div>
                                </div>
                            </div>
                        ");
                    }),

                Tables\Actions\Action::make('import')
                    ->label('Importer ce Produit')
                    ->icon('heroicon-o-arrow-down-tray')
                    ->color('success')
                    ->requiresConfirmation()
                    ->modalHeading('Importer dans le Catalogue & Générer le Script IA')
                    ->modalDescription('Ce produit (avec son image et ses spécifications techniques) sera importé dans ton catalogue et Ollama générera immédiatement un script TikTok sur-mesure.')
                    ->form([
                        Forms\Components\Textarea::make('ai_prompt')
                            ->label('Directives IA Manuelles (Optionnel)')
                            ->placeholder('Ex: Insiste sur le fait que ça enlève 99% des poils morts et que les chats adorent le massage...'),
                    ])
                    ->action(function (\App\Models\TrendProposal $record, array $data, RelationManager $livewire) {
                        $trend = $livewire->getOwnerRecord();
                        $niche = $trend->extracted_keyword ?: ($trend->hashtag ?: 'E-commerce');

                        $fullSpecs = $record->description
                            ?: "Produit tendance TikTok : {$record->title} ({$niche}).\nContexte viral : {$trend->description}";

                        // 1. Créer le Produit avec son image et ses vraies spécifications techniques
                        $product = \App\Models\Product::create([
                            'name' => $record->title,
                            'image_url' => $record->image_url,
                            'supplier_url' => $record->aliexpress_url,
                            'niche' => $niche,
                            'description' => $fullSpecs . "\n\nSource AliExpress : " . $record->aliexpress_url,
                            'status' => 'testing',
                            'ai_custom_prompt' => !empty($data['ai_prompt']) ? $data['ai_prompt'] : null,
                        ]);

                        // 2. Mettre à jour le statut du Trend parent
                        $trend->update(['status' => 'imported']);

                        // 3. Génération Automatique du Script via Ollama avec les vraies spécifications
                        $prompt = "Tu es un copywriter expert TikTok et Shorts. Écris un script viral très dynamique (15s) pour vendre ce produit précis :\n"
                                . "Nom du produit : '{$product->name}'\n"
                                . "Catégorie / Usage : {$niche}\n"
                                . "Spécifications techniques et usage réel du produit :\n{$fullSpecs}\n\n"
                                . "RÈGLES STRICTES POUR LA VOIX IA (TTS) :\n"
                                . "1. Parle UNIQUEMENT de ce produit précis et de ses vraies caractéristiques techniques ci-dessus (ne change jamais le sujet !).\n"
                                . "2. NE LIS JAMAIS le titre anglais complet tel quel. Appelle-le par son vrai nom en français naturel (ex: 'cette brosse à vapeur pour chat', 'ce projecteur galaxie').\n"
                                . "3. INTERDICTION d'utiliser des points de suspension (...), des URLs ou des emojis. Utilise des phrases courtes et percutantes.\n"
                                . "4. Directive spéciale : " . (!empty($product->ai_custom_prompt) ? $product->ai_custom_prompt : "Cible le problème concret résolu par le produit.") . "\n\n"
                                . "FORMAT OBLIGATOIRE:\n[HOOK]: <1 phrase choc qui interpelle>\n[BODY]: <2 phrases concrètes sur les fonctionnalités techniques et le bénéfice>\n[CTA]: <1 phrase d'action courte>\n\n"
                                . "Réponds UNIQUEMENT avec ce format, rien d'autre.";

                        try {
                            $response = \Illuminate\Support\Facades\Http::timeout(60)->post('http://host.docker.internal:11434/api/generate', [
                                'model' => 'qwen2.5:7b',
                                'prompt' => $prompt,
                                'stream' => false,
                            ]);

                            if ($response->successful()) {
                                $text = $response->json('response');
                                $text = preg_replace('/[\x{1F600}-\x{1F64F}\x{1F300}-\x{1F5FF}\x{1F680}-\x{1F6FF}\x{2600}-\x{26FF}\x{2700}-\x{27BF}]/u', '', $text);
                                $text = preg_replace('/https?:\/\/\S+/i', '', $text);
                                $text = str_replace('...', '.', $text);

                                $hook = str_contains($text, '[HOOK]:') ? explode('[BODY]:', explode('[HOOK]:', $text)[1])[0] : 'Arrête de scroller !';
                                $body = str_contains($text, '[BODY]:') ? explode('[CTA]:', explode('[BODY]:', $text)[1])[0] : $text;
                                $cta = str_contains($text, '[CTA]:') ? explode('[CTA]:', $text)[1] : 'Clique sur le lien en bio !';

                                $fullText = trim(str_replace(['[HOOK]:', '[BODY]:', '[CTA]:'], '', $text));

                                $product->scripts()->create([
                                    'hook' => trim($hook),
                                    'body' => trim($body),
                                    'cta' => trim($cta),
                                    'full_text' => $fullText,
                                    'status' => 'draft',
                                ]);

                                \Filament\Notifications\Notification::make()
                                    ->title('Produit importé (avec image & specs) + Script IA prêt !')
                                    ->body("Le script pour « {$product->name} » t'attend dans l'onglet Produits.")
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
                    ->label('AliExpress')
                    ->icon('heroicon-o-arrow-top-right-on-square')
                    ->color('gray')
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
