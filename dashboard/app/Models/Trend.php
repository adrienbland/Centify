<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\HasMany;

class Trend extends Model
{
    protected $guarded = [];

    public function proposals(): HasMany
    {
        return $this->hasMany(TrendProposal::class);
    }
}
