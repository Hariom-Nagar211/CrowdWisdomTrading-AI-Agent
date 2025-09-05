#!/usr/bin/env python3
"""
Demo runner for CrowdWisdomTrading AI Agent
This script demonstrates the system with sample data if APIs are not configured
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path

# Mock data for demonstration when APIs are not available
MOCK_SEARCH_RESULTS = {
    "results": [
        {
            "title": "S&P 500 Closes Higher on Strong Earnings Reports",
            "content": "The S&P 500 index gained 0.8% today, reaching 4,785 points, driven by strong quarterly earnings from major technology companies. Apple and Microsoft both exceeded analyst expectations, with Apple reporting record iPhone sales and Microsoft showing robust cloud computing growth.",
            "url": "https://example.com/sp500-gains",
            "published_date": "2024-01-15T21:00:00Z",
            "score": 0.95
        },
        {
            "title": "Federal Reserve Signals Cautious Approach to Rate Cuts",
            "content": "Federal Reserve Chair Jerome Powell indicated that the central bank will take a measured approach to interest rate adjustments, citing ongoing inflation concerns and labor market strength. Markets reacted positively to the dovish tone.",
            "url": "https://example.com/fed-rates",
            "published_date": "2024-01-15T20:30:00Z",
            "score": 0.92
        },
        {
            "title": "Tesla Announces Expansion Plans, Stock Surges",
            "content": "Tesla shares jumped 2.5% in after-hours trading following the company's announcement of new manufacturing facilities in Texas and Berlin. The electric vehicle maker also reported higher-than-expected delivery numbers for Q4.",
            "url": "https://example.com/tesla-expansion",
            "published_date": "2024-01-15T19:45:00Z",
            "score": 0.89
        },
        {
            "title": "Banking Sector Shows Mixed Results in Earnings Season",
            "content": "Major banks reported mixed quarterly results, with JPMorgan Chase beating expectations while Bank of America faced challenges from higher credit loss provisions. The financial sector closed slightly lower on the day.",
            "url": "https://example.com/banking-earnings",
            "published_date": "2024-01-15T18:30:00Z",
            "score": 0.87
        },
        {
            "title": "Oil Prices Rise on Supply Concerns",
            "content": "Crude oil prices gained 1.2% as geopolitical tensions in the Middle East raised supply concerns. West Texas Intermediate crude closed at $73.45 per barrel, while Brent crude reached $78.20.",
            "url": "https://example.com/oil-prices",
            "published_date": "2024-01-15T17:15:00Z",
            "score": 0.84
        }
    ],
    "images": [
        "https://example.com/sp500-chart.png",
        "https://example.com/fed-rates-chart.png",
        "https://example.com/tesla-stock-chart.png",
        "https://example.com/banking-sector-chart.png"
    ]
}

MOCK_ENGLISH_SUMMARY = """
**Daily Financial Market Summary**
*January 15, 2024 - Market Close Analysis*

**Executive Summary**
US markets closed mixed today with the S&P 500 gaining 0.8% to 4,785 points, driven by strong technology earnings. The Federal Reserve's dovish commentary on future rate cuts provided additional market support, while oil prices rose on supply concerns.

**Key Market Movements**
• S&P 500: +0.8% to 4,785 points (new monthly high)
• NASDAQ Composite: +1.2% led by technology sector strength
• Dow Jones: +0.3% with mixed sector performance
• Oil (WTI): +1.2% to $73.45/barrel on supply concerns

**Corporate Highlights**
• **Apple Inc.**: Exceeded Q4 expectations with record iPhone sales, stock up 3.2%
• **Microsoft Corp.**: Strong cloud computing growth, shares gained 2.8%
• **Tesla Inc.**: Announced facility expansions, after-hours surge of 2.5%
• **Banking Sector**: Mixed earnings results, JPMorgan outperformed while BofA faced headwinds

**Federal Reserve Update**
Chair Powell signaled a measured approach to rate adjustments, citing inflation concerns but acknowledging economic resilience. Markets interpreted the commentary as dovish, supporting equity valuations.

**Tomorrow's Outlook**
Investors will focus on additional earnings reports and economic data releases. The positive momentum from tech earnings may continue, but attention remains on Fed policy signals and geopolitical developments affecting oil markets.

