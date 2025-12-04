# ImageGene Unified API Integration - Complete Setup

## Overview
This document provides the complete API integration for ImageGene to work with the unified credit system. All endpoints require the PENORA_API_KEY for authentication.

## API Base URL
```
https://e1e07499-d292-4451-b55b-9647412a4052-00-3cl7v3i6gfvjy.spock.replit.dev
```

## Required Headers
```javascript
const headers = {
    'X-API-Key': 'Pl2UbWIUMgFNQ-iUtQZSozcSUTd1cyNtsNDMhw87bTRST2fN15qT8DP0MG8ZihhZLDcX14xZlikbuwqlIQZ-og',
    'Content-Type': 'application/json'
};
```

## Essential API Endpoints

### 1. Check User Credits
```javascript
GET /api/unified/user-info?user_id={user_id}

Response:
{
    "success": true,
    "credits": 55,
    "user_id": "101902121794505144784",
    "storage": {
        "used_mb": 0.0,
        "limit_mb": 1.0,
        "available_mb": 1.0,
        "usage_percentage": 0.0
    },
    "timestamp": "2025-08-28T07:26:03.764370"
}
```

### 2. Deduct Credits for Image Generation
```javascript
POST /api/unified/deduct-credits
Content-Type: application/json

{
    "user_id": "101902121794505144784",
    "amount": 3,
    "app_name": "imagegene",
    "description": "AI image generation",
    "project_code": "IMG_001"
}

Response:
{
    "success": true,
    "credits_deducted": 3,
    "new_balance": 52,
    "app_name": "imagegene",
    "timestamp": "2025-08-28T07:23:01.032080"
}
```

### 3. Add Credits (for admin/purchase integration)
```javascript
POST /api/unified/add-credits
Content-Type: application/json

{
    "user_id": "101902121794505144784",
    "amount": 10,
    "transaction_type": "purchased",
    "description": "Credit purchase via ImageGene"
}

Response:
{
    "success": true,
    "credits_added": 10,
    "new_balance": 62,
    "timestamp": "2025-08-28T07:26:15.123456"
}
```

### 4. Get User Projects (Cross-App Workspace)
```javascript
GET /api/unified/user-projects?user_id={user_id}&app_filter=penora

Response:
{
    "success": true,
    "projects": [
        {
            "code": "JHSHDU",
            "title": "1 Page(s) - test generation",
            "content": "Generated content...",
            "app_source": "penora",
            "project_type": "text",
            "created_at": "2025-08-28T06:45:12.000000",
            "file_size_mb": 0.01
        }
    ],
    "total_projects": 1,
    "user_id": "101902121794505144784"
}
```

### 5. Save ImageGene Project to Unified Workspace
```javascript
POST /api/unified/save-project
Content-Type: application/json

{
    "user_id": "101902121794505144784",
    "app_source": "imagegene",
    "project_type": "ai_image",
    "title": "Generated AI Art",
    "content": "base64_image_data_or_url",
    "metadata": {
        "prompt": "beautiful landscape",
        "model": "stable-diffusion",
        "dimensions": "1024x1024"
    }
}

Response:
{
    "success": true,
    "project_code": "IMG_ABC123",
    "title": "Generated AI Art",
    "size_mb": 0.5,
    "storage_remaining_mb": 0.5
}
```

## Complete JavaScript Integration for ImageGene

