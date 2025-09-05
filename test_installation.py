#!/usr/bin/env python3
"""
Installation test script for CrowdWisdomTrading AI Agent
This script verifies that all dependencies are properly installed
"""

import sys
import importlib
from pathlib import Path

def test_python_version():
    """Test Python version compatibility"""
    print("Testing Python version...")
    if sys.version_info >= (3, 8):
        print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro} - Compatible")
        return True
    else:
        print(f"❌ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro} - Requires 3.8+")
        return False

def test_imports():
    """Test all required imports"""
    print("\nTesting required imports...")
    
    required_packages = [
        ('crewai', 'CrewAI framework'),
        ('crewai_tools', 'CrewAI tools'),
        ('litellm', 'LiteLLM client'),
        ('tavily', 'Tavily search API'),
        ('telegram', 'Telegram bot API'),
        ('reportlab', 'PDF generation'),
        ('PIL', 'Image processing (Pillow)'),
        ('requests', 'HTTP requests'),
        ('dotenv', 'Environment variables')
    ]
    
    optional_packages = [
        ('groq', 'Groq API client'),
        ('matplotlib', 'Plotting library'),
        ('pandas', 'Data analysis'),
        ('beautifulsoup4', 'HTML parsing')
    ]
    
    results = {'required': [], 'optional': [], 'missing_required': [], 'missing_optional': []}
    
    # Test required packages
    for package, description in required_packages:
        try:
            importlib.import_module(package)
            print(f"✅ {package} - {description}")
            results['required'].append(package)
        except ImportError:
            print(f"❌ {package} - {description} (MISSING)")
            results['missing_required'].append(package)
    
    # Test optional packages
    for package, description in optional_packages:
        try:
            importlib.import_module(package)
            print(f"✅ {package} - {description} (optional)")
            results['optional'].append(package)
        except ImportError:
            print(f"⚠️  {package} - {description} (optional, not installed)")
            results['missing_optional'].append(package)
    
    return results

def test_file_structure():
    """Test required file structure"""
    print("\nTesting file structure...")
    
    required_files = [
        ('main.py', 'Main application file'),
        ('requirements.txt', 'Dependencies list'),
        ('README.md', 'Documentation')
    ]
    
    optional_files = [
        ('.env', 'Environment variables'),
        ('setup.py', 'Setup script'),
        ('demo.py', 'Demo runner')
    ]
    
    results = {'found': [], 'missing': []}
    
    for filename, description in required_files:
        if Path(filename).exists():
            print(f"✅ {filename} - {description}")
            results['found'].append(filename)
        else:
            print(f"❌ {filename} - {description} (MISSING)")
            results['missing'].append(filename)
    
    for filename, description in optional_files:
        if Path(filename).exists():
            print(f"✅ {filename} - {description} (optional)")
            results['found'].append(filename)
        else:
            print(f"⚠️  {filename} - {description} (optional, not found)")
    
    return results

def test_directories():
    """Test required directories"""
    print("\nTesting directories...")
    
    required_dirs = ['outputs', 'logs', 'temp']
    
    for dirname in required_dirs:
        dir_path = Path(dirname)
        if dir_path.exists() and dir_path.is_dir():
            print(f"✅ {dirname}/ directory exists")
        else:
            print(f"⚠️  {dirname}/ directory missing (will be created automatically)")
            try:
                dir_path.mkdir(exist_ok=True)
                print(f"✅ Created {dirname}/ directory")
            except Exception as e:
                print(f"❌ Failed to create {dirname}/: {e}")

def test_environment_file():
    """Test environment file configuration"""
    print("\nTesting environment configuration...")
    
    env_file = Path('.env')
    if not env_file.exists():
        print("⚠️  .env file not found")
        print("   This is normal for first setup - run setup.py to create it")
        return False
    
    with open(env_file, 'r') as f:
        content = f.read()
    
    required_vars = ['TAVILY_API_KEY']
    optional_vars = ['TELEGRAM_BOT_TOKEN', 'TELEGRAM_CHANNEL_ID', 'GROQ_API_KEY']
    
    for var in required_vars:
        if var in content:
            if f'{var}=your_' in content or f'{var}=' in content:
                print(f"⚠️  {var} found but not configured")
            else:
                print(f"✅ {var} configured")
        else:
            print(f"❌ {var} missing from .env")
    
    for var in optional_vars:
        if var in content:
            if f'{var}=your_' in content or f'{var}=' in content:
                print(f"⚠️  {var} found but not configured (optional)")
            else:
                print(f"✅ {var} configured (optional)")
    
    return True

