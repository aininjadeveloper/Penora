# Hostinger VPS Deployment Guide - PenoraWriter

## 📋 Prerequisites

Before starting, ensure you have:
- ✅ Hostinger VPS with Ubuntu 20.04/22.04 or CentOS 7/8
- ✅ SSH access to your VPS
- ✅ Root or sudo access
- ✅ Domain name pointed to your VPS IP (optional but recommended)
- ✅ All API keys and secrets ready

---

## 🚀 Step-by-Step Deployment

### **Step 1: Connect to Your VPS**

```bash
ssh root@your-vps-ip
# or
ssh your-username@your-vps-ip
```

### **Step 2: Update System Packages**

```bash
# For Ubuntu/Debian
sudo apt update && sudo apt upgrade -y

# For CentOS/RHEL
sudo yum update -y
```
# Hostinger VPS Deployment Guide - PenoraWriter

## 📋 Prerequisites

Before starting, ensure you have:
- ✅ Hostinger VPS with Ubuntu 20.04/22.04 or CentOS 7/8
- ✅ SSH access to your VPS
- ✅ Root or sudo access
- ✅ Domain name pointed to your VPS IP (optional but recommended)
- ✅ All API keys and secrets ready

---

## 🚀 Step-by-Step Deployment

### **Step 1: Connect to Your VPS**

```bash
ssh root@your-vps-ip
# or
ssh your-username@your-vps-ip
```

### **Step 2: Update System Packages**

```bash
# For Ubuntu/Debian
sudo apt update && sudo apt upgrade -y

# For CentOS/RHEL
sudo yum update -y
```

### **Step 3: Install Python and Required Tools**

```bash
# Ubuntu/Debian
sudo apt install -y python3 python3-pip python3-venv python3-dev
sudo apt install -y build-essential nginx

# CentOS/RHEL
sudo yum install -y python3 python3-pip python3-devel
sudo yum install -y gcc nginx
```

### **Step 4: Create Application Directory**

```bash
sudo mkdir -p /var/www/penora
sudo chown $USER:$USER /var/www/penora
cd /var/www/penora
```

### **Step 5: Upload Your Application**

**Option A: Using Git (Recommended)**
```bash
# If your code is in a Git repository
git clone https://your-repository-url.git .

# Or if you need to upload manually, use SCP from your local machine:
# scp -r /path/to/PenoraWriter/* user@your-vps-ip:/var/www/penora/
```

**Option B: Using SCP (Manual Upload)**
From your local machine:
```bash
scp -r C:\Users\Tn22\Downloads\PenoraWriter\* user@your-vps-ip:/var/www/penora/
```

### **Step 6: Create Virtual Environment**

```bash
cd /var/www/penora
python3 -m venv venv
source venv/bin/activate
```

### **Step 7: Install Python Dependencies**

```bash
# Upgrade pip
pip install --upgrade pip setuptools wheel

# Install dependencies from pyproject.toml
pip install email-validator>=2.2.0
pip install flask-login>=0.6.3
pip install flask>=3.1.1
pip install flask-sqlalchemy>=3.1.1
pip install gunicorn>=23.0.0
pip install oauthlib>=3.3.1
pip install reportlab>=4.4.3
pip install sqlalchemy>=2.0.41
pip install werkzeug>=3.1.3
pip install requests>=2.32.4
pip install paypalrestsdk>=1.13.3
pip install dropbox>=12.0.2
pip install google-api-python-client>=2.177.0
pip install google-auth-httplib2>=0.2.0
pip install google-auth-oauthlib>=1.2.2
pip install python-docx>=1.2.0
pip install authlib>=1.6.1
pip install python-dotenv>=1.1.1
pip install flask-migrate>=4.1.0
pip install docx>=0.2.4
pip install flask-wtf>=1.2.2
pip install pyjwt>=2.10.1
pip install razorpay>=1.4.2
pip install flask-cors>=6.0.1
pip install pypdf2>=3.0.1
pip install beautifulsoup4>=4.13.4
```

