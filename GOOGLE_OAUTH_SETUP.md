# Restore / Publish Google OAuth

If Google OAuth authentication is not working (showing 403 access denied or "unavailable" button), follow these steps:

## 1. Create New OAuth 2.0 Web Client

1. Go to [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
2. Click "Create Credentials" → "OAuth 2.0 Client ID"
3. Application type: "Web application"
4. Name: "Penora Google Login"

## 2. Set Authorized Origins + Redirect URIs

Add these **Authorized JavaScript origins**:
```
http://localhost:5000
https://e1e07499-d292-4451-b55b-9647412a4052-00-3cl7v3i6gfvjy.spock.replit.dev
https://your-deployment.replit.app
```

Add these **Authorized redirect URIs**:
```
http://localhost:5000/auth/google/callback
https://e1e07499-d292-4451-b55b-9647412a4052-00-3cl7v3i6gfvjy.spock.replit.dev/auth/google/callback
https://your-deployment.replit.app/auth/google/callback
```

## 3. Handle Testing vs Published App

**Option A: Add Test Users (for Testing mode)**
- Go to OAuth consent screen
- Under "Test users" section, click "Add users"
- Add the Gmail addresses that need access

**Option B: Publish App (for Production)**
- Go to OAuth consent screen  
- Click "Publish App" if domain is verified
- This allows any Gmail user to sign in

## 4. Update Environment Variables

Copy the new credentials and update:

**Replit Secrets:**
- `GOOGLE_OAUTH_CLIENT_ID` = your new client ID
- `GOOGLE_OAUTH_CLIENT_SECRET` = your new client secret

## 5. Test the Integration

After updating the secrets:
1. Restart the application
2. Click "Continue with Google" on login page
3. Should redirect to Google authentication
4. After authorization, should return to Penora and create/login user

## Troubleshooting

- **403 access denied**: Add your Gmail as a test user or publish the app
- **Button shows "unavailable"**: Check that OAuth credentials are properly set
- **Redirect URI mismatch**: Ensure callback URLs match exactly in Google Console