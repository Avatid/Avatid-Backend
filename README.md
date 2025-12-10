# alter-knights-backend


- Django 4.2
- Python 3.11

## Content:

1. Quick start setup
2. Manual setup
3. Features

## Quick start setup:

1. Setup env variables for local development:

   cp env.local.example .env

2. Setup docker-compose override file for local development:

   cp example.docker-compose.override.yml docker-compose.override.yml

3. Run dockerized server:

   docker-compose up

4. After docker image is built and server started, setup migrations/static files/admin access:

   docker-compose exec app sh /scripts/server_setup.sh

## Manual setup

1. Set .env variables (see comments in env.dev.example and env.local.example for details):
   1. Create .env file from development (env.dev.example) template
   2. Set PROJECT_NAME, FRONTEND_URL
   3. Set remote DB credentials
   4. Create and copy GC credentials file to GOOGLE_APPLICATION_CREDENTIALS path
   5. Create buckets for static and media files and set fields GS_STATIC_BUCKET_NAME, GS_MEDIA_BUCKET_NAME
   6. Set admin credentials for script or setup them manually later
2. Set docker-compose.override.yml file:
   1. By default, all non-core services (db, celery server) are placed remotely, in this case no
      docker-compose.override.yml is needed
   2. To place some services locally add docker-compose.override.yml
3. Run dockerized server: docker-compose up
4. After docker image is built and server started, setup migrations/static files/admin access:

   1. Run

      docker-compose exec app sh /scripts/server_setup.sh for automatic setup

      OR

   2. Apply DB migrations:

      docker-compose exec app python manage.py migrate

   3. Setup static files:

      docker-compose exec app python manage.py collectstatic

   4. Create superuser for admin access:

      docker-compose exec app python manage.py createsuperuser

## Features

1. Server is served at http://0.0.0.0:80
2. Swagger docs are served at http://0.0.0.0/api/schema/swagger/
3. Admin panel is served at http://0.0.0.0/admin/
4. Includes Celery for scheduled and background tasks. See app/core/tasks.py and app/settings.py for examples
5. New push notification implementation check **FirePush** -> fire_push_sender.py [**dependency** /app/service-account-file.json]


## Cloud Deploy
Simply run `scripts/deploy_prod.sh` (!!!NOTE: This is **PRODUCTION** deployment)

The script executes the command: `gcloud builds submit --config cloudmigrate.yaml`.

In particular, 
- Build and push image to Google Container Registry
- Perform `manage.py migrate` on Postgresql database instance via SQL Auth Proxy.
- Perform `manage.py collectstatic`, which synchronizes media and static file to google cloud bucket.
- Deploy the app to Cloud Run, and attach "cloud-run" service account

### Production configuration
Production configuration is stored in Google Secret Manager and synced with local `.env` file in "terraform" directory. 

Sync command: `terraform apply`. 


# PROJECT DOCUMENTATION
## Overview

AvatID is a comprehensive Django REST API backend for a business booking and service management platform. The system enables customers to discover, book, and rate local businesses while providing business owners with tools to manage their services, employees, and bookings.

## Core Features

- User Management - Customer and business owner registration/authentication
- Business Discovery - Location-based search with filtering capabilities
- Service Booking - Real-time booking system with availability management
- Rating System - Customer feedback and business reputation management
- Notifications - Multi-channel notification system (push, email, SMS)
- Multi-language Support - English and Albanian localization
- Payment Integration - Apple and Google Pay support
- Real-time Chat - Firebase-based messaging system

## Architecture

the backend follows a modular Django architecture with clear separation of concerns:

app/

├── business/ > Business & booking management

├── user/ > User authentication & profiles

├── notifications/ > Push & email notifications

├── rating/ > Review & rating system

├── onboarding/ > Business & freelancer setup

├── sms/  > SMS verification & authentication

├── shared/ > Shared utilities & endpoints

├── core/ > Core utilities & base classes

├── mail/ > Email handling & templates

└── templates/ > Django admin templates

## Design Patterns

- Model-View-Serializer (MVS) - Django REST Framework pattern
- Repository Pattern - Custom managers and querysets
- Factory Pattern - Business logic factories
- Observer Pattern - Django signals for event handling
- Strategy Pattern - Multiple authentication backends

## Technology Stack

### Core Framework

- Django 4.2.3 - Web framework
- Django REST Framework 3.14.0 - API development
- PostgreSQL + PostGIS - Database with geospatial support
- Redis - Caching and Celery message broker
- Celery 5.3.1 - Background task processing

### Key Libraries

