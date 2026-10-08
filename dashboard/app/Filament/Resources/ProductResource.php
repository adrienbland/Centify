<?php

namespace App\Filament\Resources;

use App\Filament\Resources\ProductResource\Pages;
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
use Filament\Tables\Columns\TextColumn;
use Filament\Tables\Columns\BadgeColumn;

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
                        Section::make('Informations du Produit')
                            ->description('Les détails de base de ton winner potentiel.')
                            ->icon('heroicon-m-cube')
                            ->schema([
                                TextInput::make('name')
                                    ->label('Nom du Produit')
                                    ->required()
                                    ->maxLength(255),
                                
                                TextInput::make('niche')
                                    ->label('Niche (ex: Tech, Beauté)')
                                    ->maxLength(100),

                                MarkdownEditor::make('description')
                                    ->label('Description Marketing')
                                    ->columnSpanFull(),
                            ])->columns(2),

                        Section::make('Intelligence Artificielle (Le Cerveau)')
                            ->description('Donne tes directives manuelles à Ollama pour la rédaction des scripts.')
                            ->icon('heroicon-m-cpu-chip')
                            ->schema([
                                Textarea::make('ai_custom_prompt')
                                    ->label('Directives IA Manuelles')
                                    ->placeholder('Ex: Insiste sur le fait que la livraison est gratuite et que le produit soulage le mal de dos en 5 minutes...')
                                    ->rows(4)
                                    ->columnSpanFull()
                                    ->hint('Ces instructions seront injectées dans le prompt system de l\'IA.'),
                            ]),
                    ])->columnSpan(2),

                    // Colonne Latérale (1/3)
                    Grid::make(1)->schema([
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
            ->columns([
                TextColumn::make('name')
                    ->label('Produit')
                    ->searchable()
                    ->sortable()
                    ->weight('bold'),
                    
                TextColumn::make('store.name')
                    ->label('Boutique')
                    ->badge()
                    ->color('gray')
                    ->sortable(),

                TextColumn::make('status')
                    ->label('Statut')
                    ->badge()
                    ->colors([
                        'warning' => 'testing',
                        'success' => 'scaling',
                        'danger' => 'dead',
                    ])
                    ->formatStateUsing(fn (string $state): string => match ($state) {
                        'testing' => 'En test',
                        'scaling' => 'Scaling',
                        'dead' => 'Mort',
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
        return [];
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
