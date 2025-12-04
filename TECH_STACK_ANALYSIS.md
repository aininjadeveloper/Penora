# PenoraWriter - Complete Tech Stack Analysis

## 📋 Project Overview
**PenoraWriter** is an AI-powered text generation platform that allows users to create content through single prompts or multi-chapter stories. It operates on a credit-based system with integrated payment processing and cross-app authentication.

---

## 🛠️ Technology Stack

### **Backend Framework**
- **Flask 3.1.1+** - Python web framework
- **Python 3.11+** - Programming language
- **Gunicorn 23.0.0+** - WSGI HTTP Server for production
- **Werkzeug 3.1.3+** - WSGI utilities (password hashing, sessions)

### **Database**
- **SQLAlchemy 2.0.41+** - ORM (Object-Relational Mapping)
- **Flask-SQLAlchemy 3.1.1+** - Flask extension for SQLAlchemy
- **Flask-Migrate 4.1.0+** - Database migrations
- **PostgreSQL** (Production) - via `psycopg2-binary 2.9.10+`
- **SQLite** (Development) - Default database (`users.db`, `unified_system.db`)

### **Authentication & Security**
- **Flask-Login 0.6.3+** - User session management
- **Google OAuth 2.0** - Social authentication
  - `google-api-python-client 2.177.0+`
  - `google-auth-httplib2 0.2.0+`
  - `google-auth-oauthlib 1.2.2+`
- **JWT Authentication** - Token-based auth (`pyjwt 2.10.1+`)
- **OAuthLib 3.3.1+** - OAuth implementation
- **Authlib 1.6.1+** - Authentication library
- **Flask-WTF 1.2.2+** - CSRF protection
- **ProxyFix** - HTTPS proxy support

### **AI Services**
- **DeepInfra API** - Primary AI text generation
  - Models: `mistralai/Mistral-7B-Instruct-v0.3`
  - Alternative models: Llama-4 Maverick, Mixtral-8, OpenChat-3.5, Gemma-7b
  - API Key required: `DEEPINFRA_API_KEY`

### **Payment Processing**
- **Razorpay 1.4.2+** - Payment gateway integration
  - Credit packages: 10, 25, 50, 100 credits
  - INR currency support
  - Payment verification and order management

### **External Integrations**
- **SukuSuku.ai** - Main website SSO integration
  - JWT authentication
  - URL parameter-based authentication
  - Shared user database
  - Credit synchronization
- **ImageGene** - Cross-app integration
  - Unified credit system
  - Shared workspace (1MB limit)
  - API key authentication (`PENORA_API_KEY`)

### **File Processing & Export**
- **ReportLab 4.4.3+** - PDF generation
- **python-docx 1.2.0+** - Word document (.docx) creation
- **PyPDF2 3.0.1+** - PDF manipulation
- **BeautifulSoup4 4.13.4+** - HTML parsing
- **python-dotenv 1.1.1+** - Environment variable management

### **Frontend**
- **Jinja2** - Template engine (Flask default)
- **Bootstrap 5** - CSS framework
- **Custom Dark Theme** - Dark red theme (`dark-red-theme.css`)
- **Font Awesome 6.4.0** - Icons
- **JavaScript** - Client-side interactivity
  - Real-time credit sync (`real_sync.js`)
  - Razorpay checkout integration
  - AJAX requests for API calls

### **HTTP & Networking**
- **Requests 2.32.4+** - HTTP library for API calls
- **Flask-CORS 6.0.1+** - Cross-Origin Resource Sharing

### **Additional Services**
- **Email Validator 2.2.0+** - Email validation
- **Dropbox 12.0.2+** - Cloud storage (planned integration)
- **PayPal SDK 1.13.3+** - Alternative payment (available)

---

## 📁 Project Structure

