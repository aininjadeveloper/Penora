#!/bin/bash
# Fix Download Not Working on VPS - Run this script

echo "=========================================="
echo "🔧 FIXING DOWNLOADS ON VPS"
echo "=========================================="
echo ""

cd /var/www/penora

echo "Step 1: Checking current git status..."
git status
echo ""

echo "Step 2: Fetching latest changes..."
git fetch origin main
echo ""

echo "Step 3: Resetting to latest version..."
git reset --hard origin/main
echo ""

echo "Step 4: Verifying templates have download fix..."
if grep -q "triggerDownload" templates/workspace.html; then
    echo "✅ workspace.html has download fix"
else
    echo "❌ workspace.html MISSING download fix"
fi

if grep -q "triggerDownload" templates/view_project.html; then
    echo "✅ view_project.html has download fix"
else
    echo "❌ view_project.html MISSING download fix"
fi

if grep -q "triggerDownload" templates/text_editor.html; then
    echo "✅ text_editor.html has download fix"
else
    echo "❌ text_editor.html MISSING download fix"
fi

echo ""
echo "Step 5: Restarting application..."
systemctl restart penora
sleep 2

echo "Step 6: Checking if app is running..."
if systemctl is-active --quiet penora; then
    echo "✅ Application is running"
else
    echo "❌ Application failed to start"
    echo "Checking logs..."
    journalctl -u penora -n 20
    exit 1
fi

echo ""
echo "=========================================="
echo "✅ DOWNLOAD FIX COMPLETE!"
echo "=========================================="
echo ""
echo "Test it:"
echo "1. Go to https://sukusuku.ai/penora"
echo "2. Go to My Workspace"
echo "3. Click Download → PDF"
echo "4. File should download now!"
echo ""
echo "If still not working, run:"
echo "  tail -f /var/log/supervisor/penora.log"
echo "  OR"
echo "  journalctl -u penora -f"
echo ""