**Risk Factors**
• Geopolitical tensions affecting energy markets
• Mixed banking sector performance
• Ongoing inflation concerns
• Interest rate policy uncertainty
"""

def check_environment():
    """Check if environment is properly configured"""
    required_keys = ['TAVILY_API_KEY']
    optional_keys = ['TELEGRAM_BOT_TOKEN', 'GROQ_API_KEY']
    
    missing_required = [key for key in required_keys if not os.getenv(key)]
    missing_optional = [key for key in optional_keys if not os.getenv(key)]
    
    print("Environment Check:")
    print("="*40)
    
    if missing_required:
        print(f"❌ Missing required keys: {missing_required}")
        print("Will run in DEMO mode with mock data")
        return False
    else:
        print("✅ All required API keys configured")
        
    if missing_optional:
        print(f"⚠️  Optional keys not set: {missing_optional}")
    
    return True

def run_demo_mode():
    """Run demonstration with mock data"""
    print("\n" + "="*50)
    print("RUNNING IN DEMO MODE")
    print("="*50)
    print("Using mock financial data for demonstration...")
    
    # Create output directory
    output_dir = Path("outputs")
    output_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Create mock deliverable
    demo_data = {
        'timestamp': timestamp,
        'mode': 'demo',
        'search_results': MOCK_SEARCH_RESULTS,
        'english_summary': MOCK_ENGLISH_SUMMARY,
        'translations': {
            'arabic': 'ملخص السوق المالي اليومي - [ترجمة تجريبية]',
            'hindi': 'दैनिक वित्तीय बाजार सारांश - [डेमो अनुवाद]',
            'hebrew': 'סיכום שוק פיננסי יומי - [תרגום הדגמה]'
        },
        'pdf_created': f"demo_financial_report_{timestamp}.pdf",
        'telegram_sent': False
    }
    
    # Save demo data
    demo_file = output_dir / f"demo_analysis_{timestamp}.json"
    with open(demo_file, 'w', encoding='utf-8') as f:
        json.dump(demo_data, f, ensure_ascii=False, indent=2)
    
    # Create simple demo PDF
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet
        
        pdf_path = output_dir / f"demo_financial_report_{timestamp}.pdf"
        doc = SimpleDocTemplate(str(pdf_path), pagesize=A4)
        styles = getSampleStyleSheet()
        
        content = []
        content.append(Paragraph("CrowdWisdomTrading AI Agent - Demo Report", styles['Title']))
        content.append(Spacer(1, 20))
        content.append(Paragraph("English Summary:", styles['Heading2']))
        content.append(Paragraph(MOCK_ENGLISH_SUMMARY.replace('\n', '<br/>'), styles['Normal']))
        content.append(Spacer(1, 20))
        content.append(Paragraph("Translations:", styles['Heading2']))
        content.append(Paragraph("Arabic: ملخص السوق المالي اليومي", styles['Normal']))
        content.append(Paragraph("Hindi: दैनिक वित्तीय बाजार सारांश", styles['Normal']))
        content.append(Paragraph("Hebrew: סיכום שוק פיננסי יומי", styles['Normal']))
        
        doc.build(content)
        print(f"✅ Demo PDF created: {pdf_path}")
        
    except ImportError:
        print("⚠️  ReportLab not available, skipping PDF creation")
    
    print(f"\nDemo files created in: {output_dir}")
    print(f"📁 Analysis data: {demo_file.name}")
    
    return demo_data

def run_full_mode():
    """Run full system with real APIs"""
    print("\n" + "="*50)
    print("RUNNING IN FULL MODE")
    print("="*50)
    print("Using real API connections...")
    
    try:
        # Import and run the main system
        from main import main
        return main()
        
    except ImportError as e:
        print(f"❌ Error importing main system: {e}")
        print("Make sure main.py is in the same directory")
        return None
    except Exception as e:
        print(f"❌ Error running full system: {e}")
        return None

def display_results(results):
    """Display execution results"""
    print("\n" + "="*50)
    print("EXECUTION RESULTS")
    print("="*50)
    
    output_dir = Path("outputs")
    if output_dir.exists():
        files = list(output_dir.iterdir())
        if files:
            print("Generated files:")
            for file in sorted(files):
                size = file.stat().st_size if file.is_file() else 0
                print(f"  📄 {file.name} ({size:,} bytes)")
        else:
            print("No output files generated")
    else:
        print("Output directory not found")

def main():
    """Main demonstration function"""
    print("CrowdWisdomTrading AI Agent - Demo Runner")
    print("="*50)
    print("This script demonstrates the financial analysis system")
    print("It can run in two modes:")
    print("1. DEMO MODE: Uses mock data (no API keys required)")
    print("2. FULL MODE: Uses real APIs (requires configuration)")
    print()
    
    # Check environment
    has_apis = check_environment()
    
    # Ask user preference
    if has_apis:
        mode = input("\nRun in (F)ull mode or (D)emo mode? [F/d]: ").lower().strip()
        if mode == 'd' or mode == 'demo':
            results = run_demo_mode()
        else:
            results = run_full_mode()
    else:
        print("\nRunning in demo mode (APIs not configured)...")
        results = run_demo_mode()
    
    # Display results
    display_results(results)
    
    print("\n" + "="*50)
    print("DEMO COMPLETE")
    print("="*50)
    print("Next steps:")
    print("1. Configure your API keys in .env file")
    print("2. Run: python main.py")
    print("3. Check outputs/ directory for results")
    
    return results

if __name__ == "__main__":
    main()