- Authentication - SimpleJWT, Django Guardian
- API Documentation - drf-spectacular (Swagger/OpenAPI)
- File Storage - Google Cloud Storage, Whitenoise
- Notifications - Firebase Admin SDK, Twilio
- Email - Django Anymail (SendGrid)
- Internationalization - django-modeltranslation
- Image Processing - Pillow, django-stdimage
- Monitoring - Sentry SDK
- Testing - Django Test Framework, Coverage

### External Services

- Google Cloud Platform - Storage, Secret Manager, Vision API
- Firebase - Push notifications, real-time chat
- Twilio - SMS verification
- SendGrid - Email delivery

## Quick Setup (Docker)

- **Clone repository**
    
    git clone …
    
- **Setup environment**
    
    cp env.local.example .env
    
    cp example.docker-compose.override.yml docker-compose.override.yml (local only)
    
- **Start services**
    
    docker-compose build
    
    docker-compose up
    

## Key environment variables:

### Database

DB_HOST=localhost

DB_NAME=postgres

DB_USER=postgres

DB_PASS=password

### Redis

REDIS_SERVER=redis

REDIS_PASSWORD=your_redis_password

REDIS_APP_DB=0

### Google Cloud

GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account.json

GS_STATIC_BUCKET_NAME=your-static-bucket

GS_MEDIA_BUCKET_NAME=your-media-bucket

### External Services

SENDGRID_KEY=your_sendgrid_key

TWILIO_ACCOUNT_SID=your_twilio_sid

TWILIO_AUTH_TOKEN=your_twilio_token

FIRE_BASE_CRED_BASE64=base64_encoded_firebase_credentials

## Database Schema

### Core Models

- **User Management**
    
    user/models.py
    
    `class User(AbstractBaseUser, PermissionsMixin):`
    
    `uid = UUIDField(unique=True)`
    
    `email = EmailField(unique=True)`
    
    `phone = CharField(unique=True)`
    
    `is_phone_verified = BooleanField(default=False)`
    
    `name = CharField(max_length=64)`
    
    `surname = CharField(max_length=64)`
    
    `avatar = ImageField()`
    
    `location = PointField(null=True)  # PostGIS`
    
    `send_push_notifications = BooleanField(default=True)`
    
    `send_email_notification = BooleanField(default=True)`
    
- **Business Management**
    
    business/models.py
    
    `class Business(Model):`
    
    `uid = UUIDField(unique=True)`
    
    `name = CharField(max_length=255)`
    
    `description = TextField()`
    
    `location = PointField()  # PostGIS for geospatial queries`
    
    `address = CharField(max_length=500)`
    
    `phone = CharField(max_length=255)`
    
    `email = EmailField()`
    
    `website = URLField()`
    
    `owner = ForeignKey(User)`
    
    `categories = ManyToManyField(ServiceCategory)`
    
    `gallery = ManyToManyField(Gallery)`
    
    `working_hours = ManyToManyField(WorkingHours)`
    
    `class UserBusinessBooking(Model):`
    
    `uid = UUIDField(unique=True)`
    
    `user = ForeignKey(User)`
    
    `business = ForeignKey(Business)`
    
    `employee = ForeignKey(Employee, null=True)`
    
    `service = ForeignKey(Service)`
    
    `date = DateField()`
    
    `start_time = TimeField()`
    
    `end_time = TimeField()`
    
    `status = CharField(choices=BookingStatusChoices)`
    
    `total_price = DecimalField(max_digits=10, decimal_places=2)`
    
- **Service & Category System**
    
    `class ServiceCategory(Model):`
    
    `uid = UUIDField(unique=True)`
    
    `name = CharField(max_length=255)`
    
    `logo = ImageField()`
    
    `parent = ForeignKey('self', null=True)  # Hierarchical categories`
    
    `price = DecimalField(max_digits=10, decimal_places=2)`
    
    `currency = CharField(choices=CurrencyChoices)`
    
    `duration = DurationField()`
    
    `class Service(Model):`
    
    `uid = UUIDField(unique=True)`
    
    `name = CharField(max_length=255)`
    
    `business = ForeignKey(Business)`
    
    `category = ForeignKey(ServiceCategory)`
    
    `price = DecimalField(max_digits=10, decimal_places=2)`
    
    `duration = DurationField()`
    
    `gender = CharField(choices=ServiceGenderChoices)`
    
- **Rating & Review System**
    
    rating/models.py
    
    `class Rating(Model):`
    
    `uid = UUIDField(unique=True)`
    
    `user = ForeignKey(User)`
    
    `business = ForeignKey(Business, null=True)`
    
    `employee = ForeignKey(Employee, null=True)`
    
    `booking = ForeignKey(UserBusinessBooking, null=True)`
    
    `rating = IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])`
    
    `comment = TextField()`
    
    `reply_to = ForeignKey('self', null=True)  # For replies`
    
    `images = ManyToManyField(RatingImage)`
    
