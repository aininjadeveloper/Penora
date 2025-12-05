# Hostinger VPS Deployment Guide for Penora

This guide outlines the steps to deploy and troubleshoot the Penora application on your Hostinger VPS.

## Prerequisites

- **SSH Access**: You need `root` access to your VPS.
- **Codebase**: Ensure your local code is pushed to GitHub.
- **Dependencies**: The `requirements.txt` file must be present (we just created this).

## Deployment Steps

1.  **SSH into your VPS**:
    ```bash
    ssh root@82.25.105.23
    ```

2.  **Navigate to the project directory**:
    ```bash
    cd /var/www/penora/Penora
    ```

3.  **Pull the latest code**:
    ```bash
    git pull origin main
    ```
    *(Enter your GitHub credentials if prompted)*

4.  **Update Dependencies**:
    ```bash
    source ../venv/bin/activate
    pip install -r requirements.txt
    ```

5.  **Restart the Service**:
    ```bash
    systemctl restart penora
    ```

6.  **Verify Status**:
    ```bash
    systemctl status penora
    ```

## Troubleshooting

If the service fails to start, run the following commands to diagnose the issue:

### 1. Check Service Logs
```bash
journalctl -u penora -n 50 --no-pager
```
Look for python errors, import errors, or "ModuleNotFoundError".

### 2. Check Gunicorn Configuration
Ensure the service file points to the correct application object.
```bash
cat /etc/systemd/system/penora.service
```
It should look something like:
`ExecStart=/var/www/penora/venv/bin/gunicorn --workers 3 --bind 127.0.0.1:5100 main:app`
*Note: We use `main:app` because `main.py` registers the unified APIs.*

### 3. Manual Run (Debug Mode)
Try running Gunicorn manually to see errors directly:
```bash
source ../venv/bin/activate
gunicorn --bind 0.0.0.0:5100 main:app
```
If this works, the issue is likely in the systemd service file.

### 4. Common Issues
- **Missing `requirements.txt`**: We just generated this file. Make sure to push it to GitHub and pull it on the VPS.
- **Database Path**: Ensure the database path in `.env` is correct and writable.
- **Port Conflict**: Ensure port 5100 is free.
