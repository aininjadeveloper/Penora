# Penora - AI Text Generation Platform

## Overview
Penora is an AI-powered text generation platform built with Flask that allows users to create content through single prompts or multi-chapter stories. It operates on a credit-based system, integrating with DeepInfra for AI text generation and sukusuku.ai for user management and credit purchases. The platform is designed for high-performance production deployment, featuring optimized authentication, database operations, and seamless integration with a main website's SSO system. Its core capabilities include sophisticated AI text generation, comprehensive content management, and robust user credit tracking.

## User Preferences
```
Preferred communication style: Simple, everyday language.
```

## Recent Changes
- **Critical Payment Bug Fixed** (September 2, 2025): Fixed critical bug where users paid money but didn't receive credits. Issue was missing top-up package IDs (topup_10, topup_25, topup_50) in payment verification function. Users now properly receive credits after successful payment. Resolved "Payment verification error" that caused money deduction without credit addition.
- **SukuSuku.ai Link Updates** (September 2, 2025): Updated all sukusuku.ai references to redirect to https://suku-suku-site-developeraim.replit.app. Updated login links, "Powered by" footer links, and backend authentication URLs in templates and Python files.
- **Quick Top-Up Feature Added** (September 2, 2025): Implemented compact top-up section in pricing page with 3 affordable options: 10 Ku coins ($1), 25 Ku coins ($3), and 50 Ku coins ($5). Features direct purchase buttons for instant credit delivery, compact card layout, and integrated Razorpay payment processing. Perfect for users who need small credit boosts without monthly subscriptions.
- **ImageGene Integration Fix** (September 2, 2025): Fixed "Transform Text to Visual Art" button to properly redirect to ImageGene at https://image-gene-developeraim.replit.app/. Updated button text to "ImageGene" with appropriate icon and description. Users can now seamlessly navigate between Penora text generation and ImageGene image generation with unified authentication and credit system.
- **Authentic SukuSuku.ai Authentication** (September 2, 2025): Implemented proper JWT and URL parameter authentication system to display authentic user details from sukusuku.ai. Users now see correct information (e.g., "developer aim" with developeraimw@gmail.com) instead of placeholder accounts. Enhanced JWT token validation with sukusuku-ai-secret-key-2025 and proper session management.
- **Credit Standardization Fix** (September 2, 2025): Emergency fix to standardize all users across the unified system to exactly 50 credits. Reset 6 users from varying amounts (47-250 credits) to consistent 50 credits. Updated database schema default to 50 credits for new users. All existing and new users now have identical 50 credit starting balance across Penora and ImageGene.
- **Complete Unified Credit System Integration** (August 28, 2025): Fixed credit deduction system with real-time synchronization between Penora and ImageGene. Enhanced credit deduction function with unified system sync, added session credit updates, created credit sync API endpoint, and resolved Flask route conflicts. Provided complete API integration documentation for ImageGene with JavaScript SDK, authentication headers, and all required endpoints for unified credit management.
- **PENORA_API_KEY Authentication System** (August 28, 2025): Implemented secure API key authentication for cross-app integration. Generated 64-character secure API key and added environment variable support. All unified endpoints now require PENORA_API_KEY for external access, enabling ImageGene to securely check balances, deduct credits, and maintain real-time synchronization. Created comprehensive integration guides for seamless ImageGene deployment.
- **Unified Credit and Workspace System** (August 20, 2025): Implemented complete integration between Penora and ImageGene with shared credit system and unified workspace. Users now have single credit pool and 1MB storage shared across both applications. Created comprehensive API endpoints for cross-app integration, enhanced user isolation system, and real-time credit deduction. Both apps now work seamlessly together with merged project displays and unified transaction history.
- **Complete Ku Coin System Upgrade** (August 19, 2025): Fully transformed entire platform from "credits" to "Ku coins" with professional card-based UI layout. Implemented monthly/yearly plans with 50% yearly savings: Lite ($20/500 Ku monthly, $120/3000 Ku yearly), Pro ($50/1500 Ku monthly, $300/9000 Ku yearly), Studio ($150/5000 Ku monthly, $900/30000 Ku yearly). Updated all templates, navigation, home page, and pricing page with interactive monthly/yearly toggle, proper card layouts with icons, detailed feature breakdowns, and consistent 1MB storage limits across all plans.
- **Cross-App Workspace Integration** (August 12, 2025): Implemented comprehensive API system allowing external applications to access user's Penora workspace. Added `/api/user-projects`, `/api/project/<code>`, and `/api/cross-app/auth` endpoints. External apps can now display user projects in dropdowns and use content seamlessly, similar to ImageGene integration.
- **Enhanced Post-Generation Features** (August 12, 2025): Added direct action buttons after content generation including Copy, Edit & Save, Download (PDF/DOCX/TXT), and Save Custom Title. Users can now immediately interact with generated content without navigating to workspace.
- **Complete Workspace Functionality** (August 12, 2025): Fixed all workspace functions - view (modal popup), edit, download, copy, and save operations. All JavaScript functions now use correct API endpoints and provide seamless user experience.
- **Internal Server Error Fixed** (August 11, 2025): Completely resolved Internal Server Error during content generation by switching to ai_service_fixed module with improved timeout handling. All content generation now works flawlessly.
- **Database Query Optimization** (August 11, 2025): Fixed all PostgreSQL datatype mismatch errors by ensuring all user_id parameters are properly converted to strings in workspace queries. Eliminated "operator does not exist" errors.
- **Workspace Saving Fixed** (August 11, 2025): Resolved foreign key constraint issues preventing SSO users from saving generated content to workspace. All generated content now automatically saves with unique project codes.
- **1MB Storage Limit** (August 11, 2025): All new users now have exactly 1MB storage limit instead of 5MB, enforced across workspace and project creation.
- **Enhanced Workspace** (August 11, 2025): Added detailed timestamps showing creation and update times, file sizes, and comprehensive project history with proper formatting.
- **Transaction History Display** (August 11, 2025): After payments, users see complete transaction history with enhanced timestamp details, payment status, and credit tracking.
- **Database Schema Fixed** (August 11, 2025): Updated WorkspaceProject model to use String user_id instead of Integer to handle large SSO user IDs, removed foreign key constraints for SSO compatibility.
- **API Timeout Increased** (August 11, 2025): Increased DeepInfra API timeout from 30s to 60s to prevent connection timeout errors during content generation.
- **Database Errors Fixed** (August 11, 2025): Resolved SQLite INTEGER overflow issues by converting large SSO user IDs to strings, eliminating all database connection errors.
- **SSO Credit System Fixed** (August 11, 2025): Implemented session-based credit deduction for SSO users to bypass database integer overflow issues with large user IDs. All AI features now work properly for SSO users.
- **SSO Authentication Fixed** (August 11, 2025): Resolved database datatype mismatch errors that prevented SSO users from authenticating properly. SSO now works directly in routes.py bypassing database issues.
- **Real User Details Integration**: SSO users from sukusuku.ai main website now appear with correct user details (developer aim, developeraimw@gmail.com) instead of fallback demo accounts.
- **50 Premium Ku Coins**: SSO users automatically receive 50 premium Ku coins upon first authentication from the main website.
- **Payment System Fixed**: Resolved JSON parsing errors in Ku coin purchase system. Razorpay integration now works correctly with proper receipt formatting and user ID handling.
- **SSO Redirect to Home**: SSO users now land on the home page instead of directly in the writer interface.
- **Session Management**: Implemented robust session handling for SSO authentication with permanent sessions and proper user data storage.

