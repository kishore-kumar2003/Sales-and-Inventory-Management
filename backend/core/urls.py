from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ProductViewSet, ProductionViewSet, SaleViewSet, StockHistoryViewSet
)
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

router = DefaultRouter()
router.register(r'products', ProductViewSet, basename='product')
router.register(r'productions', ProductionViewSet, basename='production')
router.register(r'sales', SaleViewSet, basename='sale')
router.register(r'stock-history', StockHistoryViewSet, basename='stock-history')

urlpatterns = [
    path('', include(router.urls)),
    path("login/", TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path("refresh/", TokenRefreshView.as_view(), name='token_refresh'),
]
