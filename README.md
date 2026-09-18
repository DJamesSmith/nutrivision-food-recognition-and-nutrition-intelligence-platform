# NutriVision

**Food Recognition & Nutrition Intelligence Platform**

NutriVision is a Django-based computer vision application that identifies food from images using an **EfficientNetB0 convolutional neural network** and provides associated nutrition information through a separate nutrition lookup system.

The project combines deep learning, Django backend engineering, REST APIs, authentication, asynchronous model training, image processing, PostgreSQL, Redis, Celery, and an interactive Bootstrap/jQuery frontend.

---

## Overview

The application allows an authenticated user to:

1. Register an account.
2. Authenticate using email or phone number.
3. Upload a food image.
4. Send the image through the EfficientNetB0 classifier.
5. Receive the predicted food class and confidence.
6. Retrieve nutrition information associated with the predicted food.
7. Save the meal and prediction to personal history.
8. Review previous meals and predictions through the dashboard.

The system also provides authorized functionality for model training and model management.

---

## Core Architecture

```text
                    ┌──────────────────────┐
                    │       Frontend       │
                    │ Bootstrap + jQuery   │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │        Django        │
                    │  Template + REST API │
                    └───────┬───────┬──────┘
                            │       │
              ┌─────────────┘       └─────────────┐
              ▼                                   ▼
       ┌──────────────┐                    ┌──────────────┐
       │ Authentication│                    │ PostgreSQL   │
       │ Session + JWT │                    │ Application  │
       └──────────────┘                    │ Data         │
                                           └──────────────┘
                                                   ▲
                                                   │
                                     ┌─────────────┘
                                     │
                              ┌──────┴──────┐
                              │    Celery   │
                              │    Worker   │
                              └──────┬──────┘
                                     │
                                  Redis
                                     │
                                     ▼
                              EfficientNetB0
                                     │
                                     ▼
                              Model Artifact
```

---

## Machine Learning Pipeline

NutriVision uses **EfficientNetB0 with transfer learning** for food classification.

```text
Food-101 Dataset
       │
       ▼
Dataset Validation
       │
       ▼
Image Preprocessing
       │
       ▼
Data Augmentation
       │
       ▼
EfficientNetB0
(ImageNet Weights)
       │
       ▼
Global Average Pooling
       │
       ▼
Dropout
       │
       ▼
Dense Classification Layer
       │
       ▼
Softmax
       │
       ▼
101 Food Classes
```

The initial training strategy is:

```text
Phase 1
EfficientNetB0 Backbone → Frozen
Classification Head      → Trainable

Phase 2
Selected EfficientNetB0 Layers → Unfrozen
Classification Head             → Trainable
```

This allows the project to demonstrate both standard transfer learning and optional fine-tuning.

---

## Dataset

### Food-101

The initial model is trained using the **Food-101 dataset**.

Dataset characteristics:

| Property              |   Value |
| --------------------- | ------: |
| Food categories       |     101 |
| Total images          | 101,000 |
| Training images       |  75,750 |
| Test images           |  25,250 |
| Images per class      |   1,000 |
| Training images/class |     750 |
| Test images/class     |     250 |

The official dataset is provided by ETH Zürich.

**Dataset:**
https://data.vision.ee.ethz.ch/cvl/vision2/datasets_extra/food-101/

The dataset contains real-world food images and includes visually similar food categories, making it appropriate for demonstrating image-classification challenges.

---

## Example Food Classes

Food-101 contains classes such as:

```text
apple_pie
baby_back_ribs
baklava
beef_carpaccio
beef_tartare
bibimbap
caesar_salad
cannoli
cheesecake
chicken_curry
chicken_wings
chocolate_cake
club_sandwich
donuts
dumplings
eggs_benedict
french_fries
fried_rice
hamburger
hot_dog
ice_cream
lasagna
macaroni_and_cheese
pizza
ramen
samosa
sashimi
sushi
tacos
waffles
```

The complete set of 101 categories comes from the Food-101 dataset.

---

