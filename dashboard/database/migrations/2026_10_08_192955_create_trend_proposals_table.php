<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    /**
     * Run the migrations.
     */
    public function up(): void
    {
        Schema::create('trend_proposals', function (Blueprint $table) {
            $table->id();
            $table->foreignId('trend_id')->constrained()->cascadeOnDelete();
            $table->string('aliexpress_url')->nullable();
            $table->string('title')->nullable();
            $table->decimal('price', 8, 2)->nullable();
            $table->integer('orders')->default(0);
            $table->string('image_url')->nullable();
            $table->timestamps();
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::dropIfExists('trend_proposals');
    }
};
