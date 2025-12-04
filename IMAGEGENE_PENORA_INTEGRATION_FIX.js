// ImageGene + Penora Real-Time Credit Integration Fix
// Add this code to ImageGene to sync with Penora credit system using PENORA_API_KEY

const PENORA_API_BASE = 'https://e1e07499-d292-4451-b55b-9647412a4052-00-3cl7v3i6gfvjy.spock.replit.dev';
const PENORA_API_KEY = 'Pl2UbWIUMgFNQ-iUtQZSozcSUTd1cyNtsNDMhw87bTRST2fN15qT8DP0MG8ZihhZLDcX14xZlikbuwqlIQZ-og';

// ✅ STEP 1: Get Real Credit Balance from Penora
async function getPenoraCredits(userId) {
    try {
        console.log(`🔍 Checking Penora credits for user: ${userId}`);
        
        const response = await fetch(`${PENORA_API_BASE}/api/unified/user-info?user_id=${userId}`, {
            method: 'GET',
            headers: {
                'X-API-Key': PENORA_API_KEY,
                'Content-Type': 'application/json'
            }
        });
        
        const data = await response.json();
        
        if (data.success) {
            console.log(`✅ Penora credits loaded: ${data.credits} KU coins`);
            return {
                success: true,
                credits: data.credits,
                storage: data.storage
            };
        } else {
            console.error('❌ Failed to get Penora credits:', data.error);
            return { success: false, credits: 0 };
        }
    } catch (error) {
        console.error('❌ Error connecting to Penora:', error);
        return { success: false, credits: 0 };
    }
}