- **Notification System**
    
    notifications/models.py
    
    `class NotificationObject(Model):`
    
    `uid = UUIDField(unique=True)`
    
    `user = ForeignKey(User)`
    
    `title = CharField(max_length=255)`
    
    `body = TextField()`
    
    `data = JSONField()`
    
    `notification_type = CharField(choices=NotificationType.choices)`
    
    `is_sent = BooleanField(default=False)`
    
    `sent_at = DateTimeField(null=True)`
    
    `read_at = DateTimeField(null=True)`
    

### **Key Relationships**

- User ↔ Business - One-to-Many (owner relationship)
- Business ↔ Services - One-to-Many
- User ↔ Bookings - One-to-Many
- Business ↔ Bookings - One-to-Many
- Booking ↔ Rating - One-to-One or One-to-Many
- Business ↔ Categories - Many-to-Many

## API Endpoints

### **Authentication Endpoints**

POST /api/user/registration/email/     → Email registration

POST /api/user/registration/phone/     → Phone registration

POST /api/user/auth/email/            → Email login

POST /api/user/auth/phone/            → Phone login

POST /api/user/auth/google/           → Google OAuth

POST /api/user/auth/apple/            → Apple OAuth

POST /api/user/auth/facebook/         → Facebook OAuth

POST /api/user/auth/refresh/          → Token refresh

POST /api/user/auth/logout/all/       → Logout all devices

### **User Management**

GET    /api/user/detail/              → Get user profile

PATCH  /api/user/update/              → Update user profile

PATCH  /api/user/avatar/              → Update avatar

PATCH  /api/user/location/            → Update location

DELETE /api/user/delete/              → Delete account

PATCH  /api/user/notification-settings/ → Update notification preferences

### **Business Discovery & Management**

GET    /api/business/search/          → Search businesses

GET    /api/business/categories/      → Get service categories

GET    /api/business/detail/<uid>/    → Get business details

GET    /api/business/nearby/          → Get nearby businesses

GET    /api/business/hours/<uid>/     → Get business working hours

GET    /api/business/services/<uid>/  → Get business services

GET    /api/business/employees/<uid>/ → Get business employees

### **Booking System**

POST   /api/business/book/            → Create booking

GET    /api/business/my-bookings/     → Get user's bookings

PATCH  /api/business/booking/<uid>/   → Update booking

DELETE /api/business/booking/<uid>/   → Cancel booking

GET    /api/business/booking/detail/<uid>/ → Get booking details

GET    /api/business/available-slots/ → Get available time slots

### **Rating & Reviews**

POST   /api/rating/add/              → Add rating/review

GET    /api/rating/list/<business_uid>/ → Get business ratings

GET    /api/rating/list/booking/<booking_uid>/ → Get booking ratings

GET    /api/rating/my-rating/        → Get user's ratings

PATCH  /api/rating/edit/<uid>/       → Edit rating

DELETE /api/rating/delete/<uid>/     → Delete rating

### **Onboarding (Business Setup)**

POST   /api/onboarding/business/create/    → Create business profile

PATCH  /api/onboarding/business/update/    → Update business

GET    /api/onboarding/business/my/        → Get my businesses

POST   /api/onboarding/working-hours/      → Add working hours

POST   /api/onboarding/employee/           → Add employee

POST   /api/onboarding/service/            → Add service

### **SMS Verification**

POST   /api/sms/verify/request/       → Send SMS verification code

POST   /api/sms/verify/submit/        → Verify SMS code

POST   /api/sms/phone/update/         → Update phone number

POST   /api/sms/password/reset/       → Reset password via SMS

### **Notifications**

GET    /api/notifications/list/       → Get user notifications

PATCH  /api/notifications/<uid>/read/ → Mark notification as read

POST   /api/notifications/device/     → Register device for push notifications

### **Shared Utilities**

GET    /api/shared/countries/         → Get countries list

GET    /api/shared/timezones/         → Get timezones list

POST   /api/shared/upload/            → Upload file

## Authentication & Authorization

### JWT Token System

The API uses JWT (JSON Web Token) authentication with the following features:

- Access Token - 30-day lifetime for API access
- Refresh Token - 365-day lifetime for token renewal
- Token Blacklisting - Secure logout functionality
- Multi-device Support - Each device gets unique tokens

### Authentication Methods

1. Email/Password - Traditional email-based authentication

2. Phone/SMS - Phone verification with SMS codes

3. Social OAuth - Google, Apple, Facebook, Instagram integration

4. Master Password - Admin backdoor access (for support)

### Permission System

Custom permissions