```
PenoraWriter/
├── app.py                 # Flask app initialization
├── main.py                # Application entry point
├── models.py              # Database models (User, Transaction, Generation, etc.)
├── routes.py              # Main application routes
├── auth_blueprint.py      # Authentication routes
├── credits_blueprint.py   # Credit management routes
├── ai_service.py          # DeepInfra AI integration
├── razorpay_service.py    # Payment processing
├── sukusuku_integration.py # SSO integration
├── unified_api_endpoints.py # Cross-app APIs
├── templates/             # Jinja2 HTML templates
│   ├── base.html
│   ├── index.html
│   ├── auth/
│   ├── credits/
│   └── ...
├── static/                # Static assets
│   ├── css/
│   └── js/
├── pyproject.toml         # Python dependencies
├── deploy.sh              # Deployment script
└── *.db                   # SQLite databases
```

---

## 🔑 Required Environment Variables

### **Core Configuration**
```bash
SECRET_KEY=your-flask-secret-key
SESSION_SECRET=your-session-secret-key
JWT_SECRET_KEY=your-jwt-secret-key
DATABASE_URL=postgresql://user:password@localhost/penora_db
```

### **AI Service**
```bash
DEEPINFRA_API_KEY=your-deepinfra-api-key
```

### **OAuth**
```bash
GOOGLE_OAUTH_CLIENT_ID=your-google-client-id
GOOGLE_OAUTH_CLIENT_SECRET=your-google-client-secret
```

### **Payment**
```bash
RAZORPAY_KEY_ID=your-razorpay-key-id
RAZORPAY_KEY_SECRET=your-razorpay-secret
```

### **External Integrations**
```bash
SUKUSUKU_MAIN_URL=https://suku-suku-site-developeraim.replit.app
PENORA_API_KEY=your-penora-api-key-for-cross-app
AUTO_LOGIN=false
```

---

## 🚀 Deployment Architecture

### **Production Stack**
1. **Web Server**: Nginx (reverse proxy)
2. **Application Server**: Gunicorn (WSGI)
3. **Database**: PostgreSQL
4. **Process Manager**: systemd
5. **SSL**: Let's Encrypt (Certbot)

### **Development Stack**
1. **Web Server**: Flask development server
2. **Database**: SQLite
3. **No reverse proxy needed**

---

## 📊 Key Features

### **User Management**
- Email/password authentication
- Google OAuth 2.0
- JWT SSO from SukuSuku.ai
- User isolation and data security

### **Credit System**
- Welcome bonus: 10 free credits
- 1 credit ≈ 100 words generated
- Real-time credit balance
- Transaction history
- Credit purchases via Razorpay

### **AI Generation**
- Single prompt generation
- Multi-chapter story creation
- Multiple AI models support
- Dynamic credit cost preview

### **Content Management**
- Workspace for saving projects
- Export to PDF, DOCX, TXT
- Project sharing (6-character codes)
- Storage tracking (1MB limit per user)

### **API Integration**
- Unified API endpoints for cross-app access
- API key authentication
- Real-time credit synchronization
- Project sharing between apps

---

## 🔒 Security Features

- Password hashing with Werkzeug
- CSRF protection (Flask-WTF)
- JWT token validation
- API key authentication
- User data isolation
- HTTPS support (ProxyFix)
- Secure session management

---

## 📈 Scalability Considerations

- **Database Connection Pooling**: SQLAlchemy pool configuration
- **Gunicorn Workers**: Configurable worker processes
- **Static File Serving**: Nginx for static assets
- **Caching**: Session-based caching for user data
- **Load Balancing**: Ready for multiple Gunicorn instances

---

## 🐛 Development Tools

- **Logging**: Python logging module
- **Database Migrations**: Flask-Migrate
- **Error Handling**: Comprehensive try-catch blocks
- **Health Checks**: `/health` and `/health/detailed` endpoints

---

## 📝 Notes

- The application is designed for both standalone and integrated deployment
- Supports both SQLite (dev) and PostgreSQL (production)
- Cross-app integration with ImageGene for unified credit system
- SSO integration with SukuSuku.ai main website
- Payment processing ready for production use

