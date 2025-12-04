# 🚀 QUICK FIX: Make ImageGene Show Real Penora Credits

## Problem Identified
- **Penora**: Shows 50 credits ✅
- **ImageGene**: Shows 0 KU Coins ❌
- **Root Cause**: ImageGene not using PENORA_API_KEY to fetch real credit balance

## 🔧 IMMEDIATE SOLUTION

### Step 1: Add Environment Variable to ImageGene
Add this to your ImageGene environment variables:
```bash
PENORA_API_KEY=Pl2UbWIUMgFNQ-iUtQZSozcSUTd1cyNtsNDMhw87bTRST2fN15qT8DP0MG8ZihhZLDcX14xZlikbuwqlIQZ-og
PENORA_API_BASE=https://e1e07499-d292-4451-b55b-9647412a4052-00-3cl7v3i6gfvjy.spock.replit.dev
```

### Step 2: Replace ImageGene Credit Check Function
Replace your current credit fetching function with this:

```javascript
// REPLACE THIS IN IMAGEGENE
async function getUserCredits(userId) {
    try {
        const response = await fetch(`${process.env.PENORA_API_BASE}/api/unified/user-info?user_id=${userId}`, {
            headers: {
                'X-API-Key': process.env.PENORA_API_KEY,
                'Content-Type': 'application/json'
            }
        });
        
        const data = await response.json();
        
        if (data.success) {
            console.log(`✅ Real Penora credits: ${data.credits}`);
            return data.credits;
        } else {
            console.error('❌ Failed to get Penora credits:', data.error);
            return 0;
        }
    } catch (error) {
        console.error('❌ Error connecting to Penora:', error);
        return 0;
    }
}
```

### Step 3: Update Credit Display Function
```javascript
// REPLACE THIS IN IMAGEGENE
function updateCreditsDisplay(credits) {
    // Update all credit display elements
    const creditElements = document.querySelectorAll('[data-credits], .ku-coins, .credits-display');
    
    creditElements.forEach(element => {
        element.textContent = credits;
        element.setAttribute('data-credits', credits);
    });
    
    // Update specific ImageGene UI elements
    const accountInfo = document.querySelector('.account-info .credits');
    if (accountInfo) {
        accountInfo.textContent = `${credits} KU Coins`;
    }
    
    console.log(`✅ ImageGene UI updated: ${credits} KU coins`);
}
```

### Step 4: Initialize Real Credit Sync
Add this to your ImageGene initialization:

```javascript
// ADD THIS TO IMAGEGENE INITIALIZATION
async function initializeRealCredits() {
    const userId = getCurrentUserId(); // Your existing function
    
    if (userId) {
        console.log('🔗 Syncing with Penora credits...');
        
        const realCredits = await getUserCredits(userId);
        updateCreditsDisplay(realCredits);
        
        // Sync every 30 seconds
        setInterval(async () => {
            const credits = await getUserCredits(userId);
            updateCreditsDisplay(credits);
        }, 30000);
        
        console.log(`✅ Real-time Penora sync active: ${realCredits} credits`);
    }
}

// Call on page load
document.addEventListener('DOMContentLoaded', initializeRealCredits);
```

### Step 5: Update Image Generation Function
```javascript
// REPLACE YOUR IMAGE GENERATION FUNCTION
async function generateImageWithCredits(prompt, settings) {
    const userId = getCurrentUserId();
    const creditCost = 5; // Adjust based on your pricing
    
    try {
        // Check current credits
        const currentCredits = await getUserCredits(userId);
        if (currentCredits < creditCost) {
            throw new Error(`Insufficient credits. You have ${currentCredits}, need ${creditCost}`);
        }
        
        // Deduct credits in Penora
        const deductResponse = await fetch(`${process.env.PENORA_API_BASE}/api/unified/deduct-credits`, {
            method: 'POST',
            headers: {
                'X-API-Key': process.env.PENORA_API_KEY,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                user_id: userId,
                amount: creditCost,
                app_name: 'imagegene',
                description: `Image: ${prompt}`
            })
        });
        
        const deductData = await deductResponse.json();
        if (!deductData.success) {
            throw new Error('Credit deduction failed');
        }
        
        // Generate image (your existing logic)
        const imageResult = await generateImage(prompt, settings);
        
        // Update UI with new balance
        updateCreditsDisplay(deductData.new_balance);
        
        console.log(`✅ Image generated! Credits remaining: ${deductData.new_balance}`);
        
        return imageResult;
        
    } catch (error) {
        console.error('❌ Generation failed:', error);
        alert(error.message);
        throw error;
    }
}
```

## 🧪 Test the Fix

### Test 1: Check Credit Sync
```javascript
// Run this in ImageGene console
getUserCredits('103603059097313725207').then(credits => {
    console.log('Real Penora credits:', credits);
});
```

### Test 2: Verify API Connection
```bash
# Test from ImageGene server
curl -X GET "https://e1e07499-d292-4451-b55b-9647412a4052-00-3cl7v3i6gfvjy.spock.replit.dev/api/unified/user-info?user_id=103603059097313725207" \
     -H "X-API-Key: Pl2UbWIUMgFNQ-iUtQZSozcSUTd1cyNtsNDMhw87bTRST2fN15qT8DP0MG8ZihhZLDcX14xZlikbuwqlIQZ-og"
```

## 🎯 Expected Result After Fix

| App | Before Fix | After Fix |
|-----|------------|-----------|
| **Penora** | 50 credits ✅ | 50 credits ✅ |
| **ImageGene** | 0 KU Coins ❌ | 50 KU Coins ✅ |

## 📝 Summary

After implementing this fix:
1. ✅ ImageGene will show real Penora credit balance (50 instead of 0)
2. ✅ Credits will sync in real-time between both apps
3. ✅ Image generation will properly deduct from shared Penora credits
4. ✅ Users will see same balance across both platforms

The key was adding the PENORA_API_KEY authentication to ImageGene's API calls so it can access the unified credit system instead of showing a local balance of 0.