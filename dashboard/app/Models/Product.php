<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;

class Product extends Model
{
    protected $guarded = [];

    public function store()
    {
        return $this->belongsTo(Store::class);
    }

    public function category()
    {
        return $this->belongsTo(Category::class);
    }

    public function defaultTiktokAccount()
    {
        return $this->belongsTo(SocialAccount::class, 'default_tiktok_account_id');
    }
}
