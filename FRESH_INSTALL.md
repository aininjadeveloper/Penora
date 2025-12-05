# Fresh VPS Installation Guide

**⚠️ WARNING: This will DELETE all existing data, database, and configuration on the VPS.**

## Phase 1: Cleanup (The "Nuke" Part)

Run these commands to completely remove the old installation:

```bash
# 1. Stop and remove the service
systemctl stop penora
systemctl disable penora
rm /etc/systemd/system/penora.service
systemctl daemon-reload

# 2. Delete the project directory
rm -rf /var/www/penora

# 3. Verify it's gone
ls -F /var/www/
# (Should NOT show 'penora/')
```

## Phase 2: Fresh Setup

```bash
# 1. Create directory and enter it
mkdir -p /var/www/penora
cd /var/www/penora

# 2. Clone the repository (into the current directory)
git clone https://github.com/aininjadeveloper/Penora.git .

# 3. Create virtual environment
python3 -m venv venv
source venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt
```

## Phase 3: Configuration

### 1. Create .env file
You need to copy your secrets. Run this:
```bash
nano .env
```

**PASTE your local `.env` content here.**
*Make sure `DATABASE_URL=sqlite:///users.db` is present.*
*Save and exit (Ctrl+X, Y, Enter).*

### 2. Create Systemd Service
Run this to create the service file:
```bash
nano /etc/systemd/system/penora.service
```

**PASTE this exact content:**
```ini
[Unit]
Description=Penora Flask App (Gunicorn)
After=network.target

[Service]
User=root
Group=www-data
WorkingDirectory=/var/www/penora
Environment="PATH=/var/www/penora/venv/bin"
ExecStart=/var/www/penora/venv/bin/gunicorn --workers 2 --bind 127.0.0.1:5100 --timeout 120 main:app
Restart=always

[Install]
WantedBy=multi-user.target
```
*Save and exit (Ctrl+X, Y, Enter).*

## Phase 4: Launch

```bash
# 1. Start the service
systemctl daemon-reload
systemctl start penora
systemctl enable penora

# 2. Verify status
systemctl status penora
```

You should see `active (running)`.
