from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProductViewSet, BillViewSet, PurchaseHistoryView

# Create a router and register all ViewSets
router = DefaultRouter()
router.register(r"products", ProductViewSet, basename="product")
router.register(r"billing", BillViewSet, basename="billing")

urlpatterns = [
    path("", include(router.urls)),
    path("purchases/<str:customer_email>/", PurchaseHistoryView.as_view(), name="purchase-history"),
]
