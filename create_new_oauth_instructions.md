# Fix for "OAuth client was deleted" Error

## The Problem
Google is returning "Error 401: deleted_client" which means the OAuth client either:
1. Was accidentally deleted from Google Console
2. Is disabled/inactive
3. Has configuration issues

## Solution: Create Fresh OAuth Client

### Step 1: Go to Google Cloud Console
Visit: https://console.cloud.google.com/apis/credentials

### Step 2: Create New OAuth 2.0 Client
1. Click "Create Credentials" → "OAuth 2.0 Client ID"
2. Application type: "Web application"
3. Name: "Penora Google Login"

### Step 3: Add Redirect URI
Add this EXACT redirect URI:
```
https://e1e07499-d292-4451-b55b-9647412a4052-00-3cl7v3i6gfvjy.spock.replit.dev/working_google_login/callback
```

### Step 4: Copy New Credentials
After creating, copy:
- Client ID
- Client Secret

### Step 5: Update Replit Secrets
Replace the existing secrets with new values:
- `GOOGLE_OAUTH_CLIENT_ID` = new client ID  
- `GOOGLE_OAUTH_CLIENT_SECRET` = new client secret

### Step 6: Test
The Google login should work immediately after updating the secrets.

## Alternative: Check Existing Client
If you prefer to fix the existing client:
1. Go to Google Console credentials page
2. Find your OAuth client: `814950413158-ug0h11ft0j7lqkrbd93n2dac06jsrlsu.apps.googleusercontent.com`
3. Ensure it's not deleted and is active
4. Verify the redirect URI is properly configured