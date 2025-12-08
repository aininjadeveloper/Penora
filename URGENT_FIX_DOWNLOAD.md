# ⚡ URGENT FIX - RUN THESE COMMANDS ON VPS RIGHT NOW

## Copy & Paste These Commands One By One

### Command 1: Connect to VPS
```bash
ssh root@82.25.105.23
```

### Command 2: Go to app folder
```bash
cd /var/www/penora
```

### Command 3: Force update from GitHub
```bash
git fetch origin main
git reset --hard origin/main
```

**What this does**: Downloads LATEST templates with the download fix

### Command 4: Verify templates updated
```bash
grep "triggerDownload" templates/workspace.html && echo "✅ FIXED" || echo "❌ NOT FIXED"
```

**Should output**: `✅ FIXED`

### Command 5: Restart app
```bash
systemctl restart penora
```

### Command 6: Check status
```bash
systemctl status penora
```

**Should show**: `active (running)`

---

## After Running Commands

### Test Download:
1. Go to https://sukusuku.ai/penora
2. Click "My Workspace"
3. Click "Download" button
4. Select "PDF"
5. **File should download now!** ✅

### If Still Not Working:

Check browser console (press F12):
- Look for `"Starting download from:"`
- Look for `"Blob received"`
- Look for error messages

If nothing appears in console, templates didn't update. Run this:
```bash
cd /var/www/penora
git log --oneline -3
# Should show: 18b98c3 Fix: Enable proper browser file downloads...
```

If you don't see that commit, the pull didn't work.

---

## CRITICAL: The Templates Must Update

The download function is now in the templates. If templates didn't update from GitHub, downloads won't work.

**Verify by checking file content:**
```bash
# Check if triggerDownload function exists
grep -n "triggerDownload" templates/workspace.html

# Should output something like:
# 305:    function triggerDownload(url, event) {
```

If it doesn't show, templates didn't update. Run git reset again:
```bash
cd /var/www/penora
git reset --hard HEAD
git pull origin main --force
systemctl restart penora
```

---

## Debug Commands If Needed

```bash
# See git history
git log --oneline -5

# Check if latest commit is there
git log | grep "Enable proper browser file downloads"

# Check file directly
cat templates/workspace.html | grep -A 5 "triggerDownload"

# Check app logs
journalctl -u penora -n 100 | grep -i download

# Force restart
systemctl stop penora
sleep 2
systemctl start penora
systemctl status penora
```

---

## The Fix (What Should Happen)

**OLD CODE (Broken):**
```javascript
window.location.href = url;  // ❌ Doesn't download
```

**NEW CODE (Fixed):**
```javascript
function triggerDownload(url, event) {
    event.preventDefault();
    fetch(url, {
        method: 'GET',
        credentials: 'include'
    })
    .then(response => response.blob())
    .then(blob => {
        const blobUrl = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = blobUrl;
        link.download = 'document';
        link.click();  // ✅ This triggers actual download
    });
}
```

If your templates still have the OLD code, downloads won't work.

---

## TL;DR - Just Run These 6 Commands:

```bash
ssh root@82.25.105.23
cd /var/www/penora
git fetch origin main
git reset --hard origin/main
systemctl restart penora
systemctl status penora
```

Then test download in browser.

**If that doesn't work, send me this output:**
```bash
git log --oneline -1
grep -n "triggerDownload" templates/workspace.html
journalctl -u penora -n 20
```

