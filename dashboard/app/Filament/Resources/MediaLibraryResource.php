<?php

namespace App\Filament\Resources;

use App\Filament\Resources\MediaLibraryResource\Pages;
use App\Models\MediaLibrary;
use Filament\Forms;
use Filament\Forms\Form;
use Filament\Resources\Resource;
use Filament\Tables;
use Filament\Tables\Table;

class MediaLibraryResource extends Resource
{
    protected static ?string $model = MediaLibrary::class;

    protected static ?string $navigationIcon = 'heroicon-o-musical-note';
    protected static ?string $navigationGroup = 'Studio & Publication';
    protected static ?string $navigationLabel = 'Médiathèque (B-Rolls & Sons)';
    protected static ?int $navigationSort = 3;

    public static function form(Form $form): Form
    {
        return $form
            ->schema([
                Forms\Components\Section::make('Ajouter un Asset au Studio Vidéo')
                    ->description('Les B-Rolls et musiques ajoutés ici seront automatiquement utilisés par le moteur Python lors des montages.')
                    ->schema([
                        Forms\Components\TextInput::make('name')
                            ->label('Nom de l\'asset')
                            ->placeholder('Ex: Fond Satisfaisant Savon 9:16 ou Musique Phonk TikTok')
                            ->required()
                            ->maxLength(255),

                        Forms\Components\Select::make('type')
                            ->label('Type de média')
                            ->options([
                                'b_roll' => '🎬 Vidéo de fond (B-Roll)',
                                'audio' => '🎵 Musique de fond (Audio)',
                                'font' => '🔤 Police d\'écriture (.ttf)',
                                'transition' => '⚡ Transition vidéo',
                            ])
                            ->default('b_roll')
                            ->required(),

                        Forms\Components\FileUpload::make('file_path')
                            ->label('Fichier Média (.mp4, .mp3, .ttf)')
                            ->disk('medias')
                            ->directory('library')
                            ->preserveFilenames()
                            ->required()
                            ->columnSpanFull(),

                        Forms\Components\TextInput::make('tags')
                            ->label('Tags (séparés par des virgules)')
                            ->placeholder('Ex: tiktok, dynamique, tech, satisfaisant')
                            ->columnSpanFull(),
                    ])->columns(2),
            ]);
    }

    public static function table(Table $table): Table
    {
        return $table
            ->columns([
                Tables\Columns\TextColumn::make('name')
                    ->label('Nom')
                    ->weight('bold')
                    ->searchable()
                    ->sortable(),

                Tables\Columns\TextColumn::make('type')
                    ->label('Type')
                    ->badge()
                    ->colors([
                        'primary' => 'b_roll',
                        'success' => 'audio',
                        'warning' => 'font',
                        'info' => 'transition',
                    ])
                    ->formatStateUsing(fn (string $state): string => match ($state) {
                        'b_roll' => '🎬 B-Roll Vidéo',
                        'audio' => '🎵 Musique',
                        'font' => '🔤 Police',
                        'transition' => '⚡ Transition',
                        default => $state,
                    }),

                Tables\Columns\TextColumn::make('file_path')
                    ->label('Chemin (Public)')
                    ->color('gray'),

                Tables\Columns\TextColumn::make('tags')
                    ->label('Tags')
                    ->badge()
                    ->separator(','),

                Tables\Columns\TextColumn::make('created_at')
                    ->label('Ajouté le')
                    ->dateTime('d/m/Y H:i')
                    ->sortable(),
            ])
            ->filters([
                Tables\Filters\SelectFilter::make('type')
                    ->options([
                        'b_roll' => 'B-Roll Vidéo',
                        'audio' => 'Musique Audio',
                        'font' => 'Police',
                        'transition' => 'Transition',
                    ]),
            ])
            ->actions([
                Tables\Actions\EditAction::make(),
                Tables\Actions\DeleteAction::make(),
            ])
            ->bulkActions([
                Tables\Actions\BulkActionGroup::make([
                    Tables\Actions\DeleteBulkAction::make(),
                ]),
            ]);
    }

    public static function getPages(): array
    {
        return [
            'index' => Pages\ListMediaLibraries::route('/'),
            'create' => Pages\CreateMediaLibrary::route('/create'),
            'edit' => Pages\EditMediaLibrary::route('/{record}/edit'),
        ];
    }
}