## Nutrition Lookup

Food recognition and nutrition estimation are treated as two separate components.

```text
Image
  │
  ▼
EfficientNetB0
  │
  ▼
Food Class
  │
  ▼
Nutrition Lookup
  │
  ├── Calories
  ├── Protein
  ├── Carbohydrates
  ├── Fat
  ├── Fiber
  └── Other Nutrients
```

The model identifies the food.

The nutrition subsystem retrieves nutrition information associated with that food.

This separation is intentional because a food-classification CNN does not inherently determine the actual nutritional content of an arbitrary photographed portion.

A nutrition dataset such as **USDA FoodData Central** can be used to populate or supplement the nutrition database.

---

## Main Features

### Authentication

* Custom Django User model
* Custom User Manager
* Email authentication
* Phone authentication
* Login using email OR phone
* Custom Django authentication backend
* Django session authentication
* JWT authentication
* JWT access tokens
* JWT refresh tokens
* JWT expiration
* HS256 JWT signing
* HTTP-only JWT cookies
* JWT authentication decorator
* Permission-based authorization

### User Management

* Registration
* Login
* Logout
* User dashboard
* Protected pages
* User-specific meal history
* User-specific prediction history

### Image Classification

* Food image upload
* Image validation
* EfficientNetB0
* ImageNet transfer learning
* Fine-tuning support
* Confidence score
* Food class prediction
* Model version tracking

### Nutrition

* Food-to-nutrition lookup
* Calories
* Protein
* Carbohydrates
* Fat
* Fiber
* Nutrition history
* Daily aggregation
* Weekly aggregation

### Machine Learning

* Dataset management
* Training jobs
* EfficientNetB0 training
* Validation
* Evaluation metrics
* Model versioning
* Asynchronous training
* Training status tracking

### Backend

* Django ORM
* PostgreSQL
* Django migrations
* Django REST Framework
* DRF serializers
* Function-based views
* Separate template and API views
* Multipart API support
* Professional JSON responses
* HTTP status codes

### Asynchronous Processing

* Redis
* Celery
* Background model training
* Training status
* Training task IDs
* Model update operations
* Batch nutrition-data refresh jobs

### Frontend

* Bootstrap
* Template inheritance
* jQuery
* AJAX
* FormData
* Client-side validation
* Image upload interface
* Dashboard
* Prediction interface

### File Management

* Django media configuration
* Image upload
* Automatic old-image cleanup
* Automatic image deletion
* Django signals

### Security

* Password hashing
* CSRF protection
* JWT expiration
* HTTP-only cookies
* CORS configuration
* Server-side permissions
* File validation
* Upload size restrictions
* No-cache authentication pages
* Environment-based secrets
* Sensitive-data protection in logs

### Auditing

Audit events can include:

```text
USER_REGISTERED
USER_LOGIN
USER_LOGOUT
LOGIN_FAILED
IMAGE_UPLOADED
PREDICTION_CREATED
TRAINING_STARTED
TRAINING_COMPLETED
TRAINING_FAILED
MODEL_UPDATED
```

---

## Technology Stack

```text
Python
Django
Django REST Framework
PostgreSQL
TensorFlow / Keras
EfficientNetB0
Redis
Celery
JWT
Bootstrap 5
jQuery
AJAX
FormData
Pillow
python-dotenv
CORS
```

---

## Project Architecture

