# Billing System API

## Project Overview
This is a Django REST Framework (DRF) project for a **Billing System**, which includes:
- **Product Management** (CRUD APIs)
- **Billing Calculation** with tax
- **Purchase History** tracking
- **Async Invoice Emailing** using Celery & Redis

---

## Installation & Setup

### **1️ Clone the Repository**
```bash
git clone <your-repository-url>
cd <project-directory>
```

### **2️ Create a Virtual Environment & Install Dependencies**
```bash
python -m venv env
source env\Scripts\activate
pip install -r requirements.txt
```

### **3️ Configure Database (PostgreSQL)**
Update `billing_system/settings.py` with your database credentials:
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'billing_db',
        'USER': 'your_db_user',
        'PASSWORD': 'your_db_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

### **4️ Apply Database Migrations**
```bash
python manage.py makemigrations
python manage.py migrate
```

### **5️ Start Redis (Required for Celery)**
#### **If using Docker**  (its recommended to use)
```bash
docker run -d -p 6379:6379 redis
```
#### **If Redis is installed locally**
```bash
redis-server
```

### **6️ Start Celery Worker**
```bash
celery -A billing_system worker --loglevel=info --pool=solo
```

### **7️ Start Django Server**
```bash
python manage.py runserver
```

---

## 📌 API Endpoints

### **🔹 Product APIs**
| Method  | Endpoint | Description |
|---------|---------|-------------|
| **GET** | `/api/products/` | Retrieve all products |
| **POST** | `/api/products/` | Create a new product |
| **GET** | `/api/products/{product_id}/` | Retrieve a specific product |
| **PUT** | `/api/products/{product_id}/` | Update a product |
| **DELETE** | `/api/products/{product_id}/` | Delete a product |

### **🔹 Billing APIs**
| Method  | Endpoint | Description |
|---------|---------|-------------|
| **GET** | `/api/billing/` | Retrieve all bills |
| **POST** | `/api/billing/` | Create a new bill |
| **GET** | `/api/billing/{id}/` | Retrieve a specific bill |
| **DELETE** | `/api/billing/{id}/` | Delete a bill |

### **🔹 Purchase History API**
| Method  | Endpoint | Description |
|---------|---------|-------------|
| **GET** | `/api/purchases/{customer_email}/` | Retrieve purchase history by customer |

---

## 📌 Testing the API
(Postman API collections have been sent seperately)
### **1️ Using Postman or cURL**
#### **Example: Create a Bill (POST)**
```bash
curl -X POST http://127.0.0.1:8000/api/billing/ \
-H "Content-Type: application/json" \
-d '{
    "customer_email": "customer@example.com",
    "paid_amount": 500,
    "items": [
        {"product_id": "P001", "quantity": 2},
        {"product_id": "P002", "quantity": 1}
    ]
}'
```

#### **Example: Get All Products (GET)**
```bash
curl -X GET http://127.0.0.1:8000/api/products/
```

---

If there are any setup issues, please contact me (Karthik, Ph: 7358913054).

---
