"""
RunPod Connection Configuration
This file contains the configuration for connecting to RunPod.
"""

import os
from typing import Optional

class RunPodConfig:
    """Configuration class for RunPod API connection."""
    
    def __init__(self):
        # Load from environment variables or set defaults
        self.api_key = os.getenv('RUNPOD_API_KEY', '')
        self.endpoint_id = os.getenv('RUNPOD_ENDPOINT_ID', '')
        self.api_base_url = os.getenv('RUNPOD_API_BASE_URL', 'https://api.runpod.io')
        self.timeout = int(os.getenv('RUNPOD_TIMEOUT', '300'))
    
    def validate(self) -> bool:
        """Validate that required configuration is present."""
        if not self.api_key:
            print("❌ RUNPOD_API_KEY is not set")
            return False
        if not self.endpoint_id:
            print("❌ RUNPOD_ENDPOINT_ID is not set")
            return False
        return True
    
    def get_headers(self) -> dict:
        """Get headers for API requests."""
        return {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }

# Example usage
if __name__ == "__main__":
    config = RunPodConfig()
    print("RunPod Configuration:")
    print(f"API Key: {'*' * 20 if config.api_key else 'Not set'}")
    print(f"Endpoint ID: {config.endpoint_id or 'Not set'}")
    print(f"API Base URL: {config.api_base_url}")
    print(f"Timeout: {config.timeout}s")
    print(f"Valid: {config.validate()}")

