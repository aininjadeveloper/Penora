# DeepInfra API Setup for Penora

## Overview

Penora has been migrated from OpenAI to DeepInfra API for cost-effective AI text generation using the `mistralai/Mistral-7B-Instruct-v0.3` model.

## Required Setup

### 1. Get DeepInfra API Key

1. Visit [DeepInfra.com](https://deepinfra.com/)
2. Sign up or log in to your account
3. Navigate to API Keys section
4. Create a new API key
5. Copy the API key (format: `xxx-xxxxxxxxxxxxxxxxxxxxxxxx`)

### 2. Add to Replit Secrets

1. In your Replit project, go to **Secrets** tab (lock icon)
2. Click **+ New Secret**
3. Set:
   - **Key**: `DEEPINFRA_API_KEY`
   - **Value**: Your DeepInfra API key from step 1
4. Click **Add Secret**

### 3. Verification

The application will automatically detect the API key and enable AI features. You can verify by:

1. Running the test script: `python3 deepinfra_client.py`
2. Using the single prompt generator with any prompt
3. Checking application logs for "DeepInfra API Test Successful!"

## Migration Changes

✅ **Completed:**
- Created `deepinfra_client.py` module
- Updated `ai_service.py` to use DeepInfra instead of OpenAI
- Removed OpenAI dependencies from `pyproject.toml`
- Updated all templates to remove engine selection
- Cleaned up Premium/GPT-4o references
- Updated documentation and README

## Technical Details

- **Model**: `mistralai/Mistral-7B-Instruct-v0.3`
- **Endpoint**: `https://api.deepinfra.com/v1/openai/chat/completions`
- **Max Tokens**: 2048 (configurable)
- **Temperature**: 0.7 (creative balance)
- **Timeout**: 60 seconds

## Cost Benefits

- **Lower API costs** compared to OpenAI
- **Same quality** text generation
- **Faster response times** in many cases
- **No rate limiting** for basic usage

## Troubleshooting

### "AI service is temporarily unavailable"
- Verify `DEEPINFRA_API_KEY` is set in Replit Secrets
- Check API key is valid at DeepInfra dashboard
- Restart the application workflow

### API Request Failed
- Ensure you have sufficient credits in your DeepInfra account
- Check DeepInfra service status
- Verify internet connectivity

### Rate Limiting
- DeepInfra has generous rate limits for the Mistral model
- If exceeded, wait a few minutes and try again
- Consider upgrading your DeepInfra plan for higher limits

## Support

For DeepInfra-specific issues:
- Visit [DeepInfra Documentation](https://deepinfra.com/docs)
- Contact DeepInfra support
- Check their Discord community

For Penora application issues:
- Check application logs in Replit console
- Verify all environment variables are set
- Test with the included test script