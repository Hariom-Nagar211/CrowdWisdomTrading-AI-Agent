#!/usr/bin/env python3
"""
Setup script for CrowdWisdomTrading AI Agent
This script helps set up the environment and API keys
"""

import os
import sys
from pathlib import Path

def create_env_file():
    """Create .env file with template"""
    env_content = """# CrowdWisdomTrading AI Agent Environment Variables
# Required
TAVILY_API_KEY=your_tavily_api_key_here

# Optional - for Telegram notifications
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
TELEGRAM_CHANNEL_ID=your_telegram_channel_id_here

# Optional - for additional summaries
GROQ_API_KEY=your_groq_api_key_here

# Optional - for LiteLLM
LITELLM_API_KEY=your_litellm_api_key_here
"""
    
    env_file = Path(".env")
    if not env_file.exists():
        with open(env_file, 'w') as f:
            f.write(env_content)
        print("✓ Created .env template file")
        return True
    else:
        print("⚠ .env file already exists")
        return False

def create_directories():
    """Create necessary directories"""
    directories = [
        "outputs",
        "logs",
        "temp"
    ]
    
    for dir_name in directories:
        dir_path = Path(dir_name)
        dir_path.mkdir(exist_ok=True)
        print(f"✓ Created directory: {dir_name}")

def check_python_version():
    """Check Python version compatibility"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ is required")
        return False
    else:
        print(f"✓ Python version: {sys.version}")
        return True

def install_requirements():
    """Install required packages"""
    try:
        import subprocess
        print("Installing requirements...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✓ Requirements installed successfully")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to install requirements")
        return False
    except FileNotFoundError:
        print("❌ requirements.txt not found")
        return False

def validate_setup():
    """Validate the setup"""
    print("\n" + "="*50)
    print("SETUP VALIDATION")
    print("="*50)
    
    # Check if main files exist
    required_files = ["main.py", "requirements.txt"]
    for file_name in required_files:
        if Path(file_name).exists():
            print(f"✓ {file_name} found")
        else:
            print(f"❌ {file_name} missing")
    
    # Check environment file
    env_file = Path(".env")
    if env_file.exists():
        print("✓ .env file exists")
        
        # Check if keys are configured
        with open(env_file, 'r') as f:
            content = f.read()
            if "your_tavily_api_key_here" in content:
                print("⚠ Please update your API keys in .env file")
            else:
                print("✓ API keys appear to be configured")
    
    print("\n" + "="*50)
    print("NEXT STEPS:")
    print("="*50)
    print("1. Update your API keys in the .env file")
    print("2. Get Tavily API key from: https://tavily.com")
    print("3. (Optional) Set up Telegram bot for notifications")
    print("4. Run: python main.py")
    print("="*50)

def main():
    """Main setup function"""
    print("CrowdWisdomTrading AI Agent Setup")
    print("="*40)
    
    # Check Python version
    if not check_python_version():
        return
    
    # Create directories
    create_directories()
    
    # Create env file
    create_env_file()
    
    # Install requirements
    if Path("requirements.txt").exists():
        install_choice = input("\nInstall requirements? (y/n): ").lower().strip()
        if install_choice == 'y':
            install_requirements()
    else:
        print("⚠ requirements.txt not found, skipping installation")
    
    # Validate setup
    validate_setup()

if __name__ == "__main__":
    main()