```javascript
class PenoraAPI {
    constructor() {
        this.baseURL = 'https://e1e07499-d292-4451-b55b-9647412a4052-00-3cl7v3i6gfvjy.spock.replit.dev';
        this.apiKey = 'Pl2UbWIUMgFNQ-iUtQZSozcSUTd1cyNtsNDMhw87bTRST2fN15qT8DP0MG8ZihhZLDcX14xZlikbuwqlIQZ-og';
        this.headers = {
            'X-API-Key': this.apiKey,
            'Content-Type': 'application/json'
        };
    }

    async getUserCredits(userId) {
        try {
            const response = await fetch(`${this.baseURL}/api/unified/user-info?user_id=${userId}`, {
                method: 'GET',
                headers: this.headers
            });
            const data = await response.json();
            return data.success ? data.credits : 0;
        } catch (error) {
            console.error('Error getting user credits:', error);
            return 0;
        }
    }

    async deductCredits(userId, amount, description = 'AI image generation') {
        try {
            const response = await fetch(`${this.baseURL}/api/unified/deduct-credits`, {
                method: 'POST',
                headers: this.headers,
                body: JSON.stringify({
                    user_id: userId,
                    amount: amount,
                    app_name: 'imagegene',
                    description: description,
                    project_code: `IMG_${Date.now()}`
                })
            });
            const data = await response.json();
            return data.success ? data.new_balance : false;
        } catch (error) {
            console.error('Error deducting credits:', error);
            return false;
        }
    }

    async saveProject(userId, title, imageData, metadata = {}) {
        try {
            const response = await fetch(`${this.baseURL}/api/unified/save-project`, {
                method: 'POST',
                headers: this.headers,
                body: JSON.stringify({
                    user_id: userId,
                    app_source: 'imagegene',
                    project_type: 'ai_image',
                    title: title,
                    content: imageData,
                    metadata: metadata
                })
            });
            return await response.json();
        } catch (error) {
            console.error('Error saving project:', error);
            return { success: false, error: error.message };
        }
    }

    async getUserProjects(userId, appFilter = null) {
        try {
            let url = `${this.baseURL}/api/unified/user-projects?user_id=${userId}`;
            if (appFilter) url += `&app_filter=${appFilter}`;
            
            const response = await fetch(url, {
                method: 'GET',
                headers: this.headers
            });
            return await response.json();
        } catch (error) {
            console.error('Error getting user projects:', error);
            return { success: false, projects: [] };
        }
    }
}

// Usage Example for ImageGene
const penoraAPI = new PenoraAPI();

// Check credits before generation
async function checkUserCredits(userId) {
    const credits = await penoraAPI.getUserCredits(userId);
    console.log(`User has ${credits} credits`);
    return credits;
}

// Deduct credits after successful image generation
async function processImageGeneration(userId, imageCost = 3) {
    const credits = await checkUserCredits(userId);
    
    if (credits >= imageCost) {
        // Generate image here...
        const newBalance = await penoraAPI.deductCredits(userId, imageCost);
        if (newBalance !== false) {
            console.log(`Credits deducted. New balance: ${newBalance}`);
            return newBalance;
        }
    } else {
        console.log('Insufficient credits');
        return false;
    }
}

// Save generated image to workspace
async function saveGeneratedImage(userId, title, imageData, prompt) {
    const result = await penoraAPI.saveProject(userId, title, imageData, {
        prompt: prompt,
        model: 'stable-diffusion',
        app_version: 'imagegene-v1.0'
    });
    
    if (result.success) {
        console.log(`Image saved with code: ${result.project_code}`);
    }
    return result;
}
```

## Real-Time Credit Display Integration

Add this to your ImageGene UI to show live credit balance:

```javascript
// Credit display update function
async function updateCreditDisplay(userId) {
    const credits = await penoraAPI.getUserCredits(userId);
    const creditElement = document.getElementById('credit-balance');
    if (creditElement) {
        creditElement.textContent = `${credits} KU Coins`;
    }
    return credits;
}

// Call this every 30 seconds or after any credit operation
setInterval(() => {
    if (currentUserId) {
        updateCreditDisplay(currentUserId);
    }
}, 30000);
```

## Error Handling

```javascript
async function safeAPICall(apiFunction, ...args) {
    try {
        return await apiFunction(...args);
    } catch (error) {
        console.error('API Error:', error);
        // Show user-friendly error message
        showNotification('Unable to connect to credit system. Please try again.', 'error');
        return null;
    }
}
```

## Environment Variables (for ImageGene)

Add these to your ImageGene environment:

```bash
PENORA_API_BASE_URL=https://e1e07499-d292-4451-b55b-9647412a4052-00-3cl7v3i6gfvjy.spock.replit.dev
PENORA_API_KEY=Pl2UbWIUMgFNQ-iUtQZSozcSUTd1cyNtsNDMhw87bTRST2fN15qT8DP0MG8ZihhZLDcX14xZlikbuwqlIQZ-og
```

## Testing the Integration

Use these curl commands to test:

```bash
# Check user credits
curl -X GET "https://e1e07499-d292-4451-b55b-9647412a4052-00-3cl7v3i6gfvjy.spock.replit.dev/api/unified/user-info?user_id=101902121794505144784" \
     -H "X-API-Key: Pl2UbWIUMgFNQ-iUtQZSozcSUTd1cyNtsNDMhw87bTRST2fN15qT8DP0MG8ZihhZLDcX14xZlikbuwqlIQZ-og"

# Deduct credits
curl -X POST "https://e1e07499-d292-4451-b55b-9647412a4052-00-3cl7v3i6gfvjy.spock.replit.dev/api/unified/deduct-credits" \
     -H "X-API-Key: Pl2UbWIUMgFNQ-iUtQZSozcSUTd1cyNtsNDMhw87bTRST2fN15qT8DP0MG8ZihhZLDcX14xZlikbuwqlIQZ-og" \
     -H "Content-Type: application/json" \
     -d '{"user_id": "101902121794505144784", "amount": 3, "app_name": "imagegene", "description": "Test image generation"}'
```

This integration provides complete credit synchronization between Penora and ImageGene, ensuring both apps show the same credit balance and can deduct credits in real-time.