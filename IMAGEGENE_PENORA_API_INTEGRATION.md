# ImageGene + Penora Unified Credit System Integration Guide

## Overview
This guide shows how ImageGene can integrate with Penora's unified credit system using the secure PENORA_API_KEY for real-time credit synchronization.

## API Authentication
All API requests require authentication using the PENORA_API_KEY:

```bash
# Method 1: HTTP Header (Recommended)
X-API-Key: YOUR_PENORA_API_KEY

# Method 2: URL Parameter (Alternative)
?api_key=YOUR_PENORA_API_KEY
```

## Base URLs
- **Production**: `https://your-penora-domain.replit.app`
- **Development**: `http://localhost:5000`

## Core API Endpoints

### 1. Check User Credits
Get user's current Ku coin balance and storage information.

```bash
GET /api/unified/user-info?user_id=USER_ID
Headers: X-API-Key: YOUR_PENORA_API_KEY
```

**Response:**
```json
{
  "success": true,
  "user_id": "101902121794505144784",
  "credits": 50,
  "storage": {
    "used_mb": 0.85,
    "remaining_mb": 0.15,
    "total_mb": 1.0,
    "usage_percentage": 85,
    "total_projects": 4
  },
  "timestamp": "2025-08-28T06:00:00.000Z"
}
```

### 2. Deduct Credits (Image Generation)
Deduct credits when user generates images in ImageGene.

```bash
POST /api/unified/deduct-credits
Headers: X-API-Key: YOUR_PENORA_API_KEY
Content-Type: application/json
```

**Request Body:**
```json
{
  "user_id": "101902121794505144784",
  "amount": 5,
  "app_name": "imagegene",
  "description": "AI image generation - 1024x1024 artwork",
  "project_code": "img_xyz123"
}
```

**Response:**
```json
{
  "success": true,
  "credits_deducted": 5,
  "new_balance": 45,
  "app_name": "imagegene",
  "timestamp": "2025-08-28T06:00:00.000Z"
}
```

### 3. Save Generated Images to Unified Workspace
Save ImageGene projects to shared workspace.

```bash
POST /api/unified/save-project
Headers: X-API-Key: YOUR_PENORA_API_KEY
Content-Type: application/json
```

**Request Body:**
```json
{
  "user_id": "101902121794505144784",
  "app_source": "imagegene",
  "project_type": "ai_artwork",
  "title": "Sunset Landscape AI Art",
  "content": "base64_encoded_image_data_or_url",
  "metadata": {
    "style": "realistic",
    "dimensions": "1024x1024",
    "model": "stable_diffusion_xl",
    "prompt": "Beautiful sunset over mountains"
  }
}
```

### 4. Get User's Projects (Cross-App View)
Display user's projects from both Penora and ImageGene.

```bash
GET /api/unified/projects?user_id=USER_ID&app=imagegene
Headers: X-API-Key: YOUR_PENORA_API_KEY
```

**Response includes projects from both apps:**
```json
{
  "success": true,
  "all_projects": [...],
  "penora_projects": [...],
  "imagegene_projects": [...],
  "total_count": 8,
  "penora_count": 4,
  "imagegene_count": 4
}
```

## ImageGene Integration Implementation

### Step 1: Before Image Generation
```javascript
// Check if user has enough credits
async function checkUserCredits(userId) {
  const response = await fetch(`/api/unified/user-info?user_id=${userId}`, {
    headers: {
      'X-API-Key': process.env.PENORA_API_KEY
    }
  });
  
  const data = await response.json();
  if (data.success) {
    return data.credits;
  }
  throw new Error('Failed to check credits');
}

// Example usage
const userId = getCurrentUserId();
const credits = await checkUserCredits(userId);
if (credits < 5) {
  showError('Insufficient credits. Please purchase more Ku coins.');
  return;
}
```

### Step 2: During Image Generation
```javascript
// Deduct credits when starting generation
async function deductCreditsForImage(userId, creditCost, projectCode) {
  const response = await fetch('/api/unified/deduct-credits', {
    method: 'POST',
    headers: {
      'X-API-Key': process.env.PENORA_API_KEY,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      user_id: userId,
      amount: creditCost,
      app_name: 'imagegene',
      description: `Image generation - ${getCurrentImageSettings()}`,
      project_code: projectCode
    })
  });
  
  const result = await response.json();
  if (result.success) {
    updateUICredits(result.new_balance);
    return result.new_balance;
  }
  throw new Error('Credit deduction failed');
}
```

