<?php

namespace App\Filament\Resources;

use App\Filament\Resources\ProductResource\Pages;
use App\Filament\Resources\ProductResource\RelationManagers;
use App\Models\Product;
use Filament\Forms;
use Filament\Forms\Form;
use Filament\Resources\Resource;
use Filament\Tables;
use Filament\Tables\Table;
use Filament\Forms\Components\Section;
use Filament\Forms\Components\Grid;
use Filament\Forms\Components\TextInput;
use Filament\Forms\Components\Select;
use Filament\Forms\Components\MarkdownEditor;
use Filament\Forms\Components\Textarea;
use Filament\Forms\Components\Placeholder;
use Filament\Tables\Columns\TextColumn;
use Filament\Tables\Columns\ImageColumn;
use Illuminate\Support\HtmlString;

class ProductResource extends Resource
{
    protected static ?string $model = Product::class;

    protected static ?string $navigationIcon = 'heroicon-o-shopping-bag';
    protected static ?string $navigationGroup = 'Catalogue & IA';
    protected static ?int $navigationSort = 1;

    public static function form(Form $form): Form
    {
        return $form
            ->schema([
                Grid::make(3)->schema([
                    // Colonne Principale (2/3)
                    Grid::make(1)->schema([
                        Section::make('Informations & Spécifications du Produit')
                            ->description('Les détails techniques et visuels utilisés par Ollama et le moteur vidéo Python.')
                            ->icon('heroicon-m-cube')
                            ->schema([
                                TextInput::make('name')
                                    ->label('Nom du Produit')
                                    ->required()
                                    ->maxLength(255)
                                    ->live(onBlur: true)
                                    ->afterStateUpdated(fn ($record, $state) => $record?->update(['name' => $state])),

                                TextInput::make('niche')
                                    ->label('Niche (ex: Animaux, Tech, Beauté)')
                                    ->maxLength(100)
                                    ->live(onBlur: true)
                                    ->afterStateUpdated(fn ($record, $state) => $record?->update(['niche' => $state])),

                                TextInput::make('image_url')
                                    ->label('Image du Produit (URL ou chemin /medias/...)')
                                    ->placeholder('https://... ou /medias/library/...')
                                    ->maxLength(255)
                                    ->live(onBlur: true)
                                    ->afterStateUpdated(fn ($record, $state) => $record?->update(['image_url' => $state])),

                                TextInput::make('supplier_url')
                                    ->label('Lien Fournisseur (AliExpress / Shopify)')
                                    ->placeholder('https://aliexpress.com/item/...')
                                    ->maxLength(255)
                                    ->live(onBlur: true)
                                    ->afterStateUpdated(fn ($record, $state) => $record?->update(['supplier_url' => $state])),

                                MarkdownEditor::make('description')
                                    ->label('Spécifications Techniques & Description Marketing (Contexte IA)')
                                    ->columnSpanFull()
                                    ->live(onBlur: true)
                                    ->afterStateUpdated(fn ($record, $state) => $record?->update(['description' => $state])),
                            ])->columns(2),

                        Section::make('Intelligence Artificielle (Le Cerveau)')
                            ->description('Donne tes directives permanentes à Ollama pour la rédaction des scripts de ce produit.')
                            ->icon('heroicon-m-cpu-chip')
                            ->schema([
                                Textarea::make('ai_custom_prompt')
                                    ->label('Directives IA Manuelles (Globales au produit)')
                                    ->placeholder('Ex: Insiste sur le fait que la vapeur démêle les poils sans douleur et que la batterie tient 1 semaine...')
                                    ->rows(3)
                                    ->columnSpanFull()
                                    ->live(onBlur: true)
                                    ->afterStateUpdated(fn ($record, $state) => $record?->update(['ai_custom_prompt' => $state]))
                                    ->hint('Ces instructions seront systématiquement injectées dans le prompt d\'Ollama.'),
                            ]),
                    ])->columnSpan(2),

                    // Colonne Latérale (1/3)
                    Grid::make(1)->schema([
                        Section::make('Visuel Produit (Incrusté en Vidéo)')
                            ->schema([
                                Placeholder::make('product_image_preview')
                                    ->label('Aperçu Visuel')
                                    ->content(function (?Product $record): HtmlString {
                                        if (!$record || empty($record->image_url)) {
                                            return new HtmlString('<div class="text-xs text-gray-400 italic">Aucune image associée. Ajoute une URL d\'image pour qu\'elle soit incrustée dans les vidéos TikTok !</div>');
                                        }
                                        $src = htmlspecialchars($record->image_url, ENT_QUOTES, 'UTF-8');
                                        return new HtmlString("
                                            <div class='flex flex-col items-center space-y-2'>
                                                <img src='{$src}' class='w-44 h-44 object-cover rounded-xl border border-purple-500/40 shadow-md' alt='Produit' />
                                                <span class='text-xs text-purple-400'>✅ Utilisée par le moteur vidéo Python</span>
                                            </div>
                                        ");
                                    }),
                            ]),

                        Section::make('Statut & Liaisons')
                            ->schema([
                                Select::make('status')
                                    ->label('Statut du test')
                                    ->options([
                                        'testing' => '🧪 En test (Testing)',
                                        'scaling' => '🚀 En explosion (Scaling)',
                                        'dead' => '💀 Mort (Dead)',
                                    ])
                                    ->default('testing')
                                    ->required(),

                                Select::make('store_id')
                                    ->label('Boutique Shopify')
                                    ->relationship('store', 'name')
                                    ->searchable()
                                    ->preload(),

                                Select::make('category_id')
                                    ->label('Catégorie Globale')
                                    ->relationship('category', 'name')
                                    ->searchable()
                                    ->preload(),

                                Select::make('default_tiktok_account_id')
                                    ->label('Compte TikTok lié')
                                    ->relationship('defaultTiktokAccount', 'account_name')
                                    ->searchable()
                                    ->preload(),

                                TextInput::make('shopify_id')
                                    ->label('ID Shopify')
                                    ->disabled()
                                    ->dehydrated(false)
                                    ->hint('Généré automatiquement lors de la synchro.'),
                            ]),
                    ])->columnSpan(1),
                ]),
            ]);
    }

    public static function table(Table $table): Table
    {
        return $table
            ->poll('5s')
            ->columns([
                ImageColumn::make('image_url')
                    ->label('Visuel')
                    ->size(56)
                    ->square(),

                TextColumn::make('name')
                    ->label('Produit')
                    ->description(fn (Product $record) => \Illuminate\Support\Str::limit($record->niche ?? 'Général', 40))
                    ->searchable()
                    ->sortable()
                    ->weight('bold'),

                TextColumn::make('store.name')
                    ->label('Boutique')
                    ->badge()
                    ->color('gray')
                    ->sortable(),

                TextColumn::make('scripts_count')
                    ->counts('scripts')
                    ->label('Scripts IA')
                    ->badge()
                    ->color('info'),

                TextColumn::make('status')
                    ->label('Statut')
                    ->badge()
                    ->colors([
                        'warning' => 'testing',
                        'success' => 'scaling',
                        'danger' => 'dead',
                    ])
                    ->formatStateUsing(fn (string $state): string => match ($state) {
                        'testing' => '🧪 En test',
                        'scaling' => '🚀 Scaling',
                        'dead' => '💀 Mort',
                        default => $state,
                    }),

                TextColumn::make('created_at')
                    ->label('Créé le')
                    ->dateTime('d/m/Y')
                    ->sortable(),
            ])
            ->filters([
                //
            ])
            ->actions([
                Tables\Actions\EditAction::make(),
            ])
            ->bulkActions([
                Tables\Actions\BulkActionGroup::make([
                    Tables\Actions\DeleteBulkAction::make(),
                ]),
            ]);
    }

    public static function getRelations(): array
    {
        return [
            RelationManagers\ScriptsRelationManager::class,
        ];
    }

    public static function getPages(): array
    {
        return [
            'index' => Pages\ListProducts::route('/'),
            'create' => Pages\CreateProduct::route('/create'),
            'edit' => Pages\EditProduct::route('/{record}/edit'),
        ];
    }
}
