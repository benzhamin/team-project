# MedLink - Advanced Medical Appointment & Communication Platform

## 🏥 Project Overview

MedLink is a comprehensive **telemedicine platform** built with Django that modernizes the doctor-patient relationship through digital appointment booking, secure communication, and medical record management.

## ✨ Key Features

### 🔐 **Advanced User Management**
- **Multi-role authentication**: Admin, Patient, Doctor, Receptionist
- **JWT-based security** with refresh tokens
- **Profile management** with comprehensive user information
- **User verification** and session tracking

### 📅 **Smart Appointment System**
- **Intelligent scheduling** with conflict detection
- **Time slot management** (Morning, Afternoon, Evening)
- **Urgency levels** (Low, Medium, High, Emergency)
- **Appointment reminders** and notifications
- **Rescheduling** and cancellation capabilities

### 💬 **Real-time Communication**
- **WebSocket-based chat** with typing indicators
- **File sharing** (images, documents)
- **Read receipts** and message status
- **Chat invitations** and participant management
- **Appointment-related messaging**

### 📁 **Medical File Management**
- **Secure file uploads** with validation
- **Multiple file types** support (PDF, DOC, images)
- **File size limits** and security
- **Privacy controls** and access management

### 👨‍⚕️ **Doctor Discovery & Profiles**
- **Advanced search** by specialization, rating, experience
- **Working hours** and availability tracking
- **Consultation fees** and qualifications
- **Review system** with ratings

## 🚀 Recent Improvements

### **Security & Permissions**
- ✅ **Role-based access control** with custom permissions
- ✅ **Input validation** and sanitization
- ✅ **File upload security** with extension validation
- ✅ **Authentication middleware** improvements

### **Data Models & Validation**
- ✅ **Enhanced user profiles** with medical information
- ✅ **Appointment conflict detection** and validation
- ✅ **File management** with metadata tracking
- ✅ **Review system** with duplicate prevention

### **API & Performance**
- ✅ **RESTful API** with proper HTTP status codes
- ✅ **Pagination** and filtering for large datasets
- ✅ **Search functionality** across multiple fields
- ✅ **Optimized database queries** with select_related

### **Real-time Features**
- ✅ **WebSocket improvements** with proper error handling
- ✅ **Typing indicators** and online status
- ✅ **Message notifications** and read receipts
- ✅ **Chat participant management**

## 🛠️ Technical Stack

### **Backend**
- **Django 5.2.3** - Web framework
- **Django REST Framework** - API development
- **Django Channels** - WebSocket support
- **Redis** - Channel layer and caching

### **Database**
- **SQLite** (development)
- **PostgreSQL** (production ready)
- **Django ORM** with optimized queries

### **Authentication**
- **JWT tokens** with refresh capability
- **Custom user model** with role-based permissions
- **Session management** and tracking

### **File Handling**
- **Pillow** - Image processing
- **File validation** and security
- **Media storage** with proper organization

## 📋 API Endpoints

### **Authentication**
```
POST /api/auth/register/          # User registration
POST /api/auth/login/             # User login
POST /api/auth/logout/            # User logout
POST /api/auth/password-change/   # Password change
POST /api/auth/password-reset/    # Password reset
```

### **Appointments**
```
GET    /api/appointment-requests/           # List requests
POST   /api/appointment-requests/           # Create request
GET    /api/appointment-requests/{id}/      # Get request details
POST   /api/appointment-requests/{id}/accept/    # Accept request
POST   /api/appointment-requests/{id}/reject/    # Reject request
POST   /api/appointment-requests/{id}/cancel/    # Cancel request
```

### **Medical Files**
```
GET    /api/medical-files/        # List files
POST   /api/medical-files/        # Upload file
GET    /api/medical-files/{id}/   # Get file details
PUT    /api/medical-files/{id}/   # Update file
DELETE /api/medical-files/{id}/   # Delete file
```

