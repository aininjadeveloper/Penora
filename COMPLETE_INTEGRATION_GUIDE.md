# Complete Penora x SukuSuku Integration Guide

This guide covers everything from pushing your code to making it live and connected to SukuSuku.ai.

## 📋 Overview

1.  **Push Code**: Send your local code to GitHub.
2.  **VPS Setup**: Install Penora on your Hostinger VPS.
3.  **Nginx Setup**: Expose Penora on port 80/443 (Essential for production).
4.  **Connect SukuSuku**: Configure the integration.

---

## Part 1: Push Code to GitHub

Do this on your **Local Machine** (where you are now).

1.  **Check status**:
    ```bash
    git status
    ```
2.  **Add all changes**:
    ```bash
    git add .
    ```
3.  **Commit**:
    ```bash
    git commit -m "Ready for deployment"
    ```
4.  **Push**:
    ```bash
    git push origin main
    ```

---

## Part 2: VPS Setup (Fresh Install)

Do this on your **VPS** (SSH in as root).

### 1. Clean Slate (Optional but recommended)
```bash
systemctl stop penora
rm -rf /var/www/penora
```

### 2. Install & Configure
```bash
# Setup folder
mkdir -p /var/www/penora
cd /var/www/penora

# Clone code
git clone https://github.com/aininjadeveloper/Penora.git .

# Setup Python environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Environment Variables (.env)
Create the file:
```bash
nano .env
```
**Paste your secrets.** Important fields for integration:
```ini
DATABASE_URL=sqlite:///users.db
SUKUSUKU_MAIN_URL=https://sukusuku.ai
# Add your other keys (DEEPINFRA, GOOGLE, etc.)
```

### 4. Systemd Service
Create the service to keep Penora running:
```bash
nano /etc/systemd/system/penora.service
```
Content:
```ini
[Unit]
Description=Penora Flask App
After=network.target

[Service]
User=root
Group=www-data
WorkingDirectory=/var/www/penora
Environment="PATH=/var/www/penora/venv/bin"
ExecStart=/var/www/penora/venv/bin/gunicorn --workers 2 --bind 127.0.0.1:5100 main:app
Restart=always

[Install]
WantedBy=multi-user.target
```
Start it:
```bash
systemctl daemon-reload
systemctl enable penora
systemctl restart penora
```

---

## Part 3: Nginx Reverse Proxy (Crucial!)

To make your app accessible via a domain (or IP) without port 5100, and to handle CORS properly.

### 1. Install Nginx (if not installed)
```bash
apt update
apt install nginx -y
```

### 2. Configure Nginx
Create a config file:
```bash
nano /etc/nginx/sites-available/penora
```
Content (Replace `your_domain_or_IP` with your actual IP or domain):
```nginx
server {
    listen 80;
    server_name 82.25.105.23;  # OR your domain like penora.yourdomain.com

    location / {
        proxy_pass http://127.0.0.1:5100;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        
        # CORS Headers (Extra safety)
        add_header 'Access-Control-Allow-Origin' 'https://sukusuku.ai' always;
        add_header 'Access-Control-Allow-Methods' 'GET, POST, OPTIONS' always;
        add_header 'Access-Control-Allow-Headers' 'Content-Type, Authorization, X-API-Key' always;
    }
}
```

### 3. Enable & Restart
```bash
ln -s /etc/nginx/sites-available/penora /etc/nginx/sites-enabled/
rm /etc/nginx/sites-enabled/default  # Remove default if needed
nginx -t  # Test config
systemctl restart nginx
```

---

## Part 4: Connect to SukuSuku.ai

Now that Penora is live at `http://82.25.105.23` (or your domain), you need to tell SukuSuku where to send users.

### 1. Update SukuSuku Settings
In the SukuSuku application settings (wherever it defines the "Writing Tool" URL), set the **Redirect URL** to:
`http://82.25.105.23/`

### 2. Verify Integration
1.  Log in to **SukuSuku.ai**.
2.  Click the "Open Penora" (or similar) button.
3.  It should redirect you to:
    `http://82.25.105.23/?user_id=...&email=...`
4.  **Penora should load and show your name/credits immediately.**

## ✅ Checklist for "Full Working" Status
- [ ] Penora Service is `active (running)`.
- [ ] Nginx is proxying port 80 -> 5100.
- [ ] `https://sukusuku.ai` is allowed in CORS (we added this in code).
- [ ] SukuSuku redirects to the correct VPS IP/Domain.
