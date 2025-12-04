# Penora Deployment Guide

## Quick Deploy (Replit)

### 1. Environment Setup
Add these secrets in Replit → Secrets:

```bash
DEEPINFRA_API_KEY=your_deepinfra_api_key_here
SESSION_SECRET=your_random_secret_key_here  
JWT_SECRET_KEY=your_jwt_secret_here
SUKUSUKU_MAIN_URL=https://sukusuku.ai
AUTO_LOGIN=false
DATABASE_URL=sqlite:///users.db
```

### 2. Quick Deploy
```bash
./deploy.sh
```

### 3. Start Application
The app will automatically start via the Replit workflow:
```bash
gunicorn --bind 0.0.0.0:5000 --reuse-port --reload main:app
```

## Features Ready for Production

✅ **Authentication System**
- Seamless sukusuku.ai integration  
- Real user data detection from URL parameters
- Individual user isolation with separate workspaces
- Fallback authentication for development

✅ **AI Text Generation**
- DeepInfra API integration with multiple models
- Credit-based system (1 credit ≈ 100 words)
- Real-time cost preview and model selection
- Enhanced error handling

✅ **User Management**
- Real user profiles with credits and transaction history
- Automatic credit deduction and transaction logging
- Razorpay payment integration for credit purchases
- Complete data isolation between users

✅ **Content Features**
- Single text generation and multi-chapter stories
- Workspace for saving and managing projects
- Export to PDF, DOCX, and TXT formats
- Real-time credit balance in navigation

✅ **Database & Security**
- SQLite database with proper relationships
- Session management with ProxyFix for HTTPS
- Input validation and error handling
- CSRF protection and secure password hashing

## Current Status

The application is fully functional with:
- Authentication working with real user data (Lucifer_Jhon with 90 credits)
- All routes fixed and error-free
- Proper user isolation and data persistence
- Ready for production deployment

## Access URLs

- Homepage: `/` or `/penora`
- Start Writing: `/start-writing`
- My Workspace: `/workspace`
- Account Dashboard: `/account`
- Pricing: `/pricing`

The app automatically detects users from sukusuku.ai URL parameters and maintains individual sessions.