<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::table('trends', function (Blueprint $table) {
            $table->string('extracted_keyword')->nullable();
            $table->string('collage_image_path')->nullable();
            $table->string('status')->default('new');
        });
    }

    public function down(): void
    {
        Schema::table('trends', function (Blueprint $table) {
            $table->dropColumn(['extracted_keyword', 'collage_image_path', 'status']);
        });
    }
};