## System Architecture

### Backend
- **Framework**: Flask with SQLAlchemy ORM and Flask-Migrate.
- **Database**: PostgreSQL (production) / SQLite (development), optimized for speed with memory journaling and caching.
- **Authentication**: Flask-Login supporting traditional username/password, Google OAuth 2.0, JWT SSO integration, and dynamic URL parameter authentication. Features include intelligent caching and seamless session persistence.
- **Credit System**: Word-based credit calculation (1 credit ≈ 100 words), with real-time sync from a shared user database.
- **Session Management**: Flask sessions with ProxyFix for HTTPS.

### Frontend
- **Template Engine**: Jinja2 with Bootstrap 5 dark theme.
- **UI/UX**: Mobile-first responsive design, live credit balance in navigation, Font Awesome 6.4.0 icons.
- **Writing Tools**: Sudowrite-inspired features including "Complete Write," "Advanced Rewrite," "Rich Describe," and "Smart Brainstorm." These tools are presented in a three-column layout (project sidebar, main editor, results/history panel) with result cards.

### AI Integration
- **Provider**: DeepInfra API, specifically using models like `mistralai/Mistral-7B-Instruct-v0.3` (and others such as Llama-4 Maverick, Mixtral-8, OpenChat-3.5, Gemma-7b) for creative text generation.
- **Features**: Single text generation, multi-chapter story creation with configurable lengths, and dynamic credit cost preview based on model multipliers.
- **Error Handling**: Comprehensive error handling for AI API calls.

### Key Components
- **Data Models**: User, CreditPackage, Transaction, and Generation models for managing authentication, credits, and content.
- **Services**: `AIService` for AI generation, `PDFService` for content export, and `CrossAppIntegration` for external app access.
- **Route Structure**: Authentication, generation, account management, content export endpoints, and cross-app API endpoints.
- **Cross-App APIs**: `/api/user-projects`, `/api/project/<code>`, `/api/cross-app/auth` for external application integration.

### System Design Choices
- **Data Flow**: Seamless user authentication (auto-authentication similar to "imagegene"), credit-checked content generation, real-time credit sync, and multi-format content export.
- **Security**: Werkzeug for password hashing, Flask-Login for session handling, ProxyFix for HTTPS, and server-side input validation.
- **Deployment**: Configured for robust production deployment with environment variables for database and session security, and Replit-specific features.

## External Dependencies

### AI Services
- **DeepInfra API**: Primary AI text generation service.
- **Models**: `mistralai/Mistral-7B-Instruct-v0.3`, Llama-3.1-8B, Mixtral-8x7B, OpenChat-3.5, Gemma-2-7B.

### Credit Purchase System
- **sukusuku.ai**: Integrated for direct credit purchases, instant credit delivery, and management of various credit packages.

### Authentication Services
- **sukusuku.ai**: Provides URL parameter-based and JWT SSO authentication, enabling seamless user creation, data isolation, and credit sync via a shared `users.db` database.

### Frontend Libraries
- **Bootstrap 5**: CSS framework.
- **Font Awesome 6.4.0**: Icon library.

### PDF Generation
- **ReportLab**: Python library for generating PDF documents.