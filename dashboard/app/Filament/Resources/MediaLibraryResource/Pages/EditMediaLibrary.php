<?php

namespace App\Filament\Resources\MediaLibraryResource\Pages;

use App\Filament\Resources\MediaLibraryResource;
use Filament\Actions;
use Filament\Resources\Pages\EditRecord;

class EditMediaLibrary extends EditRecord
{
    protected static string $resource = MediaLibraryResource::class;

    protected function getHeaderActions(): array
    {
        return [
            Actions\DeleteAction::make(),
        ];
    }
}
