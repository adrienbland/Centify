<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;

class TrendProposal extends Model
{
    protected $guarded = [];

    public function trend(): BelongsTo
    {
        return $this->belongsTo(Trend::class);
    }
}
