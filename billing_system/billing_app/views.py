from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics, viewsets
from .models import Product, Bill, PurchaseHistory
from .serializers import BillSerializer, PurchaseHistorySerializer, ProductSerializer
from .constants import NOT_FOUND
from .tasks import send_invoice_email
from django.db.models import Q
import re
from rest_framework.exceptions import APIException
from rest_framework.decorators import action

def is_valid_email(email):
    return re.match(r"[^@]+@[^@]+\.[^@]+", email)

class BillViewSet(viewsets.ViewSet):
    """
    ViewSet for handling all Billing operations.
    Supports:
    - GET (list all, filter by customer, amount, and date range)
    - POST (create a bill)
    """
    
    def list(self, request):
        """Retrieve all bills with optional filtering."""
        try:
            queryset = Bill.objects.all()
            id = request.query_params.get("id")
            customer_email = request.query_params.get("customer_email")
            min_amount = request.query_params.get("min_amount")
            max_amount = request.query_params.get("max_amount")
            start_date = request.query_params.get("start_date")
            end_date = request.query_params.get("end_date")

            if id:
                queryset = queryset.filter(id=id)
            if customer_email:
                queryset = queryset.filter(customer_email__iexact=customer_email)
            if min_amount and max_amount:
                queryset = queryset.filter(total_amount__gte=min_amount, total_amount__lte=max_amount)
            if start_date and end_date:
                queryset = queryset.filter(created_at__range=[start_date, end_date])

            serializer = BillSerializer(queryset, many=True)
            return Response({"status": "success","data":serializer.data}, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response({"status": "fail","error": f"Error fetching bills: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def create(self, request):
        """Create a new bill with input validation and error handling."""
        try:
            data = request.data
            customer_email = data.get("customer_email")
            paid_amount = data.get("paid_amount")
            items = data.get("items", [])

            if not customer_email or not items:
                return Response({"status": "fail","error": "Customer email and items are required"}, status=status.HTTP_400_BAD_REQUEST)

            if not is_valid_email(customer_email):
                return Response({"status": "fail","error": "Invalid email format"}, status=status.HTTP_400_BAD_REQUEST)

            if not isinstance(paid_amount, (int, float)) or paid_amount < 0:
                return Response({"status": "fail","error": "Paid amount must be a positive number"}, status=status.HTTP_400_BAD_REQUEST)

            total_amount = 0
            purchased_items = []

            for item in items:
                try:
                    product = Product.objects.get(product_id=item["product_id"])
                except Product.DoesNotExist:
                    return Response({"status": "fail","error": f"Product {item['product_id']} not found"}, status=status.HTTP_404_NOT_FOUND)

                if not isinstance(item["quantity"], int) or item["quantity"] <= 0:
                    return Response({"status": "fail","error": "Quantity must be a positive integer"}, status=status.HTTP_400_BAD_REQUEST)

                if product.available_stock < item["quantity"]:
                    return Response({"status": "fail","error": f"Not enough stock for {product.name}"}, status=status.HTTP_400_BAD_REQUEST)

                product_price = product.price * item["quantity"]
                tax = product_price * product.tax_percentage / 100
                total_amount += product_price + tax
                product.available_stock -= item["quantity"]
                product.save()

                purchase = PurchaseHistory(
                    customer_email=customer_email,
                    product=product,
                    quantity=item["quantity"]
                )
                purchased_items.append(purchase)

            if paid_amount < total_amount:
                return Response({"status": "fail", "error": "Paid amount is less than total bill"}, status=status.HTTP_400_BAD_REQUEST)

            bill = Bill.objects.create(
                customer_email=customer_email,
                total_amount=total_amount,
                paid_amount=paid_amount,
                balance_amount=paid_amount - total_amount
            )

            for purchase in purchased_items:
                purchase.bill = bill  
                purchase.save()

            try:
                send_invoice_email.delay(customer_email, f"Total: {total_amount}, Balance: {paid_amount - total_amount}")
            except Exception as e:
                return Response({"status": "fail","error": f"Invoice email failed: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            return Response({"status": "success", "message": "Bill created successfully", "data": 
                {"bill_id": bill.id, "total_amount": total_amount, "balance_amount": paid_amount - total_amount}},
                status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({"error": f"Error creating bill: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



    def retrieve(self, request, pk=None):
        """Retrieve a specific bill by ID."""
        try:
            bill = Bill.objects.get(id=pk)
            serializer = BillSerializer(bill)
            return Response({"status": "success", "data":serializer.data}, status=status.HTTP_200_OK)
        except Bill.DoesNotExist:
            return Response({"status": "fail","error": "Bill not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"status": "fail","error": f"Error fetching bill: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    
    
    def destroy(self, request, pk=None):
        """Delete a bill."""
        try:
            bill = Bill.objects.get(id=pk)
            bill.delete()
            return Response({"status": "success","message": "Bill deleted successfully"}, status=status.HTTP_204_NO_CONTENT)
        except Bill.DoesNotExist:
            return Response({"status": "fail","error": "Bill not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"status": "fail","error": f"Error deleting bill: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)




class ProductViewSet(viewsets.ModelViewSet):
    """
    ViewSet for handling all CRUD operations on Products with proper error handling.
    Supports:
    - GET (list all, filter by name, ID, or price range)
    - POST (create a product)
    - PUT/PATCH (update a product)
    - DELETE (remove a product)
    """
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    lookup_field = "product_id"
    def get_queryset(self):
        queryset = Product.objects.all()

        name = self.request.query_params.get("name")
        product_id = self.request.query_params.get("product_id")
        min_price = self.request.query_params.get("min_price")
        max_price = self.request.query_params.get("max_price")

        if name:
            queryset = queryset.filter(name__icontains=name)

        if min_price is not None and max_price is not None:
            try:
                min_price = float(min_price)
                max_price = float(max_price)
                queryset = queryset.filter(price__gte=min_price, price__lte=max_price)
            except ValueError:
                raise APIException("min_price and max_price must be valid numbers.")

        if product_id:
            queryset = queryset.filter(product_id=product_id)

        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        
        if not queryset.exists():
            return Response({"status": "fail", "error": "No products found."}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response({"status": "success", "data": serializer.data}, status=status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        """Create a new product with input validation and error handling."""
        try:
            serializer = self.get_serializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response({"status": "success","message": "Product added successfully"}, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"status": "fail","error": f"Error creating product: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def update(self, request, *args, **kwargs):
        """Update an existing product."""
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({"status": "success","message": "Product updated successfully"}, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Product.DoesNotExist:
            return Response({"error": "Product not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": f"Error updating product: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def destroy(self, request, *args, **kwargs):
        """Delete a product."""
        try:
            instance = self.get_object()
            instance.delete()
            return Response({"status": "success","message": "Product deleted successfully"}, status=status.HTTP_204_NO_CONTENT)
        except Product.DoesNotExist:
            return Response({"error": "Product not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": f"Error deleting product: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)






class PurchaseHistoryView(APIView):
    def get(self, request, customer_email):
        try:
            if not is_valid_email(customer_email):
                return Response({"status": "fail","error": "Invalid email format"}, status=status.HTTP_400_BAD_REQUEST)

            purchases = PurchaseHistory.objects.filter(customer_email=customer_email)
            if not purchases.exists():
                return Response({"status": "fail","error": "No purchase history found"}, status=status.HTTP_404_NOT_FOUND)

            serializer = PurchaseHistorySerializer(purchases, many=True)
            return Response({"status": "success", "data": serializer.data}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"status": "fail","error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



