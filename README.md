# Online Tutor Management System

A Django-based REST API for managing online tutoring sessions, bookings, reviews, and payments.

## Project Structure

```
quick_tutor/
├── accounts/          # User authentication and profiles
├── tutors/            # Tutor profiles and management
├── bookings/          # Session booking management
├── reviews/           # Review and rating system
├── payments/          # Payment processing
└── quick_tutor/       # Main project settings
```

## Features

- **User Management**: Register as student or tutor
- **Tutor Profiles**: Create and manage tutor profiles with subjects and ratings
- **Session Booking**: Students can book sessions with tutors
- **Review System**: Students can review and rate completed sessions
- **Payment Processing**: Track payments for sessions

## Installation

1. Create and activate virtual environment:
```bash
python -m venv .venv
.venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install django djangorestframework
```

3. Run migrations:
```bash
python manage.py migrate
```

4. Create superuser:
```bash
python manage.py createsuperuser
```

## Running the Application

Start the development server:
```bash
python manage.py runserver
```

The application will be available at `http://localhost:8000`

## API Endpoints

### Accounts
- `POST /api/accounts/register/` - Register a new user
- `POST /api/accounts/login/` - Login user
- `POST /api/accounts/logout/` - Logout user
- `GET /api/accounts/profile/` - Get user profile

### Tutors
- `GET /api/tutors/` - List all tutors
- `GET /api/tutors/<id>/` - Get tutor details
- `POST /api/tutors/create/` - Create tutor profile (tutor only)

### Bookings
- `GET /api/bookings/` - List user bookings
- `POST /api/bookings/create/` - Create new booking (student only)
- `PATCH /api/bookings/<id>/update/` - Update booking status (tutor only)

### Reviews
- `GET /api/reviews/` - List all reviews
- `GET /api/reviews/<id>/` - Get review details
- `POST /api/reviews/create/` - Create new review (student only)

### Payments
- `GET /api/payments/` - List user payments
- `GET /api/payments/<id>/` - Get payment details
- `POST /api/payments/create/` - Create new payment (student only)

## Admin Panel

Access the Django admin panel at `http://localhost:8000/admin/`

Default credentials:
- Username: `admin`
- Password: `admin123`

## Database Models

### User
- Custom user model with role (student/tutor)
- Fields: username, email, password, role, first_name, last_name

### TutorProfile
- OneToOne relationship with User
- Fields: subject, bio, rating, created_at, updated_at

### Booking
- ForeignKey to User (student and tutor)
- Fields: date, time, status (pending/confirmed/completed/rejected)

### Review
- OneToOne relationship with Booking
- Fields: rating (1-5), comment, created_at

### Payment
- OneToOne relationship with Booking
- Fields: amount, status (pending/completed/failed)

## Development

The project uses Django's default SQLite database for development. For production, configure a PostgreSQL or MySQL database in `quick_tutor/settings.py`.

## Testing

You can test the API using tools like:
- Postman
- cURL
- Thunder Client
- Django REST Framework's browsable API

## Security Notes

- Change the SECRET_KEY in production
- Set DEBUG=False in production
- Use HTTPS in production
- Implement CORS if needed (install django-cors-headers)

