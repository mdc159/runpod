"""
Environment Setup Helper
This script helps you set up your RunPod environment variables.
"""

import os
from pathlib import Path

def create_env_file():
    """Create a .env file with template values."""
    env_content = """# RunPod API Configuration
RUNPOD_API_KEY=your_runpod_api_key_here
RUNPOD_ENDPOINT_ID=your_endpoint_id_here

# Optional: RunPod API Base URL (usually not needed to change)
RUNPOD_API_BASE_URL=https://api.runpod.io

# Optional: Timeout settings
RUNPOD_TIMEOUT=300
"""
    
    env_file = Path(".env")
    if env_file.exists():
        print("⚠️  .env file already exists")
        response = input("Do you want to overwrite it? (y/N): ")
        if response.lower() != 'y':
            print("❌ Setup cancelled")
            return False
    
    try:
        with open(env_file, 'w') as f:
            f.write(env_content)
        print("✅ .env file created successfully")
        print("\n📝 Please edit the .env file and add your RunPod credentials:")
        print("   - RUNPOD_API_KEY: Your API key from RunPod Console")
        print("   - RUNPOD_ENDPOINT_ID: Your endpoint ID")
        return True
    except Exception as e:
        print(f"❌ Error creating .env file: {e}")
        return False

def check_environment():
    """Check if environment variables are set."""
    api_key = os.getenv('RUNPOD_API_KEY')
    endpoint_id = os.getenv('RUNPOD_ENDPOINT_ID')
    
    print("🔍 Checking environment variables...")
    print(f"RUNPOD_API_KEY: {'✅ Set' if api_key else '❌ Not set'}")
    print(f"RUNPOD_ENDPOINT_ID: {'✅ Set' if endpoint_id else '❌ Not set'}")
    
    if api_key and endpoint_id:
        print("\n🎉 All required environment variables are set!")
        return True
    else:
        print("\n⚠️  Some environment variables are missing")
        return False

def main():
    """Main setup function."""
    print("🚀 RunPod Environment Setup")
    print("=" * 40)
    
    # Check if .env file exists
    env_file = Path(".env")
    if not env_file.exists():
        print("📄 No .env file found. Creating one...")
        if create_env_file():
            print("\n📋 Next steps:")
            print("1. Edit the .env file with your RunPod credentials")
            print("2. Run: python runpod_client.py")
        return
    
    # Load environment from .env file
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("✅ Loaded .env file")
    except ImportError:
        print("⚠️  python-dotenv not installed. Install with: pip install python-dotenv")
        print("   Or set environment variables manually")
    
    # Check environment
    if check_environment():
        print("\n🎯 Ready to connect to RunPod!")
        print("Run: python runpod_client.py")
    else:
        print("\n📝 Please set your environment variables:")
        print("   - Edit the .env file, or")
        print("   - Set them as system environment variables")

if __name__ == "__main__":
    main()