**Or create a requirements.txt and install:**
```bash
# Create requirements.txt
cat > requirements.txt << EOF
email-validator>=2.2.0
flask-login>=0.6.3
flask>=3.1.1
flask-sqlalchemy>=3.1.1
gunicorn>=23.0.0
oauthlib>=3.3.1
reportlab>=4.4.3
sqlalchemy>=2.0.41
werkzeug>=3.1.3
requests>=2.32.4
paypalrestsdk>=1.13.3
dropbox>=12.0.2
google-api-python-client>=2.177.0
google-auth-httplib2>=0.2.0
google-auth-oauthlib>=1.2.2
python-docx>=1.2.0
authlib>=1.6.1
python-dotenv>=1.1.1
flask-migrate>=4.1.0
docx>=0.2.4
flask-wtf>=1.2.2
pyjwt>=2.10.1
razorpay>=1.4.2
flask-cors>=6.0.1
pypdf2>=3.0.1
beautifulsoup4>=4.13.4
EOF

pip install -r requirements.txt
```

### **Step 8: Configure Environment Variables**

```bash
cd /var/www/penora
nano .env
```

**Add the following (replace with your actual values):**
```env
# Flask Configuration
SECRET_KEY="your-super-secure-secret-key"
SESSION_SECRET="another-secure-secret-key"
JWT_SECRET_KEY="your-jwt-secret-key"

# Database (SQLite for production with single worker)
DATABASE_URL="sqlite:///users.db"

# DeepInfra AI
DEEPINFRA_API_KEY="your-deepinfra-api-key-here"

# Google OAuth (Optional)
GOOGLE_OAUTH_CLIENT_ID="your-google-client-id"
GOOGLE_OAUTH_CLIENT_SECRET="your-google-client-secret"

# Razorpay (Optional)
RAZORPAY_KEY_ID="your-razorpay-key-id"
RAZORPAY_KEY_SECRET="your-razorpay-secret"

# External Integrations
SUKUSUKU_MAIN_URL="https://sukusuku.ai"
PENORA_API_KEY="your-penora-api-key"
AUTO_LOGIN="false"
```

**Generate secure keys:**
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

### **Step 9: Initialize Database**

```bash
cd /var/www/penora
source venv/bin/activate

# Initialize database tables
python3 -c "from app import app, db; app.app_context().push(); db.create_all()"
python3 -c "from sukusuku_integration import sukusuku_integration; sukusuku_integration.init_database()"
```

### **Step 10: Test Application Locally**

```bash
cd /var/www/penora
source venv/bin/activate
gunicorn --bind 127.0.0.1:5000 main:app
```

**Test in another terminal:**
```bash
curl http://localhost:5000
```

If it works, press `Ctrl+C` to stop.

### **Step 11: Create Systemd Service**

> **IMPORTANT**: We use 1 worker (`--workers 1`) because SQLite does not support concurrent writes from multiple processes well.

```bash
sudo nano /etc/systemd/system/penora.service
```

**Add the following:**
```ini
[Unit]
Description=PenoraWriter Flask Application
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/penora
Environment="PATH=/var/www/penora/venv/bin"
EnvironmentFile=/var/www/penora/.env
ExecStart=/var/www/penora/venv/bin/gunicorn \
    --workers 1 \
    --bind 127.0.0.1:5000 \
    --timeout 120 \
    --keep-alive 5 \
    --max-requests 1000 \
    --max-requests-jitter 50 \
    main:app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Set permissions and start service:**
```bash
sudo chown -R www-data:www-data /var/www/penora
sudo chmod -R 755 /var/www/penora
sudo systemctl daemon-reload
sudo systemctl enable penora
sudo systemctl start penora
sudo systemctl status penora
```

### **Step 12: Configure Nginx**

```bash
sudo nano /etc/nginx/sites-available/penora
```

**Add the following (replace `yourdomain.com` with your domain):**
```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    
    # Increase body size for file uploads
    client_max_body_size 10M;
    
    # Static files
    location /static {
        alias /var/www/penora/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
    
    # Proxy to Gunicorn
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $server_name;
        
        # WebSocket support (if needed)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
}
```

**Enable site and test:**
```bash
sudo ln -s /etc/nginx/sites-available/penora /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default  # Remove default site if exists
sudo nginx -t
sudo systemctl restart nginx
```

### **Step 13: Configure Firewall**

```bash
# Ubuntu/Debian (UFW)
sudo ufw allow 'Nginx Full'
sudo ufw allow ssh
sudo ufw enable

