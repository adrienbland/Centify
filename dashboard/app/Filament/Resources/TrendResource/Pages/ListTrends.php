<?php

namespace App\Filament\Resources\TrendResource\Pages;

use App\Filament\Resources\TrendResource;
use Filament\Actions;
use Filament\Resources\Pages\ListRecords;
use Filament\Resources\Components\Tab;
use Illuminate\Database\Eloquent\Builder;

class ListTrends extends ListRecords
{
    protected static string $resource = TrendResource::class;

    public function getTabs(): array
    {
        return [
            'new' => Tab::make('Nouvelles Tendances')
                ->icon('heroicon-m-sparkles')
                ->badge(\App\Models\Trend::where('status', 'new')->count())
                ->modifyQueryUsing(fn (Builder $query) => $query->where('status', 'new')),
            'imported' => Tab::make('Déjà Importés')
                ->icon('heroicon-m-check-circle')
                ->modifyQueryUsing(fn (Builder $query) => $query->where('status', 'imported')),
            'archived' => Tab::make('Historique (Archivés)')
                ->icon('heroicon-m-archive-box')
                ->modifyQueryUsing(fn (Builder $query) => $query->where('status', 'archived')),
            'all' => Tab::make('Tout afficher'),
        ];
    }

    protected function getHeaderActions(): array
    {
        return [
            Actions\CreateAction::make()->label('Nouvelle Tendance (Manuelle)'),
        ];
    }
}
