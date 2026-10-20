<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::table('products', function (Blueprint $table) {
            if (!Schema::hasColumn('products', 'image_url')) {
                $table->string('image_url')->nullable()->after('name');
            }
            if (!Schema::hasColumn('products', 'supplier_url')) {
                $table->string('supplier_url')->nullable()->after('image_url');
            }
        });

        Schema::table('trend_proposals', function (Blueprint $table) {
            if (!Schema::hasColumn('trend_proposals', 'description')) {
                $table->text('description')->nullable()->after('title');
            }
        });
    }

    public function down(): void
    {
        Schema::table('products', function (Blueprint $table) {
            $table->dropColumn(['image_url', 'supplier_url']);
        });

        Schema::table('trend_proposals', function (Blueprint $table) {
            $table->dropColumn(['description']);
        });
    }
};
