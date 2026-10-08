<?php

namespace App\Filament\Resources;

use App\Filament\Resources\VideoResource\Pages;
use App\Models\Video;
use Filament\Forms;
use Filament\Forms\Form;
use Filament\Resources\Resource;
use Filament\Tables;
use Filament\Tables\Table;
use Filament\Forms\Components\Section;
use Filament\Forms\Components\Grid;
use Filament\Forms\Components\Select;
use Filament\Forms\Components\Textarea;
use Filament\Forms\Components\TextInput;
use Filament\Forms\Components\DateTimePicker;
use Filament\Tables\Columns\TextColumn;
use Filament\Tables\Columns\BadgeColumn;

class VideoResource extends Resource
{
    protected static ?string $model = Video::class;

    protected static ?string $navigationIcon = 'heroicon-o-video-camera';
    protected static ?string $navigationGroup = 'Studio & Publication';
    protected static ?int $navigationSort = 2;

    public static function form(Form $form): Form
    {
        return $form
            ->schema([
                Grid::make(3)->schema([
                    Grid::make(1)->schema([
                        Section::make('Le Lecteur & Feedback')
                            ->description('Visionne la vidéo générée et donne tes consignes de retouche à Python.')
                            ->icon('heroicon-m-play-circle')
                            ->schema([
                                // En réalité, ici on créerait un composant Vue/Livewire sur-mesure pour afficher la vidéo locale
                                TextInput::make('file_path')
                                    ->label('Chemin du Fichier')
                                    ->disabled()
                                    ->hint('Aperçu vidéo natif à implémenter via un composant custom Filament.'),
                                
                                Textarea::make('user_feedback')
                                    ->label('Retouches IA (Commentaire manuel)')
                                    ->placeholder('Ex: Change la musique de fond par quelque chose de plus joyeux, et corrige la faute à 00:04.')
                                    ->rows(3)
                                    ->hint('Remplis ce champ et passe le statut en "À refaire" pour relancer le moteur Python.'),
                            ]),
                    ])->columnSpan(2),

                    Grid::make(1)->schema([
                        Section::make('Orchestration')
                            ->schema([
                                Select::make('status')
                                    ->label('Statut du Rendu')
                                    ->options([
                                        'rendering' => '⚙️ En rendu',
                                        'ready' => '✅ Prête',
                                        'needs_revision' => '🔄 À refaire (IA)',
                                        'scheduled' => '📅 Planifiée',
                                        'published' => '🚀 Publiée',
                                        'failed' => '❌ Échec',
                                    ])
                                    ->required()
                                    ->live(), // Pour rendre le champ réactif

                                Select::make('social_network')
                                    ->label('Réseau cible')
                                    ->options([
                                        'tiktok' => 'TikTok',
                                        'youtube' => 'YouTube Shorts',
                                        'instagram' => 'Instagram Reels',
                                    ])
                                    ->required(),

                                DateTimePicker::make('scheduled_at')
                                    ->label('Planifiée pour')
                                    ->hidden(fn (Forms\Get $get) => $get('status') !== 'scheduled'),
                            ]),

                        Section::make('Liaisons')
                            ->schema([
                                Select::make('product_id')
                                    ->label('Produit associé')
                                    ->relationship('product', 'name')
                                    ->searchable()
                                    ->preload()
                                    ->required(),
                            ]),
                    ])->columnSpan(1),
                ]),
            ]);
    }

    public static function table(Table $table): Table
    {
        return $table
            ->columns([
                TextColumn::make('product.name')
                    ->label('Produit')
                    ->sortable()
                    ->searchable(),

                TextColumn::make('social_network')
                    ->label('Réseau')
                    ->badge()
                    ->colors([
                        'primary' => 'tiktok',
                        'danger' => 'youtube',
                        'warning' => 'instagram',
                    ]),

                TextColumn::make('status')
                    ->label('Statut')
                    ->badge()
                    ->colors([
                        'gray' => 'rendering',
                        'success' => 'ready',
                        'warning' => 'needs_revision',
                        'info' => 'scheduled',
                        'primary' => 'published',
                        'danger' => 'failed',
                    ]),
                
                TextColumn::make('scheduled_at')
                    ->label('Heure de publication')
                    ->dateTime('d/m/Y H:i')
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
            // On ajoutera plus tard le RelationManager pour les "VideoVariants" (Le Hook Tester)
        ];
    }

    public static function getPages(): array
    {
        return [
            'index' => Pages\ListVideos::route('/'),
            'create' => Pages\CreateVideo::route('/create'),
            'edit' => Pages\EditVideo::route('/{record}/edit'),
        ];
    }
}
