// Real-time credit sync with main sukusuku.ai website
class PenoraRealSync {
    constructor() {
        this.mainSiteUrl = 'https://c1ba9609-94a3-4895-8d7d-a2f5a0c196c7-00-1q7j60lf4r7la.riker.replit.dev';
        this.currentUser = null;
        this.syncInterval = null;
        this.init();
    }

    async init() {
        console.log('🚀 PENORA: Initializing real-time sync...');
        await this.loadUserData();
        this.startRealTimeSync();
        this.setupEventListeners();
    }

    async loadUserData() {
        try {
            // First try to get user status for authentication
            const statusResponse = await fetch('/api/user-status');
            if (statusResponse.ok) {
                this.currentUser = await statusResponse.json();
                
                // If authenticated, sync with unified credit system
                if (this.currentUser && this.currentUser.authenticated) {
                    await this.syncWithUnifiedSystem();
                }
                
                console.log('✅ User data loaded:', this.currentUser);
                this.updateUI();
            }
        } catch (error) {
            console.error('❌ Failed to load user data:', error);
        }
    }

    async syncWithUnifiedSystem() {
        try {
            const syncResponse = await fetch('/api/sync-credits');
            if (syncResponse.ok) {
                const syncData = await syncResponse.json();
                if (syncData.success) {
                    // Update current user credits with unified system data
                    this.currentUser.credits = syncData.credits;
                    console.log(`🔄 CREDIT SYNC: Updated to ${syncData.credits} credits from unified system`);
                }
            }
        } catch (error) {
            console.log('⚠️ Could not sync with unified system:', error);
        }
    }

    updateUI() {
        if (!this.currentUser || !this.currentUser.authenticated) return;

        // Update navbar credits
        const navbarCredit = document.querySelector('.navbar-text .badge, .credits-display');
        if (navbarCredit) {
            navbarCredit.textContent = `${this.currentUser.credits} credits`;
            navbarCredit.className = this.currentUser.credits > 10 ? 'badge bg-success' : 
                                   this.currentUser.credits > 5 ? 'badge bg-warning' : 'badge bg-danger';
        }

        // Update account page if present
        this.updateAccountPage();
        
        // Update any credit displays
        const creditDisplays = document.querySelectorAll('[data-credits]');
        creditDisplays.forEach(display => {
            display.textContent = this.currentUser.credits;
        });
    }

    updateAccountPage() {
        // Update credits breakdown
        const remainingElement = document.querySelector('.text-primary h4');
        const usedElement = document.querySelector('.text-warning h4');
        const originalElement = document.querySelector('.text-success h4');
        
        if (remainingElement) remainingElement.textContent = this.currentUser.credits;
        if (usedElement) usedElement.textContent = this.currentUser.credits_used || 0;
        if (originalElement) originalElement.textContent = this.currentUser.original_credits || 250;

        // Show real user info
        console.log(`📊 Account Page Updated - ${this.currentUser.username}: ${this.currentUser.credits} credits remaining`);
    }

    async syncCreditsUsage(creditsUsed, description) {
        if (!this.currentUser || !this.currentUser.authenticated) {
            console.error('❌ No authenticated user for credit sync');
            return false;
        }

        try {
            const response = await fetch('/api/sync-credits', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    user_id: this.currentUser.user_id,
                    credits_used: creditsUsed,
                    action: 'generation',
                    description: description
                })
            });

            if (response.ok) {
                const result = await response.json();
                console.log('✅ Credits synced:', result);
                
                // Update local user data
                this.currentUser.credits = result.remaining_credits;
                this.currentUser.credits_used = result.total_credits_used;
                
                // Update UI immediately
                this.updateUI();
                
                // Try to sync with main website
                await this.syncWithMainWebsite(result);
                
                return true;
            } else {
                console.error('❌ Credit sync failed:', response.status);
                return false;
            }
        } catch (error) {
            console.error('❌ Credit sync error:', error);
            return false;
        }
    }

    async syncWithMainWebsite(data) {
        try {
            const syncData = {
                user_id: this.currentUser.user_id,
                app: 'penora',
                credits_used: data.credits_used,
                total_credits_used: data.total_credits_used,
                remaining_credits: data.remaining_credits,
                timestamp: new Date().toISOString()
            };

            const response = await fetch(`${this.mainSiteUrl}/api/apps/penora/sync`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(syncData)
            });

            if (response.ok) {
                console.log('✅ Successfully synced with main sukusuku.ai website');
            } else {
                console.log('⚠️ Main website sync failed, but local sync successful');
            }
        } catch (error) {
            console.log('⚠️ Could not reach main website, but local sync successful');
        }
    }

    startRealTimeSync() {
        // Sync every 15 seconds to keep data fresh with unified system
        this.syncInterval = setInterval(async () => {
            await this.loadUserData();
        }, 15000);
        
        // Also add a manual refresh function
        window.refreshCredits = async () => {
            await this.loadUserData();
            console.log('🔄 Manual credit refresh completed');
        };
    }

    setupEventListeners() {
        // Listen for generation events
        document.addEventListener('creditsUsed', async (event) => {
            const { creditsUsed, description } = event.detail;
            await this.syncCreditsUsage(creditsUsed, description);
        });

        // Listen for page generation
        const generateButtons = document.querySelectorAll('[data-action="generate"]');
        generateButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                const form = e.target.closest('form');
                if (form) {
                    const pageCount = form.querySelector('input[name="page_count"]')?.value || 1;
                    const prompt = form.querySelector('input[name="prompt"]')?.value || 'Generation';
                    
                    // Emit credit usage event
                    document.dispatchEvent(new CustomEvent('creditsUsed', {
                        detail: {
                            creditsUsed: parseInt(pageCount),
                            description: `${pageCount} Page(s): ${prompt.substring(0, 50)}...`
                        }
                    }));
                }
            });
        });
    }

    destroy() {
        if (this.syncInterval) {
            clearInterval(this.syncInterval);
        }
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.penoraSync = new PenoraRealSync();
});

// Global function for manual credit sync
window.syncPenoraCredits = async (creditsUsed, description) => {
    if (window.penoraSync) {
        return await window.penoraSync.syncCreditsUsage(creditsUsed, description);
    }
    return false;
};