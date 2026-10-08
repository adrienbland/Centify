<?php

namespace App\Filament\Resources;

use App\Filament\Resources\TrendResource\Pages;
use App\Filament\Resources\TrendResource\RelationManagers;
use App\Models\Trend;
use Filament\Forms;
use Filament\Forms\Form;
use Filament\Resources\Resource;
use Filament\Tables;
use Filament\Tables\Table;
use Illuminate\Database\Eloquent\Builder;
use Illuminate\Database\Eloquent\SoftDeletingScope;

class TrendResource extends Resource
{
    protected static ?string $model = Trend::class;

    protected static ?string $navigationIcon = 'heroicon-o-sparkles';
    protected static ?string $navigationGroup = 'Radar & Tendances';
    protected static ?int $navigationSort = 0;

    public static function form(Form $form): Form
    {
        return $form
            ->schema([
                Forms\Components\Section::make('Origine TikTok')
                    ->schema([
                        Forms\Components\TextInput::make('extracted_keyword')
                            ->label('Nom générique (Trouvé par IA)'),
                        Forms\Components\TextInput::make('views_count')
                            ->label('Vues TikTok'),
                        Forms\Components\TextInput::make('video_url')
                            ->label('Lien TikTok')
                            ->url(),
                        Forms\Components\Textarea::make('description')
                            ->label('Description Vidéo')
                            ->rows(3),
                        Forms\Components\Select::make('status')
                            ->options([
                                'new' => 'Nouveau',
                                'imported' => 'Importé',
                                'archived' => 'Archivé / Ignoré',
                            ]),
                    ])->columns(2),
            ]);
    }

    public static function table(Table $table): Table
    {
        return $table
            ->columns([
                Tables\Columns\ImageColumn::make('collage_image_path')
                    ->label('Aperçu (4-en-1)')
                    ->size(80),
                Tables\Columns\TextColumn::make('extracted_keyword')
                    ->label('Produit Détecté')
                    ->searchable()
                    ->weight('bold'),
                Tables\Columns\TextColumn::make('views_count')
                    ->label('Vues')
                    ->badge()
                    ->color('success'),
                Tables\Columns\TextColumn::make('status')
                    ->label('Statut')
                    ->badge()
                    ->colors([
                        'warning' => 'new',
                        'success' => 'imported',
                        'gray' => 'archived',
                    ]),
                Tables\Columns\TextColumn::make('created_at')
                    ->label('Détecté le')
                    ->dateTime('d/m/Y')
                    ->sortable(),
            ])
            ->filters([
                //
            ])
            ->actions([
                Tables\Actions\EditAction::make()->label('Inspecter'),
                Tables\Actions\Action::make('archive')
                    ->label('Archiver')
                    ->icon('heroicon-o-archive-box')
                    ->color('gray')
                    ->action(fn (Trend $record) => $record->update(['status' => 'archived']))
                    ->hidden(fn (Trend $record) => $record->status !== 'new'),
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
            RelationManagers\ProposalsRelationManager::class,
        ];
    }

    public static function getPages(): array
    {
        return [
            'index' => Pages\ListTrends::route('/'),
            'create' => Pages\CreateTrend::route('/create'),
            'edit' => Pages\EditTrend::route('/{record}/edit'),
        ];
    }
}
