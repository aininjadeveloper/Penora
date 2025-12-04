# Penora - AI Text Generation Platform

Penora is a credit-based AI text generation platform that allows users to create content through single prompts or multi-chapter stories. Built with Flask and powered by DeepInfra's mistralai/Mistral-7B-Instruct-v0.3 model.

## Features

- **Dual Authentication System**: Email/password login and Google OAuth 2.0
- **Credit-Based System**: 1 credit ≈ 100 words generated (rounded up)
- **Welcome Bonus**: New users receive 10 free credits
- **AI Text Generation**: Single prompts and multi-chapter stories
- **Multiple Export Formats**: PDF, Word Doc (.docx), plain text
- **Live Credit Balance**: Real-time credit tracking in navigation
- **Account Management**: Transaction history and credit purchases

## Tech Stack

- **Backend**: Flask with SQLAlchemy ORM
- **Database**: PostgreSQL (production) / SQLite (development)
- **Authentication**: Flask-Login + Google OAuth 2.0
- **AI Service**: DeepInfra mistralai/Mistral-7B-Instruct-v0.3
- **Frontend**: Bootstrap 5 with dark theme
- **Export**: ReportLab (PDF), python-docx (Word)

## Installation & Development

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd penora
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Environment Setup**
   ```bash
   cp .env.example .env
   # Edit .env with your actual values
   ```

4. **Initialize Database**
   ```bash
   flask db init
   flask db migrate -m "Initial migration"
   flask db upgrade
   ```

5. **Run the application**
   ```bash
   python main.py
   # or
   flask run
   ```

## Environment Variables

Required environment variables (see `.env.example`):

- `SECRET_KEY`: Flask secret key for sessions
- `DATABASE_URL`: Database connection string
- `DEEPINFRA_API_KEY`: DeepInfra API key for text generation
- `GOOGLE_OAUTH_CLIENT_ID`: Google OAuth client ID
- `GOOGLE_OAUTH_CLIENT_SECRET`: Google OAuth client secret
- `SESSION_SECRET`: Session encryption key

## Google OAuth Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
2. Create a new OAuth 2.0 Client ID
3. Add authorized redirect URI: `https://yourdomain.com/auth/google/callback`
4. Copy client ID and secret to environment variables

## Deploy to Hostinger VPS

### Prerequisites

- Hostinger VPS with Ubuntu/CentOS
- SSH access to your VPS
- Domain name pointed to your server IP

### Step 1: Server Setup

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install Python and pip
sudo apt install python3 python3-pip python3-venv -y

# Install PostgreSQL
sudo apt install postgresql postgresql-contrib -y

# Install nginx (web server)
sudo apt install nginx -y

# Install git
sudo apt install git -y
```

### Step 2: Database Setup

```bash
# Switch to postgres user
sudo -u postgres psql

# Create database and user
CREATE DATABASE penora_db;
CREATE USER penora_user WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE penora_db TO penora_user;
\q
```

### Step 3: Application Deployment

```bash
# Create application directory
sudo mkdir -p /var/www/penora
sudo chown $USER:$USER /var/www/penora

# Clone your repository
cd /var/www/penora
git clone <your-repository-url> .

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install gunicorn psycopg2-binary
```

### Step 4: Environment Configuration

```bash
# Create production environment file
cp .env.example .env
nano .env
```

Configure with production values:
```env
SECRET_KEY=your-super-secure-secret-key-here
DATABASE_URL=postgresql://penora_user:your_secure_password@localhost/penora_db
DEEPINFRA_API_KEY=your-deepinfra-api-key
GOOGLE_OAUTH_CLIENT_ID=your-google-client-id
GOOGLE_OAUTH_CLIENT_SECRET=your-google-client-secret  
SESSION_SECRET=another-secure-secret-for-sessions
```

### Step 5: Database Migration

```bash
# Initialize database
flask db init
flask db migrate -m "Production setup"
flask db upgrade
```

### Step 6: Gunicorn Service

Create systemd service file:

```bash
sudo nano /etc/systemd/system/penora.service
```

```ini
[Unit]
Description=Penora Flask Application
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/penora
Environment="PATH=/var/www/penora/venv/bin"
ExecStart=/var/www/penora/venv/bin/gunicorn --workers 3 --bind 0.0.0.0:5000 main:app
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
# Set permissions
sudo chown -R www-data:www-data /var/www/penora

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable penora
sudo systemctl start penora
sudo systemctl status penora
```

### Step 7: Nginx Configuration

```bash
sudo nano /etc/nginx/sites-available/penora
```

```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location /static {
        alias /var/www/penora/static;
        expires 30d;
    }
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/penora /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### Step 8: SSL Certificate (Optional but Recommended)

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx -y

# Get SSL certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Auto-renewal
sudo systemctl enable certbot.timer
```

### Step 9: Firewall Configuration

```bash
# Configure UFW firewall
sudo ufw allow 'Nginx Full'
sudo ufw allow ssh
sudo ufw enable
```

### Step 10: Monitoring & Maintenance

```bash
# Check application logs
sudo journalctl -u penora -f

# Check nginx logs
sudo tail -f /var/log/nginx/error.log
sudo tail -f /var/log/nginx/access.log

# Restart services if needed
sudo systemctl restart penora
sudo systemctl restart nginx
```

### Important Notes for Hostinger VPS:

1. **Resource Limits**: Monitor CPU and RAM usage. Upgrade your VPS plan if needed.
2. **Backup Strategy**: Set up automated database backups.
3. **Security**: Keep system packages updated and use strong passwords.
4. **Domain Configuration**: Ensure your domain DNS points to your VPS IP address.
5. **Google OAuth**: Update redirect URIs to use your production domain.

### Troubleshooting:

- **502 Bad Gateway**: Check if Gunicorn service is running
- **Permission Denied**: Verify file permissions and ownership
- **Database Connection**: Ensure PostgreSQL is running and credentials are correct
- **Google OAuth**: Verify redirect URIs match exactly

Your Penora application should now be live and accessible at your domain!

## Credit System Details

- **New User Bonus**: 10 free credits upon registration
- **Usage**: 1 credit per ~100 words generated (minimum 1 credit)
- **Pricing**: Configurable credit packages starting from $0.50
- **Tracking**: All transactions logged with detailed descriptions

## API Integration

Currently integrated with:
- **DeepInfra Mistral-7B**: Primary text generation
- **Google OAuth 2.0**: Social authentication

## Export Capabilities

- **PDF**: Professional formatting with ReportLab
- **Word Doc**: .docx format with proper styling
- **Plain Text**: Simple .txt format
- **Future**: Google Drive and Dropbox integration planned

## License

This project is proprietary software. All rights reserved.