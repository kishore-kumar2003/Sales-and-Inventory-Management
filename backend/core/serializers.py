from rest_framework import serializers
from .models import Product, Production, Sale, SaleItem, StockHistory
from accounts.models import User


# User Serializer
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'name', 'role', 'salary', 'is_active']


# Product Serializer
class ProductSerializer(serializers.ModelSerializer):
    profit_margin = serializers.SerializerMethodField()
    low_stock_alert = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ['id', 'name', 'description', 'cost_price', 'selling_price', 'minimum_stock',
                  'current_stock', 'low_stock_alert', 'profit_margin', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_profit_margin(self, obj):
        return obj.get_profit_margin()

    def get_low_stock_alert(self, obj):
        return obj.low_stock_alert


# Production Serializer
class ProductionListSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    produced_by_name = serializers.CharField(source='produced_by.name', read_only=True)

    class Meta:
        model = Production
        fields = ['id', 'product', 'product_name', 'quantity_produced', 'produced_by', 'produced_by_name',
                  'production_date', 'notes', 'created_at']
        read_only_fields = ['id', 'created_at']


class ProductionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Production
        fields = ['product', 'quantity_produced', 'production_date', 'notes']

    def create(self, validated_data):
        validated_data['produced_by'] = self.context['request'].user
        return super().create(validated_data)


# Sale Item Serializer
class SaleItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    item_total = serializers.SerializerMethodField()

    class Meta:
        model = SaleItem
        fields = ['id', 'product', 'product_name', 'quantity_sold', 'unit_price', 'discount', 'item_total']
        read_only_fields = ['id']

    def get_item_total(self, obj):
        return obj.get_item_total()


# Sale Serializer
class SaleListSerializer(serializers.ModelSerializer):
    sold_by_name = serializers.CharField(source='sold_by.name', read_only=True)
    item_count = serializers.SerializerMethodField()

    class Meta:
        model = Sale
        fields = ['id', 'invoice_number', 'customer_name', 'sold_by', 'sold_by_name', 'total_amount',
                  'sale_date', 'item_count', 'created_at']
        read_only_fields = ['id', 'total_amount', 'created_at']

    def get_item_count(self, obj):
        return obj.items.count()


class SaleDetailSerializer(serializers.ModelSerializer):
    sold_by_name = serializers.CharField(source='sold_by.name', read_only=True)
    items = SaleItemSerializer(many=True, read_only=True)

    class Meta:
        model = Sale
        fields = ['id', 'invoice_number', 'customer_name', 'sold_by', 'sold_by_name', 'total_amount',
                  'sale_date', 'notes', 'items', 'created_at', 'updated_at']
        read_only_fields = ['id', 'total_amount', 'created_at', 'updated_at']


class SaleCreateSerializer(serializers.Serializer):
    customer_name = serializers.CharField(max_length=200)
    invoice_number = serializers.CharField(max_length=50)
    sale_date = serializers.DateField()
    notes = serializers.CharField(required=False, allow_blank=True)
    items = SaleItemSerializer(many=True)

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        sale = Sale.objects.create(
            sold_by=self.context['request'].user,
            **validated_data
        )
        for item_data in items_data:
            SaleItem.objects.create(sale=sale, **item_data)
        sale.calculate_total()
        return sale


# Stock History Serializer
class StockHistorySerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.name', read_only=True)

    class Meta:
        model = StockHistory
        fields = ['id', 'product', 'product_name', 'transaction_type', 'quantity_change',
                  'previous_quantity', 'new_quantity', 'reference_id', 'created_by', 'created_by_name', 'created_at']
        read_only_fields = ['id', 'created_at']