def test_basic_functionality():
    """Test basic system functionality"""
    print("\nTesting basic functionality...")
    
    try:
        # Test CrewAI import and basic usage
        from crewai import Agent
        
        test_agent = Agent(
            role="Test Agent",
            goal="Test basic functionality",
            backstory="This is a test agent",
            verbose=False
        )
        
        print("✅ CrewAI Agent creation successful")
        
        # Test LiteLLM import
        import litellm
        print("✅ LiteLLM import successful")
        
        # Test other core imports
        from datetime import datetime
        import json
        import logging
        
        print("✅ Core Python modules working")
        
        return True
        
    except Exception as e:
        print(f"❌ Basic functionality test failed: {e}")
        return False

def generate_report(results):
    """Generate test report"""
    print("\n" + "="*60)
    print("INSTALLATION TEST REPORT")
    print("="*60)
    
    # Python version
    python_ok = sys.version_info >= (3, 8)
    print(f"Python Version: {'✅ PASS' if python_ok else '❌ FAIL'}")
    
    # Required packages
    missing_required = results.get('missing_required', [])
    packages_ok = len(missing_required) == 0
    print(f"Required Packages: {'✅ PASS' if packages_ok else '❌ FAIL'}")
    if missing_required:
        print(f"  Missing: {', '.join(missing_required)}")
    
    # File structure
    files_ok = 'main.py' in results.get('found', [])
    print(f"File Structure: {'✅ PASS' if files_ok else '❌ FAIL'}")
    
    # Overall status
    overall_ok = python_ok and packages_ok and files_ok
    
    print(f"\nOverall Status: {'✅ READY TO RUN' if overall_ok else '❌ NEEDS ATTENTION'}")
    
    if not overall_ok:
        print("\nNext Steps:")
        if not python_ok:
            print("1. Upgrade to Python 3.8 or higher")
        if missing_required:
            print("2. Install missing packages: pip install " + " ".join(missing_required))
        if not files_ok:
            print("3. Ensure main.py is in the current directory")
    else:
        print("\nYou're ready to run the system!")
        print("Next steps:")
        print("1. Configure API keys in .env file")
        print("2. Run: python demo.py (for demonstration)")
        print("3. Run: python main.py (for full system)")
    
    return overall_ok

def main():
    """Main test function"""
    print("CrowdWisdomTrading AI Agent - Installation Test")
    print("="*50)
    print("This script verifies that your installation is complete and ready to run.\n")
    
    # Run all tests
    python_ok = test_python_version()
    import_results = test_imports()
    file_results = test_file_structure()
    test_directories()
    test_environment_file()
    functionality_ok = test_basic_functionality()
    
    # Combine results
    all_results = {
        'python_ok': python_ok,
        'functionality_ok': functionality_ok,
        **import_results,
        **file_results
    }
    
    # Generate report
    overall_ok = generate_report(all_results)
    
    # Provide specific guidance
    if not overall_ok:
        print("\n" + "="*60)
        print("TROUBLESHOOTING GUIDE")
        print("="*60)
        
        if not python_ok:
            print("\nPython Version Issue:")
            print("- Download Python 3.8+ from https://python.org")
            print("- Or use pyenv: pyenv install 3.11")
        
        if all_results.get('missing_required'):
            print("\nMissing Required Packages:")
            print("- Run: pip install -r requirements.txt")
            print("- Or install individually:")
            for pkg in all_results['missing_required']:
                print(f"  pip install {pkg}")
        
        if 'main.py' not in all_results.get('found', []):
            print("\nMissing Files:")
            print("- Ensure you have all project files in the current directory")
            print("- Check that main.py exists and is not corrupted")
    
    return overall_ok

if __name__ == "__main__":
    main()