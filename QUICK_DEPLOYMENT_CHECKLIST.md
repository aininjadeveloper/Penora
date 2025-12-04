# Quick Deployment Checklist for Hostinger VPS

## 🎯 What You Need Before Starting

### **1. VPS Information**
- [ ] VPS IP address: `_________________`
- [ ] SSH username: `_________________`
- [ ] SSH password/key: `_________________`
- [ ] Domain name (optional): `_________________`

### **2. API Keys & Secrets**
- [ ] DeepInfra API Key: `_________________`
- [ ] Google OAuth Client ID (optional): `_________________`
- [ ] Google OAuth Client Secret (optional): `_________________`
- [ ] Razorpay Key ID (optional): `_________________`
- [ ] Razorpay Key Secret (optional): `_________________`
- [ ] PENORA_API_KEY (for cross-app): `_________________`

### **3. Database Credentials**
- [ ] Database name: `penora_db`
- [ ] Database user: `penora_user`
- [ ] Database password: `_________________` (create a strong password)

---

## 🚀 Quick Commands Reference

### **Connect to VPS**
```bash
ssh your-username@your-vps-ip
```

### **One-Line Setup (After connecting)**
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install essentials
sudo apt install -y python3 python3-pip python3-venv python3-dev build-essential libpq-dev postgresql postgresql-contrib nginx git

# Create app directory
sudo mkdir -p /var/www/penora && sudo chown $USER:$USER /var/www/penora
```

### **Upload Files (From Your Local Machine)**
```bash
# Using SCP (run from your local machine)
scp -r C:\Users\Tn22\Downloads\PenoraWriter\* your-username@your-vps-ip:/var/www/penora/
```

### **Setup Database**
```bash
sudo -u postgres psql
# Then run:
CREATE DATABASE penora_db;
CREATE USER penora_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE penora_db TO penora_user;
\q
```

### **Install Dependencies**
```bash
cd /var/www/penora
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install flask gunicorn psycopg2-binary flask-sqlalchemy flask-migrate flask-login python-dotenv requests reportlab python-docx pyjwt razorpay flask-cors pypdf2 beautifulsoup4
```

### **Create .env File**
```bash
nano /var/www/penora/.env
# Paste your environment variables (see HOSTINGER_VPS_DEPLOYMENT.md)
```

### **Initialize Database**
```bash
cd /var/www/penora
source venv/bin/activate
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

### **Create Gunicorn Service**
```bash
sudo nano /etc/systemd/system/penora.service
# Paste service configuration (see HOSTINGER_VPS_DEPLOYMENT.md)
sudo systemctl daemon-reload
sudo systemctl enable penora
sudo systemctl start penora
```

### **Configure Nginx**
```bash
sudo nano /etc/nginx/sites-available/penora
# Paste Nginx configuration (see HOSTINGER_VPS_DEPLOYMENT.md)
sudo ln -s /etc/nginx/sites-available/penora /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### **Check Status**
```bash
sudo systemctl status penora
sudo systemctl status nginx
sudo systemctl status postgresql
```

---

## 📋 Information I Need to Help You Deploy

If you want me to help you deploy, please provide:

1. **VPS Access:**
   - IP address
   - SSH username
   - SSH password (or key file path)
   - Operating system (Ubuntu/CentOS version)

2. **Domain (if you have one):**
   - Domain name
   - DNS already pointing to VPS IP?

3. **API Keys:**
   - DeepInfra API Key
   - Google OAuth credentials (if using)
   - Razorpay credentials (if using)

4. **Preferences:**
   - Database password you want to use
   - Any custom configurations

---

## ⚠️ Important Notes

1. **Security**: Never share your actual passwords/keys in chat. Use secure methods.
2. **Backup**: Always backup your database before major changes.
3. **Testing**: Test locally on VPS before making it public.
4. **Updates**: Keep your system and packages updated regularly.

---

## 🆘 Common Issues & Quick Fixes

### **Can't connect via SSH**
- Check VPS IP and credentials
- Verify SSH service is running on VPS
- Check firewall settings

### **Permission denied errors**
```bash
sudo chown -R www-data:www-data /var/www/penora
sudo chmod -R 755 /var/www/penora
```

### **502 Bad Gateway**
```bash
sudo systemctl restart penora
sudo systemctl status penora
```

### **Database connection failed**
```bash
sudo systemctl restart postgresql
# Verify credentials in .env file
```

---

## 📞 Next Steps

1. **Read the full guide**: `HOSTINGER_VPS_DEPLOYMENT.md`
2. **Understand the stack**: `TECH_STACK_ANALYSIS.md`
3. **Gather your information** (see checklist above)
4. **Start deployment** following the step-by-step guide

---

**Ready to deploy?** Follow `HOSTINGER_VPS_DEPLOYMENT.md` for detailed instructions!

