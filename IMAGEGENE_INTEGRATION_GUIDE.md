# ImageGene Integration with Unified Penora Credit System

## Overview
This integration allows ImageGene and Penora to share a unified credit system and workspace, giving users seamless access to their content across both applications with a shared 1MB storage limit.

## Unified System Features

### 1. Shared Credits
- **Single Credit Pool**: Users have one credit balance that works across both Penora and ImageGene
- **Real-time Sync**: Credits deducted in one app are immediately reflected in the other
- **Transaction History**: Complete transaction log showing usage across both apps
- **Unified Pricing**: Same credit cost structure for both applications

### 2. Shared Workspace (1MB Total)
- **Combined Storage**: 1MB storage limit shared between both apps
- **Cross-App Access**: Projects created in Penora can be accessed in ImageGene and vice versa
- **Unified Project Codes**: 6-character codes work across both platforms
- **Merged Project Display**: See all projects from both apps in one interface

### 3. User Isolation
- **Per-User Storage**: Each user has their own isolated 1MB workspace
- **Secure Access**: Users can only access their own projects and credits
- **Cross-App Authentication**: SSO works seamlessly between applications

## API Endpoints for ImageGene

### Base URL
```
https://e1e07499-d292-4451-b55b-9647412a4052-00-3cl7v3i6gfvjy.spock.replit.dev
```

### 1. Get User Info (Credits + Storage)
```
GET /api/unified/user-info?user_id={user_id}
```

**Response:**
```json
{
  "success": true,
  "user_id": "101902121794505144784",
  "credits": 43,
  "storage": {
    "used_mb": 0.15,
    "limit_mb": 1.0,
    "available_mb": 0.85,
    "usage_percentage": 15.0
  },
  "timestamp": "2025-08-20T07:25:00.000000"
}
```

### 2. Get All Projects (Both Apps)
```
GET /api/unified/projects?user_id={user_id}&app={app_filter}
```

**Parameters:**
- `user_id`: Required user identifier
- `app`: Optional filter ('penora', 'imagegene', or omit for all)

**Response:**
```json
{
  "success": true,
  "all_projects": [...],
  "penora_projects": [...],
  "imagegene_projects": [...],
  "total_count": 8,
  "penora_count": 4,
  "imagegene_count": 4,
  "storage_stats": {
    "used_mb": 0.15,
    "limit_mb": 1.0,
    "available_mb": 0.85
  }
}
```

### 3. Save Project to Unified Workspace
```
POST /api/unified/save-project
Content-Type: application/json
```

**Request Body:**
```json
{
  "user_id": "101902121794505144784",
  "app_source": "imagegene",
  "project_type": "ai_art",
  "title": "Generated Landscape Art",
  "content": "base64_image_data_or_text_content",
  "metadata": {
    "style": "photorealistic",
    "dimensions": "1024x1024",
    "model": "dalle-3",
    "prompt": "Beautiful mountain landscape at sunset"
  }
}
```

**Response:**
```json
{
  "success": true,
  "project_code": "IMG123",
  "title": "Generated Landscape Art",
  "size_mb": 0.05,
  "app_source": "imagegene"
}
```

### 4. Deduct Credits (For ImageGene Usage)
```
POST /api/unified/deduct-credits
Content-Type: application/json
```

**Request Body:**
```json
{
  "user_id": "101902121794505144784",
  "amount": 2,
  "app_name": "imagegene",
  "description": "AI Art Generation - Landscape Style",
  "project_code": "IMG123"
}
```

**Response:**
```json
{
  "success": true,
  "credits_deducted": 2,
  "new_balance": 41,
  "app_name": "imagegene"
}
```

### 5. Get Transaction History
```
GET /api/unified/transactions?user_id={user_id}&limit=50
```

**Response:**
```json
{
  "success": true,
  "all_transactions": [...],
  "penora_transactions": [...],
  "imagegene_transactions": [...],
  "total_count": 15
}
```

### 6. Get Storage Statistics
```
GET /api/unified/storage-stats?user_id={user_id}
```

**Response:**
```json
{
  "success": true,
  "storage_stats": {
    "used_mb": 0.15,
    "limit_mb": 1.0,
    "available_mb": 0.85,
    "usage_percentage": 15.0
  },
  "breakdown": {
    "penora_mb": 0.10,
    "imagegene_mb": 0.05,
    "total_projects": 8,
    "penora_projects": 4,
    "imagegene_projects": 4
  }
}
```

## Implementation Example for ImageGene

### 1. Initialize User on ImageGene Login
```python
import requests

def initialize_user_in_unified_system(user_id, username, email):
    """Initialize user in unified credit system"""
    response = requests.post(
        "https://penora.replit.dev/api/unified/create-user",
        json={
            "user_id": user_id,
            "username": username,
            "email": email,
            "initial_credits": 50
        }
    )
    return response.json()
```

