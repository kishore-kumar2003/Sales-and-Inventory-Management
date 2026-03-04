from rest_framework.viewsets import ModelViewSet
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.decorators import action
from django.db.models import Sum, Count, Q, F, Avg
from django.utils import timezone
from datetime import timedelta
from .models import Product, Production, Sale, SaleItem, StockHistory
from .serializers import (
    ProductSerializer, ProductionListSerializer, ProductionCreateSerializer,
    SaleListSerializer, SaleDetailSerializer, SaleCreateSerializer,
    StockHistorySerializer
)


# Product ViewSet
class ProductViewSet(ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['is_active', 'name']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'current_stock', 'selling_price', 'created_at']
    ordering = ['-created_at']

    def create(self, request, *args, **kwargs):
        """Custom create with validation"""
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            product = serializer.save()
            # Log the creation
            StockHistory.objects.create(
                product=product,
                transaction_type='PRODUCTION',
                quantity_change=0,
                previous_quantity=0,
                new_quantity=product.current_stock,
                created_by=request.user,
                reference_id=f'PRODUCT_CREATE_{product.id}'
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        """Custom update with change tracking"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        old_stock = instance.current_stock
        
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if serializer.is_valid():
            updated_product = serializer.save()
            
            # Track stock changes
            if old_stock != updated_product.current_stock:
                StockHistory.objects.create(
                    product=updated_product,
                    transaction_type='ADJUSTMENT',
                    quantity_change=updated_product.current_stock - old_stock,
                    previous_quantity=old_stock,
                    new_quantity=updated_product.current_stock,
                    created_by=request.user,
                    reference_id=f'STOCK_ADJUSTMENT_{updated_product.id}'
                )
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        """Custom delete with soft delete"""
        instance = self.get_object()
        instance.is_active = False
        instance.save()
        return Response({'detail': 'Product deactivated successfully'}, status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'])
    def low_stock_alerts(self, request):
        """Get all products with low stock"""
        products = Product.objects.filter(
            Q(current_stock__lte=F('minimum_stock')) & Q(is_active=True)
        )
        serializer = self.get_serializer(products, many=True)
        return Response({
            'count': products.count(),
            'products': serializer.data
        })

    @action(detail=False, methods=['get'])
    def stock_summary(self, request):
        """Get overall stock summary"""
        total_cost_value = Product.objects.aggregate(
            total=Sum(F('current_stock') * F('cost_price'))
        )['total'] or 0
        total_selling_value = Product.objects.aggregate(
            total=Sum(F('current_stock') * F('selling_price'))
        )['total'] or 0
        
        summary = {
            'total_products': Product.objects.filter(is_active=True).count(),
            'inactive_products': Product.objects.filter(is_active=False).count(),
            'low_stock_count': Product.objects.filter(
                current_stock__lte=F('minimum_stock')
            ).count(),
            'total_stock_cost_value': float(total_cost_value),
            'total_stock_selling_value': float(total_selling_value),
            'potential_profit': float(total_selling_value - total_cost_value),
            'avg_profit_margin': self._calculate_avg_margin()
        }
        return Response(summary)

    @action(detail=True, methods=['get'])
    def stock_history(self, request, pk=None):
        """Get stock history for a product"""
        product = self.get_object()
        history = StockHistory.objects.filter(product=product).order_by('-created_at')[:100]
        serializer = StockHistorySerializer(history, many=True)
        return Response({
            'product': ProductSerializer(product).data,
            'history': serializer.data,
            'total_transactions': StockHistory.objects.filter(product=product).count()
        })

    @action(detail=False, methods=['get'])
    def active_products(self, request):
        """Get only active products"""
        products = Product.objects.filter(is_active=True)
        serializer = self.get_serializer(products, many=True)
        return Response({
            'count': products.count(),
            'products': serializer.data
        })

    @action(detail=False, methods=['get'])
    def by_price_range(self, request):
        """Filter products by price range"""
        min_price = request.query_params.get('min_price', 0)
        max_price = request.query_params.get('max_price', float('inf'))
        
        products = Product.objects.filter(
            selling_price__gte=min_price,
            selling_price__lte=max_price,
            is_active=True
        )
        serializer = self.get_serializer(products, many=True)
        return Response({
            'count': products.count(),
            'min_price': min_price,
            'max_price': max_price,
            'products': serializer.data
        })

    @action(detail=False, methods=['get'])
    def profit_analysis(self, request):
        """Get profit analysis for all products"""
        products = Product.objects.filter(is_active=True)
        analysis = []
        
        for product in products:
            analysis.append({
                'id': product.id,
                'name': product.name,
                'cost_price': float(product.cost_price),
                'selling_price': float(product.selling_price),
                'profit_per_unit': float(product.selling_price - product.cost_price),
                'profit_margin': product.get_profit_margin(),
                'current_stock': product.current_stock,
                'total_profit_potential': float((product.selling_price - product.cost_price) * product.current_stock)
            })
        
        return Response({
            'total_products': len(analysis),
            'analysis': sorted(analysis, key=lambda x: x['profit_margin'], reverse=True)
        })

    @action(detail=False, methods=['post'])
    def bulk_update_stock(self, request):
        """Bulk update stock for multiple products"""
        updates = request.data.get('updates', [])
        results = []
        
        for update in updates:
            try:
                product = Product.objects.get(id=update.get('product_id'))
                old_stock = product.current_stock
                product.current_stock = update.get('new_stock', old_stock)
                product.save()
                
                StockHistory.objects.create(
                    product=product,
                    transaction_type='ADJUSTMENT',
                    quantity_change=product.current_stock - old_stock,
                    previous_quantity=old_stock,
                    new_quantity=product.current_stock,
                    created_by=request.user,
                    reference_id=f'BULK_UPDATE_{product.id}'
                )
                results.append({'product_id': product.id, 'status': 'success'})
            except Product.DoesNotExist:
                results.append({'product_id': update.get('product_id'), 'status': 'not_found'})
        
        return Response({'updated': results})

    @action(detail=False, methods=['get'])
    def reorder_list(self, request):
        """Get products that need reordering"""
        products = Product.objects.filter(
            Q(current_stock__lt=F('minimum_stock')) & Q(is_active=True)
        ).order_by('current_stock')
        
        serializer = self.get_serializer(products, many=True)
        return Response({
            'reorder_count': products.count(),
            'products': serializer.data
        })

    def _calculate_avg_margin(self):
        """Helper method to calculate average profit margin"""
        products = Product.objects.filter(is_active=True)
        if not products.exists():
            return 0
        margins = [p.get_profit_margin() for p in products]
        return sum(margins) / len(margins)


# Production ViewSet
class ProductionViewSet(ModelViewSet):
    queryset = Production.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['product', 'produced_by']
    search_fields = ['product__name', 'produced_by__name']
    ordering_fields = ['production_date', 'quantity_produced', 'created_at']
    ordering = ['-production_date', '-created_at']

    def get_serializer_class(self):
        if self.action == 'create' or self.action == 'update' or self.action == 'partial_update':
            return ProductionCreateSerializer
        return ProductionListSerializer

    def create(self, request, *args, **kwargs):
        """Custom create with stock auto-update and validation"""
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            production = serializer.save(produced_by=request.user)
            return Response(ProductionListSerializer(production).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        """Custom update with stock adjustment"""
        instance = self.get_object()
        old_quantity = instance.quantity_produced
        
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        if serializer.is_valid():
            updated_production = serializer.save()
            
            # Adjust stock if quantity changed
            if old_quantity != updated_production.quantity_produced:
                difference = updated_production.quantity_produced - old_quantity
                updated_production.product.current_stock += difference
                updated_production.product.save()
                
                StockHistory.objects.create(
                    product=updated_production.product,
                    transaction_type='PRODUCTION',
                    quantity_change=difference,
                    previous_quantity=updated_production.product.current_stock - difference,
                    new_quantity=updated_production.product.current_stock,
                    created_by=request.user,
                    reference_id=f'PRODUCTION_{updated_production.id}'
                )
            
            return Response(ProductionListSerializer(updated_production).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        """Custom delete with stock reversal"""
        instance = self.get_object()
        product = instance.product
        
        # Reverse the stock increase
        product.current_stock -= instance.quantity_produced
        product.save()
        
        # Log the reversal
        StockHistory.objects.create(
            product=product,
            transaction_type='PRODUCTION',
            quantity_change=-instance.quantity_produced,
            previous_quantity=product.current_stock + instance.quantity_produced,
            new_quantity=product.current_stock,
            created_by=request.user,
            reference_id=f'PRODUCTION_DELETE_{instance.id}'
        )
        
        instance.delete()
        return Response({'detail': 'Production record deleted and stock reversed'}, status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'])
    def by_product(self, request):
        """Get production by product"""
        product_id = request.query_params.get('product_id')
        if product_id:
            productions = Production.objects.filter(product_id=product_id).order_by('-production_date')
            summary = {
                'product_id': product_id,
                'total_quantity': productions.aggregate(Sum('quantity_produced'))['quantity_produced__sum'] or 0,
                'total_productions': productions.count(),
                'productions': ProductionListSerializer(productions, many=True).data
            }
            return Response(summary)
        return Response({'error': 'product_id required'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def date_range(self, request):
        """Get production in date range"""
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        if start_date and end_date:
            productions = Production.objects.filter(
                production_date__range=[start_date, end_date]
            ).order_by('-production_date')
            summary = {
                'start_date': start_date,
                'end_date': end_date,
                'total_quantity': productions.aggregate(Sum('quantity_produced'))['quantity_produced__sum'] or 0,
                'total_count': productions.count(),
                'productions': ProductionListSerializer(productions, many=True).data
            }
            return Response(summary)
        return Response({'error': 'start_date and end_date required'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def monthly_summary(self, request):
        """Get monthly production summary"""
        month = request.query_params.get('month')
        year = request.query_params.get('year')
        if month and year:
            productions = Production.objects.filter(
                production_date__month=month,
                production_date__year=year
            )
            summary = {
                'month': month,
                'year': year,
                'total_quantity': productions.aggregate(Sum('quantity_produced'))['quantity_produced__sum'] or 0,
                'total_productions': productions.count(),
                'products': productions.values('product__name').annotate(
                    total_quantity=Sum('quantity_produced'),
                    count=Count('id'),
                    avg_batch=F('total_quantity') / F('count')
                ),
                'staff': productions.values('produced_by__name').annotate(
                    total_quantity=Sum('quantity_produced'),
                    count=Count('id')
                )
            }
            return Response(summary)
        return Response({'error': 'month and year required'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def by_staff(self, request):
        """Get production records by staff"""
        staff_id = request.query_params.get('staff_id')
        if staff_id:
            productions = Production.objects.filter(produced_by_id=staff_id).order_by('-production_date')
            summary = {
                'staff_id': staff_id,
                'total_quantity': productions.aggregate(Sum('quantity_produced'))['quantity_produced__sum'] or 0,
                'total_productions': productions.count(),
                'productions': ProductionListSerializer(productions, many=True).data
            }
            return Response(summary)
        return Response({'error': 'staff_id required'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def yearly_summary(self, request):
        """Get yearly production summary"""
        year = request.query_params.get('year')
        if year:
            productions = Production.objects.filter(production_date__year=year)
            monthly_data = {}
            
            for month in range(1, 13):
                month_productions = productions.filter(production_date__month=month)
                monthly_data[f'Month-{month}'] = {
                    'quantity': month_productions.aggregate(Sum('quantity_produced'))['quantity_produced__sum'] or 0,
                    'count': month_productions.count()
                }
            
            summary = {
                'year': year,
                'total_quantity': productions.aggregate(Sum('quantity_produced'))['quantity_produced__sum'] or 0,
                'total_productions': productions.count(),
                'monthly_breakdown': monthly_data
            }
            return Response(summary)
        return Response({'error': 'year required'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def performance_stats(self, request):
        """Get production performance statistics"""
        all_productions = Production.objects.all()
        
        stats = {
            'total_quantity_produced': all_productions.aggregate(Sum('quantity_produced'))['quantity_produced__sum'] or 0,
            'total_batch_count': all_productions.count(),
            'avg_batch_size': all_productions.aggregate(Avg('quantity_produced'))['quantity_produced__avg'] or 0,
            'top_producers': all_productions.values('produced_by__name').annotate(
                total=Sum('quantity_produced'),
                batches=Count('id')
            ).order_by('-total')[:5],
            'most_produced_product': all_productions.values('product__name').annotate(
                total=Sum('quantity_produced'),
                batches=Count('id')
            ).order_by('-total').first()
        }
        return Response(stats)


# Sale ViewSet
class SaleViewSet(ModelViewSet):
    queryset = Sale.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['sold_by', 'customer_name']
    search_fields = ['invoice_number', 'customer_name', 'sold_by__name']
    ordering_fields = ['sale_date', 'total_amount', 'created_at']
    ordering = ['-sale_date', '-created_at']

    def get_serializer_class(self):
        if self.action == 'create':
            return SaleCreateSerializer
        elif self.action == 'retrieve':
            return SaleDetailSerializer
        return SaleListSerializer

    def get_queryset(self):
        # Allow users to see only their sales, but admins see all
        if self.request.user.role != 'ADMIN':
            return Sale.objects.filter(sold_by=self.request.user)
        return Sale.objects.all()

    def create(self, request, *args, **kwargs):
        """Custom create with multi-item support and auto-calculation"""
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            sale = serializer.save()
            return Response(SaleDetailSerializer(sale).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        """Custom update with stock adjustment"""
        instance = self.get_object()
        old_total = instance.total_amount
        
        # Reverse old stock changes
        for item in instance.items.all():
            item.product.current_stock += item.quantity_sold
            item.product.save()
            item.delete()
        
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        if serializer.is_valid():
            updated_sale = serializer.save()
            return Response(SaleDetailSerializer(updated_sale).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        """Custom delete with stock reversal"""
        instance = self.get_object()
        
        # Reverse all stock changes
        reversal_items = []
        for item in instance.items.all():
            item.product.current_stock += item.quantity_sold
            item.product.save()
            reversal_items.append(item.product.name)
        
        instance.delete()
        return Response({
            'detail': f'Sale deleted. Stock reversed for: {", ".join(reversal_items)}'
        }, status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'])
    def by_staff(self, request):
        """Get sales by staff member with analytics"""
        staff_id = request.query_params.get('staff_id')
        if staff_id:
            sales = Sale.objects.filter(sold_by_id=staff_id)
            summary = {
                'staff_id': staff_id,
                'total_sales': sales.count(),
                'total_amount': float(sales.aggregate(Sum('total_amount'))['total_amount__sum'] or 0),
                'average_sale': float(sales.aggregate(Avg('total_amount'))['total_amount__avg'] or 0),
                'sales': SaleListSerializer(sales, many=True).data
            }
            return Response(summary)
        return Response({'error': 'staff_id required'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def date_range(self, request):
        """Get sales in date range with summary"""
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        if start_date and end_date:
            sales = Sale.objects.filter(sale_date__range=[start_date, end_date])
            summary = {
                'start_date': start_date,
                'end_date': end_date,
                'total_sales': sales.count(),
                'total_amount': float(sales.aggregate(Sum('total_amount'))['total_amount__sum'] or 0),
                'average_sale': float(sales.aggregate(Avg('total_amount'))['total_amount__avg'] or 0),
                'sales': SaleListSerializer(sales, many=True).data
            }
            return Response(summary)
        return Response({'error': 'start_date and end_date required'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def product_wise_sales(self, request):
        """Get sales analysis by product"""
        product_id = request.query_params.get('product_id')
        if product_id:
            items = SaleItem.objects.filter(product_id=product_id)
            total_revenue = items.aggregate(total_revenue=Sum(F('quantity_sold') * F('unit_price')))['total_revenue'] or 0
            
            summary = {
                'product_id': product_id,
                'total_quantity_sold': items.aggregate(Sum('quantity_sold'))['quantity_sold__sum'] or 0,
                'total_revenue': float(total_revenue),
                'number_of_transactions': items.count(),
                'average_unit_price': float(items.aggregate(Avg('unit_price'))['unit_price__avg'] or 0),
                'total_discount_given': float(items.aggregate(Sum(F('quantity_sold') * F('unit_price') * F('discount') / 100))['quantity_sold__unit_price__discount__sum'] or 0)
            }
            return Response(summary)
        return Response({'error': 'product_id required'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def monthly_report(self, request):
        """Get comprehensive monthly sales report"""
        month = request.query_params.get('month')
        year = request.query_params.get('year')
        if month and year:
            sales = Sale.objects.filter(
                sale_date__month=month,
                sale_date__year=year
            )
            total_items_sold = SaleItem.objects.filter(
                sale__sale_date__month=month,
                sale__sale_date__year=year
            ).count()
            
            report = {
                'month': month,
                'year': year,
                'total_sales_count': sales.count(),
                'total_revenue': float(sales.aggregate(Sum('total_amount'))['total_amount__sum'] or 0),
                'average_sale_value': float(sales.aggregate(Avg('total_amount'))['total_amount__avg'] or 0),
                'total_items_sold': total_items_sold,
                'best_selling_products': SaleItem.objects.filter(
                    sale__sale_date__month=month,
                    sale__sale_date__year=year
                ).values('product__name', 'product__id').annotate(
                    quantity=Sum('quantity_sold'),
                    revenue=Sum(F('quantity_sold') * F('unit_price'))
                ).order_by('-quantity')[:10],
                'top_sales_staff': Sale.objects.filter(
                    sale_date__month=month,
                    sale_date__year=year
                ).values('sold_by__name', 'sold_by__id').annotate(
                    total_sales=Count('id'),
                    total_amount=Sum('total_amount'),
                    avg_sale=Avg('total_amount')
                ).order_by('-total_amount')[:10],
                'worst_selling_products': SaleItem.objects.filter(
                    sale__sale_date__month=month,
                    sale__sale_date__year=year
                ).values('product__name', 'product__id').annotate(
                    quantity=Sum('quantity_sold'),
                    revenue=Sum(F('quantity_sold') * F('unit_price'))
                ).order_by('quantity')[:5]
            }
            return Response(report)
        return Response({'error': 'month and year required'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def best_selling_products(self, request):
        """Get best selling products"""
        limit = request.query_params.get('limit', 10)
        days = request.query_params.get('days', 30)
        
        start_date = timezone.now().date() - timedelta(days=int(days))
        best_sellers = SaleItem.objects.filter(
            sale__sale_date__gte=start_date
        ).values('product__name', 'product__id').annotate(
            total_quantity=Sum('quantity_sold'),
            total_revenue=Sum(F('quantity_sold') * F('unit_price')),
            transaction_count=Count('id')
        ).order_by('-total_quantity')[:int(limit)]
        
        return Response({
            'days': int(days),
            'limit': int(limit),
            'count': len(list(best_sellers)),
            'products': best_sellers
        })

    @action(detail=False, methods=['get'])
    def slow_moving_products(self, request):
        """Get slow moving products"""
        limit = request.query_params.get('limit', 10)
        days = request.query_params.get('days', 90)
        
        start_date = timezone.now().date() - timedelta(days=int(days))
        slow_movers = SaleItem.objects.filter(
            sale__sale_date__gte=start_date
        ).values('product__name', 'product__id').annotate(
            total_quantity=Sum('quantity_sold'),
            total_revenue=Sum(F('quantity_sold') * F('unit_price')),
            transaction_count=Count('id')
        ).order_by('total_quantity')[:int(limit)]
        
        return Response({
            'days': int(days),
            'limit': int(limit),
            'count': len(list(slow_movers)),
            'products': slow_movers
        })

    @action(detail=False, methods=['get'])
    def yearly_summary(self, request):
        """Get yearly sales summary"""
        year = request.query_params.get('year')
        if year:
            sales = Sale.objects.filter(sale_date__year=year)
            monthly_data = {}
            
            for month in range(1, 13):
                month_sales = sales.filter(sale_date__month=month)
                monthly_data[f'Month-{month}'] = {
                    'count': month_sales.count(),
                    'revenue': float(month_sales.aggregate(Sum('total_amount'))['total_amount__sum'] or 0)
                }
            
            summary = {
                'year': year,
                'total_sales': sales.count(),
                'total_revenue': float(sales.aggregate(Sum('total_amount'))['total_amount__sum'] or 0),
                'average_sale': float(sales.aggregate(Avg('total_amount'))['total_amount__avg'] or 0),
                'monthly_breakdown': monthly_data
            }
            return Response(summary)
        return Response({'error': 'year required'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def customer_analysis(self, request):
        """Get customer sales analysis"""
        customer_name = request.query_params.get('customer_name')
        if customer_name:
            sales = Sale.objects.filter(customer_name__icontains=customer_name)
            summary = {
                'customer_name': customer_name,
                'total_purchases': sales.count(),
                'total_spent': float(sales.aggregate(Sum('total_amount'))['total_amount__sum'] or 0),
                'average_purchase': float(sales.aggregate(Avg('total_amount'))['total_amount__avg'] or 0),
                'last_purchase': sales.first().sale_date if sales.exists() else None,
                'purchases': SaleListSerializer(sales, many=True).data
            }
            return Response(summary)
        return Response({'error': 'customer_name required'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def sales_performance(self, request):
        """Get overall sales performance metrics"""
        all_sales = Sale.objects.all()
        
        performance = {
            'total_revenue': float(all_sales.aggregate(Sum('total_amount'))['total_amount__sum'] or 0),
            'total_transactions': all_sales.count(),
            'average_transaction_value': float(all_sales.aggregate(Avg('total_amount'))['total_amount__avg'] or 0),
            'total_items_sold': SaleItem.objects.aggregate(Sum('quantity_sold'))['quantity_sold__sum'] or 0,
            'unique_customers': all_sales.values('customer_name').distinct().count(),
            'top_customer': all_sales.values('customer_name').annotate(
                total=Sum('total_amount'),
                purchases=Count('id')
            ).order_by('-total').first(),
            'top_staff_member': all_sales.values('sold_by__name', 'sold_by__id').annotate(
                total_revenue=Sum('total_amount'),
                sales_count=Count('id')
            ).order_by('-total_revenue').first()
        }
        return Response(performance)


# Stock History ViewSet
class StockHistoryViewSet(ModelViewSet):
    queryset = StockHistory.objects.all()
    serializer_class = StockHistorySerializer
    permission_classes = [permissions.IsAuthenticated]
    read_only_fields = ['id', 'created_at']
    filterset_fields = ['product', 'transaction_type', 'created_by']
    search_fields = ['product__name', 'created_by__name', 'reference_id']
    ordering_fields = ['created_at', 'quantity_change', 'new_quantity']
    ordering = ['-created_at']

    def create(self, request, *args, **kwargs):
        """Prevent direct creation of stock history - it's auto-generated"""
        return Response(
            {'error': 'Stock history is automatically tracked. Use production or sales endpoints instead.'},
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )

    def destroy(self, request, *args, **kwargs):
        """Prevent deletion of stock history - it's an audit trail"""
        return Response(
            {'error': 'Stock history cannot be deleted. It is an immutable audit trail.'},
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )

    def update(self, request, *args, **kwargs):
        """Prevent updates to stock history records"""
        return Response(
            {'error': 'Stock history records cannot be modified.'},
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )

    @action(detail=False, methods=['get'])
    def by_product(self, request):
        """Get stock history for a product"""
        product_id = request.query_params.get('product_id')
        if product_id:
            history = StockHistory.objects.filter(product_id=product_id).order_by('-created_at')[:100]
            summary = {
                'product_id': product_id,
                'total_transactions': history.count(),
                'total_stock_in': history.filter(transaction_type='PRODUCTION').aggregate(Sum('quantity_change'))['quantity_change__sum'] or 0,
                'total_stock_out': abs(history.filter(transaction_type='SALE').aggregate(Sum('quantity_change'))['quantity_change__sum'] or 0),
                'history': StockHistorySerializer(history, many=True).data
            }
            return Response(summary)
        return Response({'error': 'product_id required'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def by_transaction_type(self, request):
        """Get stock history by transaction type"""
        transaction_type = request.query_params.get('type')
        if transaction_type:
            history = StockHistory.objects.filter(transaction_type=transaction_type).order_by('-created_at')
            summary = {
                'transaction_type': transaction_type,
                'total_records': history.count(),
                'total_quantity_changed': history.aggregate(Sum('quantity_change'))['quantity_change__sum'] or 0,
                'history': StockHistorySerializer(history, many=True).data
            }
            return Response(summary)
        return Response({'error': 'type required'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def by_user(self, request):
        """Get stock changes made by a specific user"""
        user_id = request.query_params.get('user_id')
        if user_id:
            history = StockHistory.objects.filter(created_by_id=user_id).order_by('-created_at')
            summary = {
                'user_id': user_id,
                'total_transactions': history.count(),
                'total_quantity_affected': history.aggregate(Sum('quantity_change'))['quantity_change__sum'] or 0,
                'by_type': history.values('transaction_type').annotate(
                    count=Count('id'),
                    total_quantity=Sum('quantity_change')
                ),
                'history': StockHistorySerializer(history, many=True).data
            }
            return Response(summary)
        return Response({'error': 'user_id required'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def date_range(self, request):
        """Get stock history in date range"""
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        if start_date and end_date:
            history = StockHistory.objects.filter(
                created_at__date__range=[start_date, end_date]
            ).order_by('-created_at')
            summary = {
                'start_date': start_date,
                'end_date': end_date,
                'total_transactions': history.count(),
                'total_quantity_changed': history.aggregate(Sum('quantity_change'))['quantity_change__sum'] or 0,
                'by_type': history.values('transaction_type').annotate(
                    count=Count('id'),
                    quantity=Sum('quantity_change')
                ),
                'history': StockHistorySerializer(history, many=True).data
            }
            return Response(summary)
        return Response({'error': 'start_date and end_date required'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def anomalies(self, request):
        """Detect potential stock anomalies"""
        # Find large quantity changes
        large_changes = StockHistory.objects.filter(
            quantity_change__gt=1000
        ).values('product__name').annotate(
            count=Count('id'),
            total_change=Sum('quantity_change')
        ).order_by('-total_change')[:10]
        
        # Find products with negative movements
        negative_movements = StockHistory.objects.filter(
            quantity_change__lt=0
        ).values('product__name').annotate(
            count=Count('id'),
            total_out=Sum('quantity_change')
        ).order_by('-total_out')[:10]
        
        anomalies = {
            'large_movements': large_changes,
            'high_outflow': negative_movements
        }
        return Response(anomalies)

    @action(detail=False, methods=['get'])
    def inventory_movement(self, request):
        """Get inventory movement metrics"""
        product_id = request.query_params.get('product_id')
        days = request.query_params.get('days', 30)
        
        if product_id:
            start_date = timezone.now().date() - timedelta(days=int(days))
            history = StockHistory.objects.filter(
                product_id=product_id,
                created_at__date__gte=start_date
            ).order_by('created_at')
            
            metrics = {
                'product_id': product_id,
                'days': int(days),
                'total_inbound': history.filter(transaction_type='PRODUCTION').aggregate(Sum('quantity_change'))['quantity_change__sum'] or 0,
                'total_outbound': abs(history.filter(transaction_type='SALE').aggregate(Sum('quantity_change'))['quantity_change__sum'] or 0),
                'total_adjustments': history.filter(transaction_type='ADJUSTMENT').aggregate(Sum('quantity_change'))['quantity_change__sum'] or 0,
                'turnover_rate': self._calculate_turnover(product_id, int(days)),
                'movement_history': StockHistorySerializer(history, many=True).data
            }
            return Response(metrics)
        return Response({'error': 'product_id required'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def audit_trail(self, request):
        """Get complete audit trail with filters"""
        filters = {}
        if request.query_params.get('product_id'):
            filters['product_id'] = request.query_params.get('product_id')
        if request.query_params.get('type'):
            filters['transaction_type'] = request.query_params.get('type')
        if request.query_params.get('user_id'):
            filters['created_by_id'] = request.query_params.get('user_id')
        
        history = StockHistory.objects.filter(**filters).order_by('-created_at')[:500]
        
        audit = {
            'filters_applied': filters,
            'total_records': history.count(),
            'records': StockHistorySerializer(history, many=True).data
        }
        return Response(audit)

    def _calculate_turnover(self, product_id, days):
        """Calculate inventory turnover rate"""
        from django.db.models import Q
        
        start_date = timezone.now().date() - timedelta(days=days)
        
        outbound = StockHistory.objects.filter(
            product_id=product_id,
            transaction_type='SALE',
            created_at__date__gte=start_date
        ).aggregate(total=Sum('quantity_change'))['total'] or 0
        
        try:
            product = Product.objects.get(id=product_id)
            if product.current_stock == 0:
                return 0
            return abs(outbound) / product.current_stock
        except Product.DoesNotExist:
            return 0