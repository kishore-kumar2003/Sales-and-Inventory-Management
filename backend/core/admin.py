from django.contrib import admin
from .models import Product, Production, Sale, SaleItem, StockHistory


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'cost_price', 'selling_price', 'current_stock', 'minimum_stock', 'low_stock_alert', 'is_active']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Production)
class ProductionAdmin(admin.ModelAdmin):
    list_display = ['product', 'quantity_produced', 'produced_by', 'production_date', 'created_at']
    list_filter = ['production_date', 'product']
    search_fields = ['product__name', 'produced_by__name']
    readonly_fields = ['created_at']


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ['invoice_number', 'customer_name', 'sold_by', 'total_amount', 'sale_date']
    list_filter = ['sale_date', 'sold_by']
    search_fields = ['invoice_number', 'customer_name', 'sold_by__name']
    readonly_fields = ['created_at', 'updated_at', 'total_amount']


@admin.register(SaleItem)
class SaleItemAdmin(admin.ModelAdmin):
    list_display = ['sale', 'product', 'quantity_sold', 'unit_price', 'discount']
    list_filter = ['sale__sale_date', 'product']
    search_fields = ['sale__invoice_number', 'product__name']


@admin.register(StockHistory)
class StockHistoryAdmin(admin.ModelAdmin):
    list_display = ['product', 'transaction_type', 'quantity_change', 'new_quantity', 'created_by', 'created_at']
    list_filter = ['transaction_type', 'created_at', 'product']
    search_fields = ['product__name', 'created_by__name']
    readonly_fields = ['created_at']