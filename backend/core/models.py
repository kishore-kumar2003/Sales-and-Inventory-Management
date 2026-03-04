from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
from accounts.models import User


# Product Management
class Product(models.Model):
    name = models.CharField(max_length=200, unique=True)
    description = models.TextField(blank=True, null=True)
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    selling_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    minimum_stock = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    current_stock = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    @property
    def low_stock_alert(self):
        return self.current_stock <= self.minimum_stock

    def get_profit_margin(self):
        if self.selling_price == 0:
            return 0
        return ((self.selling_price - self.cost_price) / self.selling_price) * 100


# Production Management
class Production(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='productions')
    quantity_produced = models.IntegerField(validators=[MinValueValidator(1)])
    produced_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='productions')
    production_date = models.DateField(default=timezone.now)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-production_date', '-created_at']

    def __str__(self):
        return f"{self.product.name} - {self.quantity_produced} units on {self.production_date}"

    def save(self, *args, **kwargs):
        # Auto-update current stock when production is created
        if not self.pk:  # Only for new records
            self.product.current_stock += self.quantity_produced
            self.product.save()
        super().save(*args, **kwargs)


# Sales Management
class Sale(models.Model):
    invoice_number = models.CharField(max_length=50, unique=True)
    customer_name = models.CharField(max_length=200)
    sold_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='sales')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    sale_date = models.DateField(default=timezone.now)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-sale_date', '-created_at']

    def __str__(self):
        return f"Invoice {self.invoice_number}"

    def calculate_total(self):
        total = sum(item.get_item_total() for item in self.items.all())
        self.total_amount = total
        self.save()
        return total


class SaleItem(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, related_name='sale_items')
    quantity_sold = models.IntegerField(validators=[MinValueValidator(1)])
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    discount = models.DecimalField(max_digits=5, decimal_places=2, default=0)  # percentage

    def __str__(self):
        return f"{self.product.name} - {self.quantity_sold} units"

    def get_item_total(self):
        subtotal = float(self.quantity_sold) * float(self.unit_price)
        discount_amount = (subtotal * float(self.discount)) / 100
        return subtotal - discount_amount

    def save(self, *args, **kwargs):
        # Auto-reduce stock when sale item is created
        if not self.pk:  # Only for new records
            if self.product.current_stock < self.quantity_sold:
                raise ValueError(f"Insufficient stock. Available: {self.product.current_stock}")
            self.product.current_stock -= self.quantity_sold
            self.product.save()
        super().save(*args, **kwargs)


# Stock History (Audit Trail)
class StockHistory(models.Model):
    TRANSACTION_TYPES = (
        ('PRODUCTION', 'Production'),
        ('SALE', 'Sale'),
        ('ADJUSTMENT', 'Adjustment'),
    )

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='stock_history')
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    quantity_change = models.IntegerField()
    previous_quantity = models.IntegerField()
    new_quantity = models.IntegerField()
    reference_id = models.CharField(max_length=100, blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='stock_changes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.product.name} - {self.transaction_type}"
