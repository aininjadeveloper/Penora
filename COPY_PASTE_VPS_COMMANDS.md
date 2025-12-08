# QUICK DEPLOYMENT STEPS - Copy & Paste Ready

## For Your Hostinger VPS

---

## Step 1: SSH into VPS
```bash
ssh root@82.25.105.23
```
**Note**: Enter your password when prompted

---

## Step 2: Navigate to Application
```bash
cd /var/www/penora
```

---

## Step 3: Pull Latest Code
```bash
git pull origin main
```

**Expected output:**
```
remote: Enumerating objects: 14, done.
Counting objects: 100% (14/14), done.
Delta compression (9/9), done.
Writing objects: 9 (delta 5), done.
Total 9 (delta 5)

Updating e075e8d..b34e634
Fast-forward
 routes.py                                    | 97 +++++++++++++++++++
 templates/view_project.html                  |  6 +-
 templates/text_editor.html                   |  6 +-
 DOWNLOAD_FIX_COMPLETE_REPORT.md              | new file
 DOWNLOAD_FIX_SUMMARY.md                      | new file
 DOWNLOAD_QUICK_REFERENCE.md                  | new file
 6 files changed, 705 insertions(+), 6 deletions(-)
```

---

## Step 4: Verify Files Updated
```bash
grep "def export_generation" routes.py
```

**Expected output:**
```
def export_generation(generation_id, format):
```

If this returns empty, the pull didn't work. Go back to Step 3.

---

## Step 5: Restart Application

**Choose ONE based on your setup:**

### Option A: SystemD Service (Most Common)
```bash
systemctl restart penora
```

### Option B: Supervisor
```bash
supervisorctl restart penora
```

### Option C: Check What's Running
```bash
ps aux | grep -i gunicorn
ps aux | grep -i supervisor
```

Then use appropriate restart command above.

---

## Step 6: Verify Application is Running
```bash
systemctl status penora
```

**Should show:**
```
● penora.service - Penora Application
   Loaded: loaded (/etc/systemd/system/penora.service; enabled)
   Active: active (running)
```

---

## Step 7: Test Application
```bash
curl http://localhost:5000/health
```

**Should return:**
```
OK
```

---

## Step 8: Check for Errors
```bash
journalctl -u penora -n 20
```

**Should NOT show:**
- `ERROR`
- `Exception`
- `ModuleNotFoundError`
- `SyntaxError`

---

## ✅ All Done!

Your VPS is now updated with the download fixes.

---

## 🧪 Final Test (In Browser)

1. Go to: `https://sukusuku.ai/penora` (or your domain)
2. Create a story or prompt
3. Click "Download"
4. Select "PDF"
5. File should download

**If this works, everything is good!**

---

## 🆘 Troubleshooting

### If Step 3 (git pull) fails:
```bash
# Check git status
git status

# If dirty, reset it
git reset --hard HEAD

# Then try pull again
git pull origin main
```

### If Step 5 (restart) fails:
```bash
# Find the process
ps aux | grep gunicorn

# Kill it (replace XXXX with PID)
kill -9 XXXX

# Start fresh
systemctl start penora
```

### If Step 6 (status) shows inactive:
```bash
# Check what went wrong
journalctl -u penora -n 50

# Check logs
tail -f /var/log/supervisor/penora.log
```

### If downloads still don't work:
```bash
# Verify route exists
grep -n "export_generation" routes.py

# Should show line number around 1618
```

---

## 📋 Quick Checklist

- [ ] SSH successful
- [ ] In /var/www/penora directory
- [ ] `git pull origin main` completed
- [ ] `grep "def export_generation"` returns a line number
- [ ] `systemctl restart penora` successful
- [ ] `systemctl status penora` shows "active (running)"
- [ ] `curl http://localhost:5000/health` returns OK
- [ ] No errors in `journalctl -u penora -n 20`
- [ ] Downloaded a file successfully from web browser

---

## 📞 If You're Stuck

Save this file and send the output of these commands:

```bash
# Copy all these and run them
echo "=== Git Status ===" && git status
echo "=== Route Check ===" && grep "def export_generation" routes.py
echo "=== Service Status ===" && systemctl status penora
echo "=== Recent Logs ===" && journalctl -u penora -n 20
echo "=== Health Check ===" && curl http://localhost:5000/health
```

Send me the output and I'll help troubleshoot.

