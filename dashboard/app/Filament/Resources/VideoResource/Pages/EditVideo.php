<?php

namespace App\Filament\Resources\VideoResource\Pages;

use App\Filament\Resources\VideoResource;
use Filament\Actions;
use Filament\Resources\Pages\EditRecord;

class EditVideo extends EditRecord
{
    protected static string $resource = VideoResource::class;

    protected function getHeaderActions(): array
    {
        return [
            Actions\Action::make('rerender')
                ->label('🔄 Relancer le rendu avec les retouches')
                ->icon('heroicon-o-sparkles')
                ->color('warning')
                ->requiresConfirmation()
                ->modalHeading('Relancer le montage vidéo IA ?')
                ->modalDescription('Le moteur Python va prendre en compte ton champ "Retouches IA", réécrire le script via Ollama si nécessaire, et générer un nouveau fichier MP4.')
                ->action(function () {
                    $this->save(false);
                    $this->record->update([
                        'status' => !empty($this->record->user_feedback) ? 'needs_revision' : 'rendering',
                    ]);

                    \Filament\Notifications\Notification::make()
                        ->title('Rendu relancé !')
                        ->body('Le worker Python traite ta vidéo en arrière-plan.')
                        ->warning()
                        ->sendToDatabase(auth()->user());
                }),
            Actions\DeleteAction::make(),
        ];
    }
}