# CentOS/RHEL (firewalld)
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --permanent --add-service=ssh
sudo firewall-cmd --reload
```

### **Step 14: Install SSL Certificate (Recommended)**

```bash
# Install Certbot
sudo apt install -y certbot python3-certbot-nginx  # Ubuntu/Debian
# OR
sudo yum install -y certbot python3-certbot-nginx  # CentOS/RHEL

# Get SSL certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Auto-renewal
sudo systemctl enable certbot.timer
```

### **Step 15: Verify Deployment**

1.  **Check Gunicorn service:**
    ```bash
    sudo systemctl status penora
    ```

2.  **Check Nginx:**
    ```bash
    sudo systemctl status nginx
    ```

3.  **Check logs:**
    ```bash
    # Application logs
    sudo journalctl -u penora -f
    
    # Nginx error logs
    sudo tail -f /var/log/nginx/error.log
    
    # Nginx access logs
    sudo tail -f /var/log/nginx/access.log
    ```

4.  **Test your website:**
    -   Visit `http://yourdomain.com` or `http://your-vps-ip`
    -   Check if the homepage loads
    -   Test authentication
    -   Test AI generation

---

## 🔧 Troubleshooting

### **502 Bad Gateway**
- Check if Gunicorn is running: `sudo systemctl status penora`
- Check Gunicorn logs: `sudo journalctl -u penora -n 50`
- Verify Nginx proxy settings

### **Database Locked**
- Ensure you are using `--workers 1` in the systemd service file. SQLite cannot handle multiple concurrent writers from different processes.

### **Permission Denied**
- Fix ownership: `sudo chown -R www-data:www-data /var/www/penora`
- Fix permissions: `sudo chmod -R 755 /var/www/penora`

### **Static Files Not Loading**
- Check Nginx static file configuration
- Verify file paths and permissions
- Check Nginx error logs

### **Google OAuth Not Working**
- Verify redirect URIs in Google Cloud Console
- Update redirect URI to: `https://yourdomain.com/auth/google/callback`
- Check environment variables

---

## 📊 Monitoring & Maintenance

### **View Application Logs**
```bash
sudo journalctl -u penora -f
```

### **Restart Services**
```bash
sudo systemctl restart penora
sudo systemctl restart nginx
```

### **Update Application**
```bash
cd /var/www/penora
source venv/bin/activate
git pull  # If using Git
# Or upload new files via SCP
pip install -r requirements.txt  # If dependencies changed
# No database migration needed for SQLite unless schema changes are handled manually
sudo systemctl restart penora
```

---

## 🔐 Security Checklist

- [ ] Secure SECRET_KEY and SESSION_SECRET
- [ ] SSL certificate installed
- [ ] Firewall configured
- [ ] Regular system updates
- [ ] API keys secured in `.env` file
- [ ] `.env` file not in Git repository
- [ ] Nginx security headers configured
- [ ] File permissions set correctly

---

## 📞 Support Information

If you need help with deployment, provide:
1.  VPS operating system and version
2.  Error messages from logs
3.  Domain name (if configured)
4.  Any custom configurations

---

## ✅ Deployment Checklist

- [ ] VPS access configured
- [ ] Python 3.11+ installed
- [ ] Nginx installed
- [ ] Application files uploaded
- [ ] Virtual environment created
- [ ] Dependencies installed
- [ ] Environment variables configured (.env)
- [ ] Database initialized (SQLite)
- [ ] Gunicorn service created (workers=1)
- [ ] Nginx configured and running
- [ ] Firewall configured
- [ ] SSL certificate installed
- [ ] Application tested and working
- [ ] Monitoring set up

---

**Your PenoraWriter application should now be live! 🎉**

Visit your domain or VPS IP to access the application.