### Step 3: After Successful Generation
```javascript
// Save generated image to unified workspace
async function saveImageToWorkspace(userId, imageData, metadata) {
  const response = await fetch('/api/unified/save-project', {
    method: 'POST',
    headers: {
      'X-API-Key': process.env.PENORA_API_KEY,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      user_id: userId,
      app_source: 'imagegene',
      project_type: 'ai_artwork',
      title: metadata.title || `AI Artwork ${Date.now()}`,
      content: imageData, // base64 or URL
      metadata: {
        style: metadata.style,
        dimensions: metadata.dimensions,
        model: metadata.model,
        prompt: metadata.prompt,
        generation_time: metadata.generationTime
      }
    })
  });
  
  return await response.json();
}
```

## Complete Integration Flow

```javascript
// Complete ImageGene generation with Penora integration
async function generateImageWithPenoraSync(userId, prompt, settings) {
  try {
    // 1. Check credits
    const currentCredits = await checkUserCredits(userId);
    const requiredCredits = calculateCreditCost(settings);
    
    if (currentCredits < requiredCredits) {
      throw new Error('Insufficient credits');
    }
    
    // 2. Generate unique project code
    const projectCode = `img_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    
    // 3. Deduct credits before generation
    const newBalance = await deductCreditsForImage(userId, requiredCredits, projectCode);
    
    // 4. Generate image (your existing logic)
    const imageData = await generateImageWithAI(prompt, settings);
    
    // 5. Save to unified workspace
    await saveImageToWorkspace(userId, imageData, {
      title: `AI Art: ${prompt.substring(0, 50)}...`,
      style: settings.style,
      dimensions: `${settings.width}x${settings.height}`,
      model: settings.model,
      prompt: prompt,
      generationTime: new Date().toISOString()
    });
    
    // 6. Update UI
    updateUICredits(newBalance);
    showSuccess(`Image generated! ${newBalance} credits remaining.`);
    
    return {
      success: true,
      imageData,
      projectCode,
      creditsRemaining: newBalance
    };
    
  } catch (error) {
    console.error('Generation failed:', error);
    
    // Optionally refund credits on failure
    // await refundCredits(userId, requiredCredits, projectCode);
    
    throw error;
  }
}
```

## Error Handling

### Common Error Responses
```json
// Missing/Invalid API Key
{
  "success": false,
  "error": "Invalid or missing API key. Include X-API-Key header or api_key parameter."
}

// Insufficient Credits
{
  "success": false,
  "error": "Insufficient credits or deduction failed"
}

// User Not Found
{
  "success": false,
  "error": "User ID required"
}
```

### Recommended Error Handling
```javascript
async function handleAPICall(apiFunction) {
  try {
    return await apiFunction();
  } catch (error) {
    if (error.message.includes('API key')) {
      console.error('Penora API authentication failed');
      showError('Connection to credit system failed. Please try again.');
    } else if (error.message.includes('Insufficient')) {
      showError('Not enough Ku coins. Please purchase more credits.');
      redirectToPricing();
    } else {
      console.error('Penora API error:', error);
      showError('Credit system temporarily unavailable. Please try again.');
    }
    throw error;
  }
}
```

## Credit Cost Guidelines

### Recommended Credit Costs for ImageGene:
- **512x512 image**: 2 credits
- **1024x1024 image**: 5 credits  
- **High-quality/upscaled**: 8 credits
- **Multiple variations**: +2 credits per additional image

### Storage Considerations:
- All users have 1MB shared storage limit
- Large images should be compressed or stored externally
- Consider implementing automatic cleanup of old projects

## Security Best Practices

1. **Never expose API key in frontend code**
2. **Use environment variables for PENORA_API_KEY**
3. **Validate user permissions before API calls**
4. **Implement rate limiting to prevent abuse**
5. **Log all credit transactions for audit trails**

## Testing the Integration

Use the provided endpoints to test:

```bash
# Test credit check
curl -X GET "https://your-penora-app.replit.app/api/unified/user-info?user_id=TEST_USER_ID" \
     -H "X-API-Key: YOUR_PENORA_API_KEY"

# Test credit deduction
curl -X POST "https://your-penora-app.replit.app/api/unified/deduct-credits" \
     -H "X-API-Key: YOUR_PENORA_API_KEY" \
     -H "Content-Type: application/json" \
     -d '{"user_id":"TEST_USER_ID","amount":2,"app_name":"imagegene","description":"Test deduction"}'
```

## Support and Troubleshooting

- **API Documentation**: Available at `/api/unified/docs` (if implemented)
- **Health Check**: `GET /health` for system status
- **Logs**: Check server logs for detailed error information
- **Contact**: For integration support, contact the Penora development team

---

**Note**: This integration enables real-time credit synchronization between ImageGene and Penora, providing users with a seamless experience across both platforms.