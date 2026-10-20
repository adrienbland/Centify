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
use Filament\Forms\Components\Placeholder;
use Filament\Tables\Columns\TextColumn;
use Illuminate\Support\HtmlString;

class VideoResource extends Resource
{
    protected static ?string $model = Video::class;

    protected static ?string $navigationIcon = 'heroicon-o-video-camera';
    protected static ?string $navigationGroup = 'Studio & Publication';
    protected static ?string $navigationLabel = 'Studio Vidéos (Rendus)';
    protected static ?int $navigationSort = 2;

    public static function getNavigationBadge(): ?string
    {
        $readyCount = static::getModel()::where('status', 'ready')->count();
        return $readyCount > 0 ? (string) $readyCount : null;
    }

    public static function getNavigationBadgeColor(): ?string
    {
        return 'success';
    }

    public static function form(Form $form): Form
    {
        return $form
            ->schema([
                Grid::make(3)->schema([
                    Grid::make(1)->schema([
                        Section::make('🎬 Lecteur Vidéo & Aperçu TikTok (9:16)')
                            ->description('Visionne le rendu final (Voix-Off Edge-TTS + Sous-titres Dynamiques + B-Roll) directement ici.')
                            ->icon('heroicon-m-play-circle')
                            ->schema([
                                Placeholder::make('video_player')
                                    ->label('Aperçu du rendu MP4')
                                    ->content(function (?Video $record): HtmlString {
                                        if (!$record || !$record->file_path || $record->file_path === 'processing...' || $record->status === 'rendering') {
                                            return new HtmlString('
                                                <div class="p-6 rounded-xl bg-gray-900/60 border border-purple-500/30 text-center space-y-2">
                                                    <div class="text-purple-400 font-semibold text-base">⚙️ Montage IA en cours d\'exécution...</div>
                                                    <p class="text-xs text-gray-400">Le moteur Python (Edge-TTS + MoviePy) génère actuellement la voix-off et les sous-titres. Cette page se mettra à jour dès la fin du rendu.</p>
                                                </div>
                                            ');
                                        }

                                        $src = htmlspecialchars($record->file_path, ENT_QUOTES, 'UTF-8');
                                        $duration = $record->duration_seconds ? "{$record->duration_seconds}s" : '9:16';

                                        return new HtmlString("
                                            <div class='flex flex-col items-center space-y-3 p-4 rounded-xl bg-gray-950/70 border border-purple-500/30'>
                                                <video controls playsinline preload='metadata' style='max-height: 520px; width: auto; border-radius: 12px; box-shadow: 0 10px 25px rgba(0,0,0,0.5);'>
                                                    <source src='{$src}' type='video/mp4'>
                                                    Ton navigateur ne supporte pas la lecture vidéo HTML5.
                                                </video>
                                                <div class='flex items-center gap-4 text-xs text-gray-400'>
                                                    <span>⏱️ Durée : <strong class='text-white'>{$duration}</strong></span>
                                                    <span>•</span>
                                                    <a href='{$src}' target='_blank' download class='text-purple-400 hover:underline font-medium'>⬇️ Télécharger le fichier MP4</a>
                                                </div>
                                            </div>
                                        ");
                                    }),

                                Placeholder::make('script_preview')
                                    ->label('Texte du Script prononcé par la voix IA')
                                    ->content(fn (?Video $record): string => $record?->script?->full_text ?? 'Aucun script lié.'),

                                Textarea::make('user_feedback')
                                    ->label('Retouches IA (Feedback Loop)')
                                    ->placeholder('Ex: Rends l\'accroche plus agressive, parle du fait que la livraison est offerte aujourd\'hui...')
                                    ->rows(3)
                                    ->hint('Écris ta consigne puis passe le statut à "🔄 À refaire (IA)" (ou clique sur le bouton en haut) pour que Python réécrive le script et refasse le montage automatiquement.'),
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
                                    ->live(),

                                Select::make('social_network')
                                    ->label('Réseau cible')
                                    ->options([
                                        'tiktok' => 'TikTok',
                                        'youtube' => 'YouTube Shorts',
                                        'instagram' => 'Instagram Reels',
                                    ])
                                    ->required(),

                                TextInput::make('duration_seconds')
                                    ->label('Durée (secondes)')
                                    ->disabled()
                                    ->suffix('sec'),

                                TextInput::make('file_path')
                                    ->label('Chemin du Fichier')
                                    ->disabled(),

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

                                Select::make('script_id')
                                    ->label('Script associé')
                                    ->relationship('script', 'hook')
                                    ->searchable()
                                    ->preload(),
                            ]),
                    ])->columnSpan(1),
                ]),
            ]);
    }

    public static function table(Table $table): Table
    {
        return $table
            ->poll('5s')
            ->defaultSort('updated_at', 'desc')
            ->columns([
                TextColumn::make('id')
                    ->label('#')
                    ->sortable(),

                TextColumn::make('product.name')
                    ->label('Produit')
                    ->limit(35)
                    ->weight('bold')
                    ->sortable()
                    ->searchable(),

                TextColumn::make('script.hook')
                    ->label('Accroche (Hook)')
                    ->limit(40)
                    ->color('gray'),

                TextColumn::make('social_network')
                    ->label('Réseau')
                    ->badge()
                    ->colors([
                        'primary' => 'tiktok',
                        'danger' => 'youtube',
                        'warning' => 'instagram',
                    ]),

                TextColumn::make('duration_seconds')
                    ->label('Durée')
                    ->formatStateUsing(fn ($state) => $state ? "{$state}s" : '—')
                    ->badge()
                    ->color('gray'),

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
                    ])
                    ->formatStateUsing(fn (string $state): string => match ($state) {
                        'rendering' => '⚙️ En rendu...',
                        'ready' => '✅ Prête',
                        'needs_revision' => '🔄 Retouche IA...',
                        'scheduled' => '📅 Planifiée',
                        'published' => '🚀 Publiée',
                        'failed' => '❌ Échec',
                        default => $state,
                    }),

                TextColumn::make('updated_at')
                    ->label('Mis à jour')
                    ->since()
                    ->sortable(),
            ])
            ->filters([
                //
            ])
            ->actions([
                Tables\Actions\Action::make('preview')
                    ->label('Visionner')
                    ->icon('heroicon-o-play')
                    ->color('success')
                    ->visible(fn (Video $record) => $record->status === 'ready' && !empty($record->file_path) && $record->file_path !== 'processing...')
                    ->modalHeading(fn (Video $record) => "🎬 Aperçu : " . ($record->product?->name ?? "Vidéo #{$record->id}"))
                    ->modalSubmitAction(false)
                    ->modalCancelActionLabel('Fermer')
                    ->modalContent(function (Video $record): HtmlString {
                        $src = htmlspecialchars($record->file_path, ENT_QUOTES, 'UTF-8');
                        $script = htmlspecialchars($record->script?->full_text ?? '', ENT_QUOTES, 'UTF-8');
                        return new HtmlString("
                            <div class='flex flex-col items-center space-y-4'>
                                <video controls autoplay playsinline style='max-height: 540px; width: auto; border-radius: 12px;'>
                                    <source src='{$src}' type='video/mp4'>
                                </video>
                                <div class='w-full p-3 rounded-lg bg-gray-900 text-xs text-gray-300 border border-gray-800'>
                                    <strong>Script vocal :</strong> {$script}
                                </div>
                            </div>
                        ");
                    }),

                Tables\Actions\Action::make('request_revision')
                    ->label('Retoucher (IA)')
                    ->icon('heroicon-o-arrow-path-rounded-square')
                    ->color('warning')
                    ->visible(fn (Video $record) => in_array($record->status, ['ready', 'failed']))
                    ->modalHeading('🔄 Demander une retouche au moteur IA')
                    ->modalDescription('Ollama va réécrire le script selon ta consigne et le moteur Python va régénérer la voix-off et la vidéo MP4.')
                    ->form([
                        Textarea::make('user_feedback')
                            ->label('Consigne de modification')
                            ->placeholder('Ex: Fais une accroche plus courte et plus choc, ou parle de la garantie satisfait ou remboursé...')
                            ->default(fn (Video $record) => $record->user_feedback)
                            ->required(),
                    ])
                    ->action(function (Video $record, array $data) {
                        $record->update([
                            'user_feedback' => $data['user_feedback'],
                            'status' => 'needs_revision',
                        ]);

                        \Filament\Notifications\Notification::make()
                            ->title('Retouche IA envoyée au moteur vidéo !')
                            ->body('La vidéo va être régénérée automatiquement d\'ici quelques secondes.')
                            ->warning()
                            ->sendToDatabase(auth()->user());
                    }),

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
            \App\Filament\Resources\VideoResource\RelationManagers\VariantsRelationManager::class,
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
