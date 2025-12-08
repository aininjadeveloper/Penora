# VPS Deployment Guide - Update Penora Download Fixes

## Connection Details
- **Host**: 82.25.105.23
- **User**: root
- **App Directory**: /var/www/penora
- **Repository**: https://github.com/aininjadeveloper/Penora.git

---

## Step-by-Step Deployment Instructions

### STEP 1: Connect to Your VPS
```bash
ssh root@82.25.105.23
```
Enter your password when prompted.

---

### STEP 2: Navigate to Application Directory
```bash
cd /var/www/penora
```

---

### STEP 3: Check Current Status
```bash
# Check git status
git status

# Verify you're on main branch
git branch
```

Expected output should show you're on `main` branch with no uncommitted changes.

---

### STEP 4: Pull Latest Changes from GitHub
```bash
git pull origin main
```

This will:
- Fetch the latest code from repository
- Automatically merge the download fix changes
- Output should show files being updated

**Expected updates:**
- `routes.py` - Modified (new export_generation route added)
- `templates/view_project.html` - Modified (download URLs fixed)
- `templates/text_editor.html` - Modified (download URLs fixed)
- `DOWNLOAD_FIX_COMPLETE_REPORT.md` - New file
- `DOWNLOAD_FIX_SUMMARY.md` - New file
- `DOWNLOAD_QUICK_REFERENCE.md` - New file

---

### STEP 5: Verify All Files Updated Correctly
```bash
# Check if routes.py has the new export_generation route
grep -n "def export_generation" routes.py

# Should output something like:
# 1618:def export_generation(generation_id, format):
```

---

### STEP 6: Check Application Status

#### If Using Gunicorn:
```bash
# Check if gunicorn process is running
ps aux | grep gunicorn

# Should show running gunicorn processes
```

#### If Using SystemD Service:
```bash
# Check service status
systemctl status penora

# Or if different service name, check:
systemctl status <your-service-name>
```

---

### STEP 7: Restart Application

#### Option A: If Using Gunicorn with Supervisor
```bash
# Restart gunicorn via supervisor
supervisorctl restart penora

# Verify it restarted
supervisorctl status penora
```

#### Option B: If Using SystemD Service
```bash
# Restart the service
systemctl restart penora

# Verify status
systemctl status penora
```

#### Option C: If Running Gunicorn Directly
```bash
# First, find the process ID
PID=$(ps aux | grep gunicorn | grep -v grep | awk '{print $2}')

# Kill the old process
kill -9 $PID

# Start gunicorn again (from your app directory)
cd /var/www/penora
gunicorn -w 4 -b 0.0.0.0:5000 app:app &

# Or if you have a startup script:
./start.sh
```

#### Option D: If Using Nginx + Gunicorn + Systemd
```bash
# Reload systemd and restart service
systemctl daemon-reload
systemctl restart penora

# Check logs
journalctl -u penora -f
```

---

### STEP 8: Verify Application is Running
```bash
# Check if app is listening on port 5000 (or your configured port)
netstat -tuln | grep 5000

# Or use lsof
lsof -i :5000

# Test the application
curl http://localhost:5000/health

# Should return: OK
```

---

### STEP 9: Test Download Functionality

#### Via Browser:
1. Navigate to: `https://sukusuku.ai/penora` (or your domain)
2. Login to your account
3. Create a new story or single prompt
4. Click "Download" button
5. Try downloading as PDF, DOCX, and TXT
6. Verify files download correctly

#### Via curl (Command Line):
```bash
# You'll need a valid session token from sukusuku.ai
# This is for testing purposes only

# Test export_generation endpoint
curl -i http://localhost:5000/export/1/pdf

# Should return 401 if not authenticated (expected)
```

---

### STEP 10: Check Application Logs

#### For Supervisor/Gunicorn:
```bash
# Check supervisor logs
tail -f /var/log/supervisor/penora.log

# Or gunicorn error log
tail -f /var/log/gunicorn/error.log
```

#### For SystemD:
```bash
# View recent logs
journalctl -u penora -n 100

# Follow logs in real-time
journalctl -u penora -f
```

#### For Application Logs:
```bash
# If Flask logs to file
tail -f /var/www/penora/app.log

# Or check if Python logging outputs
cd /var/www/penora
tail -f *.log 2>/dev/null
```

---

## Verification Checklist

After deployment, verify:

- [ ] Git pull completed without conflicts
- [ ] `grep "def export_generation" routes.py` returns line number
- [ ] Application process is running
- [ ] Port 5000 (or configured port) is listening
- [ ] `/health` endpoint responds with OK
- [ ] Can login to application
- [ ] Download button appears in UI
- [ ] PDF download works
- [ ] DOCX download works
- [ ] TXT download works
- [ ] No errors in application logs
- [ ] Application responsive to requests

---

## Troubleshooting

### Issue: "fatal: Not a git repository"
**Solution**: 
```bash
# Check if .git directory exists
ls -la /var/www/penora/.git

# If not, initialize git repo:
cd /var/www/penora
git init
git remote add origin https://github.com/aininjadeveloper/Penora.git
git fetch origin
git checkout -b main origin/main
```

### Issue: "Permission denied" when pulling
**Solution**:
```bash
# Check file permissions
ls -la /var/www/penora/

# If needed, fix permissions
chown -R www-data:www-data /var/www/penora
chmod -R 755 /var/www/penora
```

### Issue: "refused to merge unrelated histories"
**Solution**:
```bash
# Force pull with merge
git pull origin main --allow-unrelated-histories
```

### Issue: Application won't restart / Port already in use
**Solution**:
```bash
# Kill process using the port
fuser -k 5000/tcp

# Or find and kill specific process
PID=$(lsof -ti :5000)
kill -9 $PID

# Restart application
systemctl restart penora
```

### Issue: "ModuleNotFoundError" or import errors
**Solution**:
```bash
# Ensure dependencies are installed
cd /var/www/penora
pip install -r requirements.txt

# Or with virtual environment
source venv/bin/activate
pip install -r requirements.txt

# Restart application
systemctl restart penora
```

### Issue: Export route returns 404
**Solution**:
```bash
# Verify route is in file
grep -A 5 "def export_generation" routes.py

# If not found, git pull didn't work properly
git status
git log --oneline -5

# If needed, do hard reset and pull
git fetch origin
git reset --hard origin/main
```

---

## Quick Reference Commands

```bash
# SSH into VPS
ssh root@82.25.105.23

# Navigate to app
cd /var/www/penora

# Pull latest code
git pull origin main

# Verify changes
grep "def export_generation" routes.py

# Restart application
systemctl restart penora

# Check status
systemctl status penora

# View logs
journalctl -u penora -f

# Test health
curl http://localhost:5000/health
```

---

## What Changed in This Update

### Files Modified:
1. **routes.py**
   - Added 97 lines for new `export_generation()` function
   - Lines 1617-1713
   - Handles PDF/DOCX/TXT exports for individual generations

2. **templates/view_project.html**
   - Fixed 3 download URLs to use `url_for()`
   - Lines 60, 63, 66

3. **templates/text_editor.html**
   - Fixed 3 download URLs to use `url_for()`
   - Lines 76, 79, 82

### New Files:
- `DOWNLOAD_FIX_COMPLETE_REPORT.md` - Technical details
- `DOWNLOAD_FIX_SUMMARY.md` - Implementation guide
- `DOWNLOAD_QUICK_REFERENCE.md` - User guide

---

## Testing the Deployment

### Test 1: Create and Export Story
1. Navigate to Penora application
2. Click "Start Writing" → "Story Generator"
3. Create a story
4. Click Download → Select PDF
5. Verify file downloads as `.pdf`

### Test 2: Create and Export Single Prompt
1. Navigate to Penora application
2. Click "Start Writing" → "Single Prompt"
3. Generate content
4. Click Download → Select DOCX
5. Verify file downloads as `.docx`

### Test 3: Export Workspace Project
1. Navigate to "My Workspace"
2. Click Download on any project
3. Select TXT
4. Verify file downloads as `.txt`

### Test 4: Check Logs for Errors
```bash
# Should see "✅ PDF generated successfully" type messages
journalctl -u penora -n 50 | grep -i download
```

---

## Rollback (if needed)

If you need to revert to the previous version:

```bash
# Show commit history
git log --oneline -5

# Revert to previous commit
git revert HEAD

# Or hard reset
git reset --hard HEAD~1

# Push change
git push origin main

# Restart application
systemctl restart penora
```

---

## Next Steps

After successful deployment:

1. ✅ Test all download features
2. ✅ Monitor application logs for 24 hours
3. ✅ Verify users can successfully download content
4. ✅ Check error rates in monitoring
5. ✅ Document any issues encountered

---

## Support

If you encounter issues during deployment:

1. Check the troubleshooting section above
2. Review application logs: `journalctl -u penora -f`
3. Verify all files were updated: `git log --oneline -1`
4. Ensure dependencies are installed: `pip install -r requirements.txt`
5. Restart application: `systemctl restart penora`