// ✅ STEP 2: Deduct Credits in Penora When Generating Images
async function deductPenoraCredits(userId, amount, description = 'Image generation') {
    try {
        console.log(`💰 Deducting ${amount} credits from Penora for user: ${userId}`);
        
        const response = await fetch(`${PENORA_API_BASE}/api/unified/deduct-credits`, {
            method: 'POST',
            headers: {
                'X-API-Key': PENORA_API_KEY,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                user_id: userId,
                amount: amount,
                app_name: 'imagegene',
                description: description,
                project_code: `img_${Date.now()}`
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            console.log(`✅ Credits deducted successfully. New balance: ${data.new_balance}`);
            return {
                success: true,
                newBalance: data.new_balance,
                deducted: data.credits_deducted
            };
        } else {
            console.error('❌ Failed to deduct credits:', data.error);
            return { success: false, error: data.error };
        }
    } catch (error) {
        console.error('❌ Error deducting Penora credits:', error);
        return { success: false, error: error.message };
    }
}

// ✅ STEP 3: Save Generated Image to Penora Workspace
async function saveToPenoraWorkspace(userId, imageData, metadata) {
    try {
        console.log(`💾 Saving image to Penora workspace for user: ${userId}`);
        
        const response = await fetch(`${PENORA_API_BASE}/api/unified/save-project`, {
            method: 'POST',
            headers: {
                'X-API-Key': PENORA_API_KEY,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                user_id: userId,
                app_source: 'imagegene',
                project_type: 'ai_artwork',
                title: metadata.title || `AI Art ${Date.now()}`,
                content: imageData,
                metadata: {
                    prompt: metadata.prompt,
                    style: metadata.style,
                    dimensions: metadata.dimensions,
                    model: metadata.model,
                    generated_at: new Date().toISOString()
                }
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            console.log(`✅ Image saved to Penora workspace: ${data.project_code}`);
            return { success: true, projectCode: data.project_code };
        } else {
            console.error('❌ Failed to save to Penora workspace:', data.error);
            return { success: false, error: data.error };
        }
    } catch (error) {
        console.error('❌ Error saving to Penora workspace:', error);
        return { success: false, error: error.message };
    }
}

// ✅ STEP 4: Update ImageGene UI with Real Credits
function updateImageGeneCreditsDisplay(credits) {
    // Update the credit display in ImageGene UI
    const creditElements = document.querySelectorAll('.ku-coins-display, .credits-display, [data-credits]');
    
    creditElements.forEach(element => {
        if (element.textContent.includes('KU Coins') || element.textContent.includes('credits')) {
            element.textContent = `${credits} KU Coins`;
        }
        
        if (element.hasAttribute('data-credits')) {
            element.setAttribute('data-credits', credits);
            element.textContent = credits;
        }
    });
    
    // Update specific ImageGene elements
    const kuCoinsElement = document.querySelector('.ku-coins-count');
    if (kuCoinsElement) {
        kuCoinsElement.textContent = credits;
    }
    
    // Update account info
    const accountCredits = document.querySelector('.account-credits');
    if (accountCredits) {
        accountCredits.textContent = credits;
    }
    
    console.log(`✅ ImageGene UI updated with ${credits} KU coins`);
}

// ✅ STEP 5: Initialize Penora Integration on Page Load
async function initializePenoraIntegration() {
    try {
        // Get current user ID (replace with your actual user ID method)
        const userId = getCurrentUserId(); // You need to implement this
        
        if (!userId) {
            console.error('❌ No user ID found for Penora integration');
            return;
        }
        
        console.log('🚀 Initializing Penora credit integration...');
        
        // Get real credits from Penora
        const creditData = await getPenoraCredits(userId);
        
        if (creditData.success) {
            // Update ImageGene UI with real credits
            updateImageGeneCreditsDisplay(creditData.credits);
            
            // Store user data for later use
            window.imagegenePenoraData = {
                userId: userId,
                credits: creditData.credits,
                storage: creditData.storage,
                lastSync: new Date()
            };
            
            console.log('✅ Penora integration initialized successfully');
        } else {
            console.error('❌ Failed to initialize Penora integration');
        }
        
    } catch (error) {
        console.error('❌ Error initializing Penora integration:', error);
    }
}

// ✅ STEP 6: Complete Image Generation with Penora Integration
async function generateImageWithPenoraSync(prompt, settings) {
    try {
        const userData = window.imagegenePenoraData;
        if (!userData) {
            throw new Error('Penora integration not initialized');
        }
        
        // Calculate credit cost based on image settings
        const creditCost = calculateImageCreditCost(settings);
        
        console.log(`🎨 Starting image generation. Cost: ${creditCost} credits`);
        
        // Check if user has enough credits
        const currentCredits = await getPenoraCredits(userData.userId);
        if (!currentCredits.success || currentCredits.credits < creditCost) {
            throw new Error(`Insufficient credits. You have ${currentCredits.credits}, need ${creditCost}`);
        }
        
        // Deduct credits before generation
        const deduction = await deductPenoraCredits(userData.userId, creditCost, `Image: ${prompt.substring(0, 50)}...`);
        if (!deduction.success) {
            throw new Error(`Credit deduction failed: ${deduction.error}`);
        }
        
        // Generate image (your existing ImageGene logic)
        const imageResult = await generateImage(prompt, settings);
        
        // Save to Penora workspace
        await saveToPenoraWorkspace(userData.userId, imageResult.imageData, {
            title: `AI Art: ${prompt}`,
            prompt: prompt,
            style: settings.style,
            dimensions: `${settings.width}x${settings.height}`,
            model: settings.model
        });
        
        // Update UI with new balance
        updateImageGeneCreditsDisplay(deduction.newBalance);
        
        // Update stored data
        window.imagegenePenoraData.credits = deduction.newBalance;
        window.imagegenePenoraData.lastSync = new Date();
        
        console.log(`✅ Image generation complete! Credits remaining: ${deduction.newBalance}`);
        
        return {
            success: true,
            imageData: imageResult.imageData,
            creditsRemaining: deduction.newBalance,
            creditsCost: creditCost
        };
        
    } catch (error) {
        console.error('❌ Image generation failed:', error);
        
        // Show error to user
        showImageGeneError(error.message);
        
        throw error;
    }
}

// ✅ STEP 7: Helper Functions
function calculateImageCreditCost(settings) {
    // Calculate credits based on image settings
    const { width, height, quality, style } = settings;
    
    let baseCost = 2; // Base cost for any image
    
    // Size multiplier
    if (width * height >= 1024 * 1024) {
        baseCost = 5; // High resolution
    } else if (width * height >= 512 * 512) {
        baseCost = 3; // Medium resolution
    }
    
    // Quality multiplier
    if (quality === 'premium' || style === 'photorealistic') {
        baseCost += 2;
    }
    
    return baseCost;
}

function getCurrentUserId() {
    // Replace this with your actual method to get current user ID
    // This could be from session, localStorage, or API call
    
    // Example implementations:
    return localStorage.getItem('userId') || 
           sessionStorage.getItem('userId') || 
           window.currentUserId ||
           document.querySelector('[data-user-id]')?.getAttribute('data-user-id');
}

function showImageGeneError(message) {
    // Show error in ImageGene UI
    const errorContainer = document.querySelector('.error-container') || document.body;
    
    const errorDiv = document.createElement('div');
    errorDiv.className = 'penora-error';
    errorDiv.style.cssText = `
        background: #ff4444;
        color: white;
        padding: 10px;
        border-radius: 5px;
        margin: 10px 0;
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 9999;
    `;
    errorDiv.textContent = message;
    
    errorContainer.appendChild(errorDiv);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        errorDiv.remove();
    }, 5000);
}

// ✅ STEP 8: Auto-Initialize on Page Load
document.addEventListener('DOMContentLoaded', initializePenoraIntegration);

// ✅ STEP 9: Periodic Credit Sync (every 30 seconds)
setInterval(async () => {
    if (window.imagegenePenoraData?.userId) {
        const credits = await getPenoraCredits(window.imagegenePenoraData.userId);
        if (credits.success) {
            updateImageGeneCreditsDisplay(credits.credits);
            window.imagegenePenoraData.credits = credits.credits;
        }
    }
}, 30000);

// ✅ STEP 10: Export functions for use in ImageGene
window.PenoraIntegration = {
    getCredits: getPenoraCredits,
    deductCredits: deductPenoraCredits,
    saveToWorkspace: saveToPenoraWorkspace,
    generateWithSync: generateImageWithPenoraSync,
    updateUI: updateImageGeneCreditsDisplay,
    initialize: initializePenoraIntegration
};

console.log('🔗 Penora Integration loaded successfully!');