```text
nutrivision/
│
├── config/
│   ├── settings.py
│   ├── urls.py
│   ├── celery.py
│   ├── logging.py
│   ├── asgi.py
│   └── wsgi.py
│
├── accounts/
│   ├── migrations/
│   ├── templates/
│   │   └── accounts/
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── managers.py
│   ├── forms.py
│   ├── serializers.py
│   ├── views.py
│   ├── api_views.py
│   ├── urls.py
│   ├── backends.py
│   ├── decorators.py
│   └── signals.py
│
├── classification/
│   ├── migrations/
│   ├── templates/
│   │   └── classification/
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── forms.py
│   ├── serializers.py
│   ├── views.py
│   ├── api_views.py
│   ├── urls.py
│   ├── tasks.py
│   ├── decorators.py
│   └── signals.py
│
├── nutrition/
│   ├── migrations/
│   ├── models.py
│   ├── serializers.py
│   ├── views.py
│   ├── api_views.py
│   ├── urls.py
│   └── ...
│
├── audit/
│   ├── migrations/
│   ├── models.py
│   ├── apps.py
│   └── signals.py
│
├── ml/
│   ├── efficientnet.py
│   ├── preprocessing.py
│   ├── training.py
│   ├── prediction.py
│   ├── evaluation.py
│   └── model_manager.py
│
├── templates/
│   ├── base.html
│   ├── home.html
│   └── ...
│
├── static/
│   └── js/
│       └── script.js
│
├── media/
│   ├── uploaded_images/
│   ├── predictions/
│   └── datasets/
│
├── ml_models/
│
├── .env
├── .gitignore
├── manage.py
├── requirements.txt
└── README.md
```

The exact architecture may evolve during implementation while preserving the project's architectural requirements.

---

## Authentication Architecture

The application deliberately uses two authentication mechanisms for different purposes.

### Template/Web Authentication

```text
Browser
   │
   ▼
Django Login
   │
   ▼
Django Session
   │
   ▼
Protected Template Views
```

### REST API Authentication

```text
Browser / API Client
        │
        ▼
HTTP-only JWT Cookie
        │
        ▼
JWT Authentication Decorator
        │
        ▼
Authenticated API View
```

JWT is not exposed directly to frontend JavaScript.

---

## Training Architecture

Model training is an asynchronous operation.

```text
Authorized User
      │
      ▼
Training API
      │
      ▼
Celery Task
      │
      ▼
Redis
      │
      ▼
Celery Worker
      │
      ▼
EfficientNetB0 Training
      │
      ▼
Evaluation
      │
      ▼
Model Artifact
      │
      ▼
Model Version
      │
      ▼
PostgreSQL
```

Training should never block a normal HTTP request.

---

## Prediction Architecture

```text
Authenticated User
       │
       ▼
Upload Food Image
       │
       ▼
Image Validation
       │
       ▼
Preprocessing
       │
       ▼
Active EfficientNetB0
       │
       ▼
Prediction
       │
       ├───────────────┐
       ▼               ▼
Food Class       Confidence
       │
       ▼
Nutrition Lookup
       │
       ▼
Nutrition Information
       │
       ▼
Meal History
       │
       ▼
Audit Log
```

---

## Future Extensions

Potential future capabilities include:

* Portion-size estimation
* Calorie estimation based on portion size
* Daily calorie tracking
* Weekly nutrition analytics
* Macro tracking
* Dietary goals
* Meal recommendations
* Ingredient recognition
* Barcode integration
* OCR for food labels
* Multiple food detection
* Regional cuisine datasets
* Personalized nutrition dashboards
* Mobile application
* EfficientNet model comparison
* Model performance monitoring
* Continuous model retraining

---

## Important Limitation

The initial system performs **food-category recognition**, not precise calorie estimation from a photograph.

For example:

```text
Image
  ↓
"Pizza"
  ↓
Nutrition lookup
```

does not mean the system knows the exact number of calories contained in that particular plate.

Accurate calorie estimation requires additional information such as:

* portion size
* ingredients
* preparation method
* recipe composition
* food density

Therefore, the initial implementation should describe nutrition values as **lookup-based estimates**, not exact measurements.

---

## Development Goal

The primary purpose of NutriVision is to demonstrate the integration of:

```text
Deep Learning
      +
Computer Vision
      +
Django
      +
PostgreSQL
      +
REST APIs
      +
JWT Authentication
      +
Session Authentication
      +
Redis
      +
Celery
      +
Asynchronous ML Training
      +
Image Processing
      +
Nutrition Data
```

The project is intended to demonstrate both **machine-learning engineering and backend software engineering** rather than functioning only as a standalone image-classification notebook.
