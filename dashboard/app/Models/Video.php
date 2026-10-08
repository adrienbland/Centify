<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;

class Video extends Model
{
    protected $guarded = [];

    public function product()
    {
        return $this->belongsTo(Product::class);
    }

    public function script()
    {
        return $this->belongsTo(Script::class);
    }

    public function variants()
    {
        return $this->hasMany(VideoVariant::class);
    }
}