### **Doctors**
```
GET /api/doctors/                 # List doctors with filters
GET /api/doctors/{id}/            # Get doctor details
GET /api/doctors/?specialization=cardiology&min_rating=4.0
```

### **Chat**
```
WS /ws/chat/{chat_id}/           # WebSocket chat connection
WS /ws/notifications/            # User notifications
```

## 🔧 Installation & Setup

### **Prerequisites**
- Python 3.8+
- Redis server
- Virtual environment

### **Setup Steps**
```bash
# Clone repository
git clone <repository-url>
cd team-project

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup environment variables
cp .env.example .env
# Edit .env with your configuration

# Run migrations
python manage.py makemigrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Start Redis server
redis-server

# Run development server
python manage.py runserver
```

### **Environment Variables**
```env
DEBUG=True
SECRET_KEY=your-secret-key
DATABASE_URL=sqlite:///db.sqlite3
REDIS_URL=redis://localhost:6379
ALLOWED_HOSTS=localhost,127.0.0.1
```

## 📊 Database Schema

### **User Management**
- `User` - Extended user model with roles
- `PatientProfile` - Patient-specific information
- `DoctorProfile` - Doctor-specific information
- `Specialization` - Medical specialties
- `Review` - Doctor ratings and reviews

### **Appointments**
- `AppointmentRequest` - Initial appointment requests
- `Appointment` - Confirmed appointments
- `AppointmentReminder` - Notification system

### **Communication**
- `Chat` - Chat rooms and conversations
- `Message` - Individual messages with attachments
- `ChatParticipant` - Participant status tracking
- `ChatNotification` - User notifications

### **Medical Records**
- `MedicalFile` - Patient medical documents
- File validation and security
- Access control and privacy

## 🔒 Security Features

### **Authentication & Authorization**
- JWT token-based authentication
- Role-based access control
- Custom permission classes
- Session management

### **Data Protection**
- Input validation and sanitization
- File upload security
- SQL injection prevention
- XSS protection

### **Privacy Controls**
- Patient data isolation
- Doctor-patient confidentiality
- File access restrictions
- Audit logging

## 🚀 Deployment

### **Production Checklist**
- [ ] Set `DEBUG=False`
- [ ] Configure production database
- [ ] Setup Redis for production
- [ ] Configure static/media file serving
- [ ] Setup SSL certificates
- [ ] Configure logging
- [ ] Setup monitoring

### **Docker Support**
```dockerfile
# Dockerfile example
FROM python:3.9
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
```

## 🧪 Testing

### **Run Tests**
```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test accounts
python manage.py test medlink
python manage.py test chat

# Run with coverage
coverage run --source='.' manage.py test
coverage report
```

## 📈 Performance Optimization

### **Database Optimization**
- Select related queries
- Database indexing
- Query optimization
- Connection pooling

### **Caching Strategy**
- Redis caching
- Query result caching
- Static file caching
- Session storage

## 🤝 Contributing

### **Development Workflow**
1. Fork the repository
2. Create feature branch
3. Make changes with tests
4. Submit pull request
5. Code review process

### **Code Standards**
- Follow PEP 8
- Write docstrings
- Add type hints
- Include tests

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

### **Documentation**
- API documentation: `/api/docs/`
- ReDoc documentation: `/api/redoc/`
- Schema: `/api/schema/`

### **Contact**
- Issues: GitHub Issues
- Discussions: GitHub Discussions
- Email: support@medlink.com

## 🔮 Future Roadmap

### **Phase 2 Features**
- [ ] Video consultations
- [ ] Payment integration
- [ ] Insurance verification
- [ ] Prescription management
- [ ] Lab result integration
- [ ] Mobile app development

### **Phase 3 Features**
- [ ] AI-powered diagnosis assistance
- [ ] Telemedicine equipment integration
- [ ] Multi-language support
- [ ] Advanced analytics dashboard
- [ ] Integration with EHR systems

---

**MedLink** - Connecting Healthcare, Digitally. 🏥💻