### 2. Check Credits Before AI Generation
```python
def check_user_credits(user_id):
    """Check if user has enough credits for generation"""
    response = requests.get(
        f"https://penora.replit.dev/api/unified/user-info?user_id={user_id}"
    )
    data = response.json()
    return data.get('credits', 0) if data.get('success') else 0
```

### 3. Generate AI Art with Credit Deduction
```python
def generate_ai_art_with_credits(user_id, prompt, style="photorealistic"):
    """Generate AI art and deduct credits"""
    
    # Check credits first
    credits = check_user_credits(user_id)
    if credits < 2:  # Assuming 2 credits per generation
        return {"error": "Insufficient credits"}
    
    # Generate the art (your existing AI generation code)
    art_result = your_ai_generation_function(prompt, style)
    
    if art_result['success']:
        # Save to unified workspace
        save_response = requests.post(
            "https://penora.replit.dev/api/unified/save-project",
            json={
                "user_id": user_id,
                "app_source": "imagegene",
                "project_type": "ai_art",
                "title": f"AI Art - {prompt[:30]}",
                "content": art_result['image_data'],
                "metadata": {
                    "style": style,
                    "prompt": prompt,
                    "model": "dalle-3"
                }
            }
        )
        
        # Deduct credits
        credit_response = requests.post(
            "https://penora.replit.dev/api/unified/deduct-credits",
            json={
                "user_id": user_id,
                "amount": 2,
                "app_name": "imagegene",
                "description": f"AI Art Generation - {style}",
                "project_code": save_response.json().get('project_code')
            }
        )
        
        return {
            "success": True,
            "image": art_result['image_data'],
            "project_code": save_response.json().get('project_code'),
            "credits_remaining": credit_response.json().get('new_balance')
        }
    
    return {"error": "Generation failed"}
```

### 4. Display Unified Projects in ImageGene
```python
def get_user_projects_for_dropdown(user_id):
    """Get all user projects for dropdown selection"""
    response = requests.get(
        f"https://penora.replit.dev/api/unified/projects?user_id={user_id}"
    )
    
    if response.json().get('success'):
        projects = response.json()['all_projects']
        
        # Format for dropdown
        dropdown_options = []
        for project in projects:
            dropdown_options.append({
                "value": project['code'],
                "label": f"[{project['app_source'].upper()}] {project['title']}",
                "type": project['project_type'],
                "size": f"{project['size_mb']}MB"
            })
        
        return dropdown_options
    
    return []
```

### 5. Display Storage Usage
```python
def get_storage_display_info(user_id):
    """Get storage info for UI display"""
    response = requests.get(
        f"https://penora.replit.dev/api/unified/storage-stats?user_id={user_id}"
    )
    
    if response.json().get('success'):
        data = response.json()
        return {
            "used": data['storage_stats']['used_mb'],
            "total": data['storage_stats']['limit_mb'],
            "percentage": data['storage_stats']['usage_percentage'],
            "penora_usage": data['breakdown']['penora_mb'],
            "imagegene_usage": data['breakdown']['imagegene_mb']
        }
    
    return {"used": 0, "total": 1, "percentage": 0}
```

## Credit Cost Structure

### Penora Costs
- Single page generation: 1 credit
- Multi-page generation: 1 credit per page
- File processing: 1 credit per page detected

### ImageGene Costs (Suggested)
- Basic AI art generation: 2 credits
- Advanced AI art generation: 3 credits
- Image enhancement: 1 credit
- Style transfer: 2 credits

## Storage Management

### File Size Limits
- Total workspace: 1MB across both apps
- Individual projects: No specific limit (constrained by total)
- Automatic compression: Recommended for image content

### Storage Optimization Tips
1. Compress images before storing
2. Use efficient text encoding
3. Remove old projects when storage is full
4. Implement project cleanup features

## Error Handling

### Common Error Responses
```json
{
  "success": false,
  "error": "Insufficient credits",
  "details": "User has 1 credit but needs 2"
}

{
  "success": false,
  "error": "Storage limit exceeded",
  "details": "Adding 0.5MB would exceed 1MB limit"
}
```

### Recommended Error Handling
1. Check credits before expensive operations
2. Show storage usage in UI
3. Provide clear error messages to users
4. Offer upgrade options when limits are reached

## Testing Commands

### Test User Creation
```bash
curl -X POST "https://penora.replit.dev/api/unified/create-user" \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test123","username":"Test User","email":"test@example.com"}'
```

### Test Credit Deduction
```bash
curl -X POST "https://penora.replit.dev/api/unified/deduct-credits" \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test123","amount":2,"app_name":"imagegene","description":"Test generation"}'
```

### Test Project Saving
```bash
curl -X POST "https://penora.replit.dev/api/unified/save-project" \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test123","app_source":"imagegene","project_type":"ai_art","title":"Test Project","content":"test content"}'
```

This unified system ensures seamless integration between Penora and ImageGene while maintaining strict user isolation and efficient resource management.