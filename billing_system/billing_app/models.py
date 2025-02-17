from django.db import models

class Product(models.Model):
    name = models.CharField(max_length=255)
    product_id = models.CharField(max_length=50, unique=True)
    available_stock = models.IntegerField(default=0)
    price = models.FloatField()
    tax_percentage = models.FloatField()

    def __str__(self):
        return self.name

class Bill(models.Model):
    customer_email = models.EmailField()
    total_amount = models.FloatField()
    paid_amount = models.FloatField()
    balance_amount = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Bill {self.id} - {self.customer_email}"

class PurchaseHistory(models.Model):
    customer_email = models.EmailField()
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    bill = models.ForeignKey(Bill, on_delete=models.CASCADE)
    purchased_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Purchase {self.id} - {self.customer_email}"