`class IsOwnerOrReadOnly(BasePermission):`

`def has_object_permission(self, request, view, obj):`

`if request.method in SAFE_METHODS:`

`return True`

`return obj.owner == request.user`

`class IsBusinessOwner(BasePermission):`

`def has_permission(self, request, view):`

`return hasattr(request.user, 'business')`

## Security Features

- CORS Configuration - Restricted to trusted origins
- CSRF Protection - For web clients
- Rate Limiting - Via Redis (configurable)
- Input Validation - Comprehensive serializer validation
- SQL Injection Protection - Django ORM safeguards
- File Upload Security - Size limits and type validation

## Background Tasks & Celery

### **Scheduled Tasks**

`CELERY_BEAT_SCHEDULE = {`

`'send_reminder_notification': {`

`'task': 'send_reminder_notification',`

`'schedule': timedelta(minutes=CRON_TIME_1HR),  # 10 min default`

`},`

`'send_reminder_notification_daily': {`

`'task': 'send_reminder_notification_daily',`

`'schedule': timedelta(minutes=CRON_TIME_24HR),  # 60 min default`

`},`

`}`

### Notification Tasks

`@shared_task(name="send_booked_notification")
"""Send booking confirmation notification"""`

`@shared_task(name="send_canceled_notification")
"""Send booking cancellation notification"""`

`@shared_task(name="send_reminder_notification")
"""Send booking reminders (hourly)"""`

`@shared_task(name="send_reminder_notification_daily")
"""Send daily booking reminders"""`

### Email Tasks

`@shared_task(name="send_verify_email")
"""Send email verification"""`

`@shared_task(name="send_password_reset_request_email")
"""Send password reset email"""`

### Business Logic Tasks

`shared_task(name="send_apply_notification")
"""Send job application notification"""`

`@shared_task(name="update_business_ratings")
"""Recalculate business rating averages"""`

### Task Queue Configuration

`CELERY_TASK_ROUTES = {
    'celery_test_task': {'queue': 'main-queue'},
    'send_verify_email': {'queue': 'main-queue'},
    'send_fire_push': {'queue': 'main-queue'},
    'send_booked_notification': {'queue': 'main-queue'},
    # ... all tasks route to main-queue
}`

## Push Notifications (Firebase)

### **Firebase integration**

`class FireBaseClient:`

`def send_push_notification(self, tokens: list, title: str, body: str, data: dict):`

`"""Send push notification to device tokens"""`

`def send_topic_notification(self, topic: str, title: str, body: str):`

`"""Send notification to topic subscribers"""`

### Configuration:

- Firebase credentials stored as base64 in environment
- Device token registration via /api/notifications/device/
- Topic-based notifications for broadcasts
- Custom data payload support

## Email Notifications (Elasticmail actually used)

### Email backend configuration

EMAIL_BACKEND = "anymail.backends.sendgrid.EmailBackend"

ANYMAIL = {

'SENDGRID_API_KEY': os.environ.get('SENDGRID_KEY'),

}

### Email Templates:

- Booking confirmations
- Booking cancellations
- Password reset requests
- Email verification
- Booking reminders

## SMS Notifications (Twilio)

`class SmsClient:`

`def send_sms_verification(self, phone_number: str) -> bool:`

`"""Send SMS verification code"""`

`def check_sms_code(self, phone_number: str, code: str) -> bool:`

`"""Verify SMS code"""`

## API Documentation & Testing

### Swagger/OpenAPI Documentation

- URL: http://localhost:8000/api/schema/swagger/
- Features:Interactive API testing
    - Request/response examples
    - Authentication testing
    - Schema validation

### Admin Panel

URL: http://localhost:8000/admin/

Features:

- User management
- Business administration
- Booking management
- Content moderation
- System monitoring

### Health Checks

- Application health
    
    GET /health/
    
- Database connectivity
    
    GET /health/db/
    
- Redis connectivity
    
    GET /health/redis/
    

## Internationalization

## Supported Languages

- English (en) - Default language
- Albanian (sq) - Full localization

### Translation System

### Django modeltranslation

- MODELTRANSLATION_LANGUAGES = ('en', 'sq')

### Model translation example

`class Business(Model):`

`name = CharField(max_length=255)`

`description = TextField()`

`# Automatically creates: name_en, name_sq, description_en, description_sq`

### Translation Management

- Generate translation files
    
    python manage.py makemessages -l sq
    
- Compile translations
    
    python manage.py compilemessages
    
- Update model translations
    
    python manage.py sync_translation_fields
    

### API Response Localization

- Accept-Language Header - Automatic language detection
- Database Content - Model-level translations
- API Messages - Translated error messages and responses
- Admin Interface - Fully translated admin panel