<?php

namespace App\Filament\Resources\VideoResource\Pages;

use App\Filament\Resources\VideoResource;
use App\Models\Video;
use Filament\Actions;
use Filament\Resources\Pages\ListRecords;
use Filament\Resources\Components\Tab;
use Illuminate\Database\Eloquent\Builder;

class ListVideos extends ListRecords
{
    protected static string $resource = VideoResource::class;

    public function getTabs(): array
    {
        return [
            'all' => Tab::make('Toutes')
                ->badge(Video::count()),
            'rendering' => Tab::make('⚙️ En rendu')
                ->badge(Video::whereIn('status', ['rendering', 'needs_revision'])->count())
                ->badgeColor('warning')
                ->modifyQueryUsing(fn (Builder $query) => $query->whereIn('status', ['rendering', 'needs_revision'])),
            'ready' => Tab::make('✅ Prêtes à publier')
                ->badge(Video::where('status', 'ready')->count())
                ->badgeColor('success')
                ->modifyQueryUsing(fn (Builder $query) => $query->where('status', 'ready')),
            'scheduled' => Tab::make('📅 Planifiées')
                ->modifyQueryUsing(fn (Builder $query) => $query->where('status', 'scheduled')),
            'published' => Tab::make('🚀 Publiées')
                ->modifyQueryUsing(fn (Builder $query) => $query->where('status', 'published')),
            'failed' => Tab::make('❌ Échecs')
                ->badge(Video::where('status', 'failed')->count())
                ->badgeColor('danger')
                ->modifyQueryUsing(fn (Builder $query) => $query->where('status', 'failed')),
        ];
    }

    protected function getHeaderActions(): array
    {
        return [
            Actions\Action::make('refresh')
                ->label('Actualiser')
                ->icon('heroicon-o-arrow-path')
                ->action(fn () => null),
            Actions\CreateAction::make()->label('Nouvelle Vidéo (Manuelle)'),
        ];
    }
}
