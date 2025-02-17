from rest_framework import serializers
from .models import Product, Bill, PurchaseHistory

class ProductSerializer(serializers.ModelSerializer):
    name = serializers.CharField(max_length=255, required=True)
    product_id = serializers.CharField(max_length=50, required=True)
    available_stock = serializers.IntegerField(min_value=0, required=True)
    price = serializers.FloatField(min_value=0.01, required=True)
    tax_percentage = serializers.FloatField(min_value=0, max_value=100, required=True)

    class Meta:
        model = Product
        fields = "__all__"

class BillSerializer(serializers.ModelSerializer):
    customer_email = serializers.EmailField(required=True)
    total_amount = serializers.FloatField(min_value=0, required=True)
    paid_amount = serializers.FloatField(min_value=0, required=True)
    balance_amount = serializers.FloatField(read_only=True)

    class Meta:
        model = Bill
        fields = "__all__"

class PurchaseHistorySerializer(serializers.ModelSerializer):
    customer_email = serializers.EmailField(required=True)
    quantity = serializers.IntegerField(min_value=1, required=True)

    class Meta:
        model = PurchaseHistory
        fields = "__all__"
