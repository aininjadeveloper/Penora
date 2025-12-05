"""
DeepInfra API Client for Penora AI Text Generation

This module provides a simple interface to DeepInfra's chat completions API
using the mistralai/Mistral-7B-Instruct-v0.3 model.

Setup:
- Add DEEPINFRA_API_KEY to your Replit Secrets with your DeepInfra API key
- The key can be obtained from https://deepinfra.com/
"""

import os
import requests
import json
from typing import Dict, Any


def ask_deepinfra(prompt: str, system_msg: str = "You are a helpful assistant.", max_tokens: int = 2500, model: str = "mistralai/Mistral-7B-Instruct-v0.3") -> str:
    """
    Send a prompt to DeepInfra's chat completions API.
    
    Args:
        prompt (str): The user prompt to send to the AI
        system_msg (str): System message to set AI behavior
        max_tokens (int): Maximum tokens to generate (default: 2500)
    
    Returns:
        str: The AI's response text
    
    Raises:
        Exception: If API call fails or returns an error
    """
    api_key = os.environ.get("DEEPINFRA_API_KEY")
    if not api_key:
        raise Exception("DEEPINFRA_API_KEY environment variable not set. Please add it to Replit Secrets.")
    
    url = "https://api.deepinfra.com/v1/openai/chat/completions"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    data = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": system_msg
            },
            {
                "role": "user", 
                "content": prompt
            }
        ],
        "max_tokens": max_tokens,
        "temperature": 0.7,
        "top_p": 0.9
    }
    
    try:
        # Increase timeout for large requests
        timeout = 120 if max_tokens and max_tokens > 4000 else 60
        response = requests.post(url, headers=headers, json=data, timeout=timeout)
        response.raise_for_status()
        
        result = response.json()
        
        if "choices" in result and len(result["choices"]) > 0:
            return result["choices"][0]["message"]["content"].strip()
        else:
            raise Exception(f"Unexpected API response format: {result}")
            
    except requests.exceptions.RequestException as e:
        raise Exception(f"DeepInfra API request failed: {str(e)}")
    except json.JSONDecodeError as e:
        raise Exception(f"Failed to parse DeepInfra API response: {str(e)}")
    except Exception as e:
        raise Exception(f"DeepInfra API error: {str(e)}")


# Model Configurations
DEEPINFRA_MODELS = {
    'balanced': {
        'name': 'mistralai/Mistral-7B-Instruct-v0.3',
        'display_name': 'Mistral 7B (Balanced)',
        'description': 'Good balance of speed and quality',
        'max_tokens': 2500,
        'cost_multiplier': 1.0
    },
    'creative': {
        'name': 'mistralai/Mixtral-8x7B-Instruct-v0.1',
        'display_name': 'Mixtral 8x7B (Creative)',
        'description': 'Better for creative writing and stories',
        'max_tokens': 4000,
        'cost_multiplier': 2.0
    },
    'fast': {
        'name': 'mistralai/Mistral-7B-Instruct-v0.3',
        'display_name': 'Mistral 7B (Fast)',
        'description': 'Fastest generation for simple tasks',
        'max_tokens': 1000,
        'cost_multiplier': 0.5
    },
    'smart': {
        'name': 'meta-llama/Meta-Llama-3-70B-Instruct',
        'display_name': 'Llama 3 70B (Smart)',
        'description': 'Highest quality for complex instructions',
        'max_tokens': 4000,
        'cost_multiplier': 3.0
    }
}

def get_model_config(model_type='balanced'):
    """Get configuration for a specific model type"""
    return DEEPINFRA_MODELS.get(model_type, DEEPINFRA_MODELS['balanced'])


if __name__ == "__main__":
    # Test the DeepInfra client
    try:
        test_response = ask_deepinfra("Write a short creative story about a space explorer.")
        print("DeepInfra API Test Successful!")
        print(f"Response: {test_response[:200]}...")
    except Exception as e:
        print(f"DeepInfra API Test Failed: {e}")