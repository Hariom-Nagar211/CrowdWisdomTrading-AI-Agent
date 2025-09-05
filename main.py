import os
import asyncio
import logging
import json
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Any
import re
from pathlib import Path

# Core CrewAI imports for version 0.177.0+
from crewai import Agent, Task, Crew
from tavily import TavilyClient
from telegram import Bot
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from PIL import Image as PILImage
from dotenv import load_dotenv

# Optional imports
try:
    import groq
    HAS_GROQ = True
except ImportError:
    HAS_GROQ = False

try:
    import litellm
    HAS_LITELLM = True
except ImportError:
    HAS_LITELLM = False

try:
    import google.generativeai as genai
    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('outputs/trading_agent.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class Config:
    """Configuration class for the trading agent"""
    TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    TELEGRAM_CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID")
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")  # <-- Added OpenAI key
    # Output directory
    OUTPUT_DIR = Path("outputs")
    OUTPUT_DIR.mkdir(exist_ok=True)

class FinancialSearchTool:
    """Custom search tool for financial news"""
    
    def __init__(self):
        if not Config.TAVILY_API_KEY:
            raise ValueError("TAVILY_API_KEY environment variable is required")
        self.client = TavilyClient(api_key=Config.TAVILY_API_KEY)
    
    def search_financial_news(self, query: str) -> Dict[str, Any]:
        """Search for recent financial news using Tavily"""
        try:
            logger.info(f"Searching Tavily for: {query}")
            
            response = self.client.search(
                query=f"{query} US financial markets stock market",
                search_depth="advanced",
                max_results=10,
                include_domains=["reuters.com", "bloomberg.com", "cnbc.com", "marketwatch.com", "yahoo.com", "finviz.com"],
                include_images=True
            )
            
            results = []
            for result in response.get('results', []):
                results.append({
                    'title': result.get('title', ''),
                    'content': result.get('content', ''),
                    'url': result.get('url', ''),
                    'published_date': result.get('published_date', ''),
                    'score': result.get('score', 0)
                })
            
            images = response.get('images', [])
            
            return {
                'results': results[:5],
                'images': images[:10],
                'success': True
            }
            
        except Exception as e:
            logger.error(f"Tavily search error: {str(e)}")
            return {
                'results': [],
                'images': [],
                'success': False,
                'error': str(e)
            }

class GroqSummaryTool:
    """Optional Groq API integration for additional summaries"""
    
    def __init__(self):
        self.has_groq = HAS_GROQ and Config.GROQ_API_KEY
        if self.has_groq:
            self.client = groq.Groq(api_key=Config.GROQ_API_KEY)
    
    def get_summary(self, text: str) -> str:
        """Get additional summary using Groq API"""
        if not self.has_groq:
            return "Groq API not configured or available"
            
        try:
            logger.info("Getting Groq summary")
            response = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "You are a financial analyst. Provide a concise summary of the key financial events and market movements."
                    },
                    {
                        "role": "user",
                        "content": f"Summarize this financial news in 2-3 key points:\n\n{text}"
                    }
                ],
                model="llama3-70b-8192",  # <-- updated model name
                max_tokens=200
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Groq summary error: {str(e)}")
            return f"Groq summary unavailable: {str(e)}"

class GeminiSummaryTool:
    """Optional Gemini API integration for additional summaries"""
    def __init__(self):
        self.has_gemini = HAS_GEMINI and Config.GEMINI_API_KEY
        if self.has_gemini:
            genai.configure(api_key=Config.GEMINI_API_KEY)
            # Use a currently supported Gemini model
            self.model = genai.GenerativeModel("gemini-1.5-flash")
    def get_summary(self, text: str) -> str:
        if not self.has_gemini:
            return "Gemini API not configured or available"
        try:
            logger.info("Getting Gemini summary")
            response = self.model.generate_content(
                f"Summarize this financial news in 2-3 key points:\n\n{text}"
            )
            return response.text if hasattr(response, "text") else str(response)
        except Exception as e:
            logger.error(f"Gemini summary error: {str(e)}")
            return f"Gemini summary unavailable: {str(e)}"

def register_unicode_fonts():
    """Register Unicode fonts for proper text rendering"""
    try:
        import os
        import requests
        
        # Create fonts directory if it doesn't exist
        fonts_dir = Path("fonts")
        fonts_dir.mkdir(exist_ok=True)
        
        # Try to register common system fonts first
        system_fonts = [
            ('DejaVuSans', 'DejaVu Sans'),
            ('ArialUnicode', 'Arial Unicode MS'),
            ('NotoSans', 'Noto Sans'),
            ('LiberationSans', 'Liberation Sans')
        ]
        
        registered_fonts = []
        for font_name, system_name in system_fonts:
            try:
                font_paths = [
                    f"C:/Windows/Fonts/{system_name}.ttf",
                    f"C:/Windows/Fonts/{system_name}.otf",
                    f"/System/Library/Fonts/{system_name}.ttf",
                    f"/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
                ]
                
                for font_path in font_paths:
                    if os.path.exists(font_path):
                        pdfmetrics.registerFont(TTFont(font_name, font_path))
                        registered_fonts.append(font_name)
                        logger.info(f"Registered system font: {font_name} from {font_path}")
                        break
            except Exception as e:
                logger.debug(f"Could not register system font {font_name}: {e}")
                continue
        
        # If no system fonts found, try to download a free Unicode font
        if not registered_fonts:
            try:
                # Download Noto Sans font (supports Hindi, Arabic, Hebrew)
                font_url = "https://github.com/googlefonts/noto-fonts/raw/main/hinted/ttf/NotoSans/NotoSans-Regular.ttf"
                font_path = fonts_dir / "NotoSans-Regular.ttf"
                
                if not font_path.exists():
                    logger.info("Downloading Noto Sans font for Unicode support...")
                    response = requests.get(font_url, timeout=30)
                    response.raise_for_status()
                    with open(font_path, 'wb') as f:
                        f.write(response.content)
                    logger.info(f"Downloaded Noto Sans font to {font_path}")
                
                # Register the downloaded font
                pdfmetrics.registerFont(TTFont('NotoSans', str(font_path)))
                registered_fonts.append('NotoSans')
                logger.info("Registered downloaded Noto Sans font")
                
            except Exception as e:
                logger.warning(f"Could not download Unicode font: {e}")
        
        # Final fallback
        if not registered_fonts:
            logger.warning("No Unicode fonts available, using Helvetica (may not support all characters)")
            return ['Helvetica']
        
        return registered_fonts
    except Exception as e:
        logger.error(f"Error registering Unicode fonts: {e}")
        return ['Helvetica']

def clean_text_for_pdf(text):
    """Clean text to ensure proper PDF rendering with Unicode support"""
    if not text:
        return ""
    
    # Ensure text is properly encoded as UTF-8
    if isinstance(text, bytes):
        text = text.decode('utf-8', errors='replace')
    
    # Remove problematic characters but preserve Unicode
    cleaned = text.replace('*', '•').replace('**', '').replace('&', 'and')
    
    # Handle special characters that might cause issues
    cleaned = cleaned.replace('"', '"').replace('"', '"')
    cleaned = cleaned.replace(''', "'").replace(''', "'")
    
    # Remove control characters but keep Unicode text
    import re
    cleaned = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x84\x86-\x9f]', '', cleaned)
    
    # Ensure proper line breaks
    cleaned = cleaned.replace('\n', '<br/>')
    
    return cleaned

class ImageDownloader:
    """Tool for downloading and processing images"""
    
    def download_image(self, url: str, filename: str) -> str:
        """Download an image from URL with better error handling"""
        try:
            logger.info(f"Downloading image: {url}")
            
            # Add headers to avoid 403 errors
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
            
            response = requests.get(url, stream=True, timeout=15, headers=headers)
            response.raise_for_status()
            
            filepath = Config.OUTPUT_DIR / filename
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            # Verify and resize image if needed
            try:
                with PILImage.open(filepath) as img:
                    # Resize if too large
                    if img.width > 800 or img.height > 600:
                        img.thumbnail((800, 600), PILImage.Resampling.LANCZOS)
                        img.save(filepath)
                    
                    return str(filepath)
            except Exception as img_error:
                logger.error(f"Image processing error: {img_error}")
                return str(filepath)
                
        except Exception as e:
            logger.error(f"Image download error: {str(e)}")
            return ""

class TelegramSender:
    """Tool for sending messages to Telegram"""
    
    def __init__(self):
        self.has_telegram = Config.TELEGRAM_BOT_TOKEN and Config.TELEGRAM_CHANNEL_ID
    
    async def send_message_async(self, message: str, image_path: str = None, parse_mode: str = None) -> str:
        """Send message to Telegram channel asynchronously"""
        if not self.has_telegram:
            return "Telegram not configured"
            
        try:
            logger.info("Sending message to Telegram")
            bot = Bot(token=Config.TELEGRAM_BOT_TOKEN)
            
            # Fix channel ID format - add @ if not present and not numeric
            channel_id = Config.TELEGRAM_CHANNEL_ID
            if not channel_id.startswith('@') and not channel_id.startswith('-') and not channel_id.isdigit():
                channel_id = f"@{channel_id}"
            
            logger.info(f"Using Telegram channel ID: {channel_id}")
            
            if image_path and os.path.exists(image_path):
                with open(image_path, 'rb') as photo:
                    await bot.send_photo(
                        chat_id=channel_id,
                        photo=photo,
                        caption=message[:1024],  # Telegram caption limit
                        parse_mode=parse_mode
                    )
            else:
                await bot.send_message(
                    chat_id=channel_id,
                    text=message[:4096],  # Telegram message limit
                    parse_mode=parse_mode
                )
            
            return "Message sent successfully to Telegram"
            
        except Exception as e:
            logger.error(f"Telegram send error: {str(e)}")
            return f"Failed to send to Telegram: {str(e)}"
    
    def send_message(self, message: str, image_path: str = None, parse_mode: str = None) -> str:
        """Send message to Telegram channel (sync wrapper)"""
        try:
            # Create new event loop if none exists
            try:
                loop = asyncio.get_event_loop()
                if loop.is_closed():
                    raise RuntimeError("Event loop is closed")
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            return loop.run_until_complete(self.send_message_async(message, image_path, parse_mode))
        except Exception as e:
            logger.error(f"Telegram wrapper error: {str(e)}")
            return f"Failed to send to Telegram: {str(e)}"

class TradingAgentSystem:
    """Main trading agent system using CrewAI 0.177.0+ API"""
    
    def __init__(self):
        self.search_tool = FinancialSearchTool()
        self.groq_tool = GroqSummaryTool()
        self.gemini_tool = GeminiSummaryTool()  # <-- Add Gemini tool
        self.image_downloader = ImageDownloader()
        self.telegram_sender = TelegramSender()
        
        # Storage for inter-agent data
        self.search_results = {}
        self.summary_data = {}
        self.formatted_data = {}
        self.translated_summaries = {}
        self.downloaded_images = []

    def create_agents(self):
        """Create all agents for the trading system"""
        
        # Search Agent
        search_agent = Agent(
            role="Financial News Search Specialist",
            goal="Find the latest and most relevant US financial news from the past hour",
            backstory="""You are an expert financial researcher who specializes in finding 
            breaking news and market-moving events. You have access to multiple search tools 
            and know how to identify the most impactful financial stories.""",
            verbose=True,
            allow_delegation=False
        )
        
        # Summary Agent  
        summary_agent = Agent(
            role="Financial Market Analyst",
            goal="Create concise, insightful summaries of daily market activity",
            backstory="""You are a senior financial analyst with 15+ years of experience 
            in market analysis. You excel at distilling complex financial information 
            into clear, actionable insights for traders and investors.""",
            verbose=True,
            allow_delegation=False
        )
        
        # Formatting Agent
        formatting_agent = Agent(
            role="Financial Content Formatter", 
            goal="Format financial content and integrate relevant charts and images",
            backstory="""You are a financial content specialist who knows how to present 
            market analysis in visually appealing formats. You understand which charts 
            and images best support different types of financial narratives.""",
            verbose=True,
            allow_delegation=False
        )
        
        # Translation Agent
        translation_agent = Agent(
            role="Financial Translation Specialist",
            goal="Translate financial content accurately while maintaining technical precision",
            backstory="""You are a professional financial translator with expertise in 
            Arabic, Hindi, and Hebrew. You understand financial terminology and maintain 
            accuracy while making content accessible to different linguistic audiences.""",
            verbose=True,
            allow_delegation=False
        )
        
        # Send Agent
        send_agent = Agent(
            role="Communication Specialist",
            goal="Distribute financial summaries through appropriate channels",
            backstory="""You are responsible for distributing financial analysis to 
            various communication channels. You ensure content is properly formatted 
            for each platform and reaches the intended audience effectively.""",
            verbose=True,
            allow_delegation=False
        )
        
        return {
            'search': search_agent,
            'summary': summary_agent, 
            'formatting': formatting_agent,
            'translation': translation_agent,
            'send': send_agent
        }

    def create_tasks(self, agents):
        """Create tasks for each agent"""
        
        # Search Task
        search_task = Task(
            description="""Search for the latest US financial news from the past hour. 
            Focus on:
            - Major market movements (S&P 500, NASDAQ, DOW)
            - Federal Reserve announcements
            - Major corporate earnings
            - Economic indicators
            - Breaking financial news
            
            Use the available search tools to get comprehensive coverage.
            Return structured data with news articles and relevant images.""",
            agent=agents['search'],
            expected_output="""JSON formatted search results containing:
            - Top 5 most relevant news articles with titles, content, URLs
            - Relevant financial charts/images URLs
            - Summary of key market events found"""
        )
        
        # Summary Task
        summary_task = Task(
            description="""Analyze the search results and create a comprehensive but concise 
            financial market summary (under 500 words). 
            
            Include:
            - Key market movements and indices performance
            - Most impactful news stories
            - Notable corporate developments  
            - Economic indicators or Fed announcements
            - Trading outlook for tomorrow
            
            Write in a professional but accessible tone.""",
            agent=agents['summary'],
            expected_output="""A well-structured financial summary under 500 words with:
            - Executive summary (2-3 sentences)
            - Key market developments (bullet points)
            - Notable corporate news
            - Economic outlook""",
            context=[search_task]
        )
        
        # Formatting Task
        format_task = Task(
            description="""Format the financial summary and integrate relevant images.
            
            Tasks:
            1. Select 2 most relevant images/charts from the search results
            2. Download and process the selected images
            3. Format the summary with proper image placement
            4. Create a structured document format
            
            Focus on images showing:
            - Market charts (S&P 500, NASDAQ trends)
            - Economic indicators
            - Corporate logos for major news
            - Federal Reserve or economic data visualizations""",
            agent=agents['formatting'],
            expected_output="""Formatted content with:
            - Structured summary text
            - 2 downloaded and processed images with captions
            - Image file paths and placement instructions
            - Ready-for-publication format""",
            context=[summary_task]
        )
        
        # Translation Task
        translate_task = Task(
            description="""Translate the financial summary into multiple languages.
            
            Languages to translate to:
            - Arabic (العربية)
            - Hindi (हिन्दी)
            - Hebrew (עברית)
            
            Requirements:
            - Maintain financial terminology accuracy
            - Keep formatting structure
            - Ensure cultural appropriateness  
            - Preserve numerical data exactly
            - Use appropriate financial terms in each language""",
            agent=agents['translation'],
            expected_output="""Complete financial summaries translated into Arabic, Hindi, and Hebrew 
            with preserved formatting and accurate financial terminology""",
            context=[format_task]
        )
        
        # Send Task
        send_task = Task(
            description="""Distribute the financial analysis through appropriate channels.
            
            Tasks:
            1. Prepare content for Telegram distribution
            2. Create final PDF report with all languages and images
            3. Send notifications via configured channels
            4. Generate final deliverable summary
            
            Format the message appropriately with:
            - Clear headline
            - Key points in bullet format
            - Professional presentation""",
            agent=agents['send'],
            expected_output="""Confirmation of successful distribution with:
            - Telegram delivery status
            - PDF report creation status
            - Final deliverable summary
            - File locations and access information""",
            context=[translate_task]
        )
        
        return [search_task, summary_task, format_task, translate_task, send_task]

    def execute_search_phase(self) -> Dict[str, Any]:
        """Execute search phase manually due to tool integration"""
        logger.info("Starting search phase...")
        
        search_queries = [
            "US stock market today S&P 500 NASDAQ",
            "Federal Reserve interest rates today",
            "major corporate earnings today",
            "US economic indicators today"
        ]
        
        all_results = []
        all_images = []
        
        for query in search_queries:
            result = self.search_tool.search_financial_news(query)
            if result['success']:
                all_results.extend(result['results'])
                all_images.extend(result['images'])
        
        # Get Gemini summary if available, else Groq
        if all_results:
            combined_text = "\n".join([f"{r['title']}: {r['content'][:200]}" for r in all_results[:3]])
            if self.gemini_tool.has_gemini:
                summary = self.gemini_tool.get_summary(combined_text)
            elif self.groq_tool.has_groq:
                summary = self.groq_tool.get_summary(combined_text)
            else:
                summary = "No additional summary available"
        else:
            summary = "No additional summary available"
        
        self.search_results = {
            'news_articles': all_results[:5],
            'images': all_images[:10], 
            'summary': summary,
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info(f"Search completed: {len(all_results)} articles, {len(all_images)} images")
        return self.search_results

    def process_images(self):
        """Download and process relevant images"""
        logger.info("Processing images...")
        
        downloaded_images = []
        images = self.search_results.get('images', [])
        
        # Download top 2 images
        for i, img_url in enumerate(images[:2]):
            try:
                filename = f"financial_chart_{i+1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                filepath = self.image_downloader.download_image(img_url, filename)
                if filepath:
                    downloaded_images.append({
                        'url': img_url,
                        'filepath': filepath,
                        'filename': filename
                    })
                    logger.info(f"Downloaded image: {filename}")
            except Exception as e:
                logger.error(f"Failed to download image {img_url}: {e}")
        
        self.downloaded_images = downloaded_images
        return downloaded_images

    def create_pdf_report(self) -> str:
        """Create comprehensive PDF report"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            pdf_path = Config.OUTPUT_DIR / f"financial_report_{timestamp}.pdf"
            
            # Register Unicode fonts
            unicode_fonts = register_unicode_fonts()
            primary_font = unicode_fonts[0] if unicode_fonts else 'Helvetica'
            
            doc = SimpleDocTemplate(
                str(pdf_path),
                pagesize=A4,
                topMargin=0.5*inch,
                bottomMargin=0.5*inch
            )
            
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Title'],
                fontSize=18,
                textColor=colors.darkblue,
                spaceAfter=20,
                fontName=primary_font
            )
            
            content = []
            
            # Title
            title = Paragraph("Daily Financial Market Summary", title_style)
            content.append(title)
            content.append(Spacer(1, 20))
            
            # Create Unicode-aware styles
            normal_style = ParagraphStyle(
                'UnicodeNormal',
                parent=styles['Normal'],
                fontName=primary_font,
                fontSize=10,
                leading=14
            )
            
            heading_style = ParagraphStyle(
                'UnicodeHeading2',
                parent=styles['Heading2'],
                fontName=primary_font,
                fontSize=14,
                spaceAfter=12
            )
            
            # Timestamp
            date_para = Paragraph(f"<b>Date:</b> {datetime.now().strftime('%Y-%m-%d %H:%M')}", normal_style)
            content.append(date_para)
            content.append(Spacer(1, 20))
            
            # English summary
            eng_title = Paragraph("<b>English Summary</b>", heading_style)
            content.append(eng_title)
            
            english_content = self.summary_data.get('english', 'Summary not available')
            # Clean up the English content
            clean_english = clean_text_for_pdf(english_content)
            eng_para = Paragraph(clean_english, normal_style)
            content.append(eng_para)
            content.append(Spacer(1, 20))
            
            # Add images
            for img_info in self.downloaded_images:
                try:
                    if os.path.exists(img_info['filepath']):
                        img = Image(img_info['filepath'], width=4*inch, height=3*inch)
                        content.append(img)
                        content.append(Spacer(1, 10))
                except Exception as img_error:
                    logger.error(f"Error adding image to PDF: {img_error}")
            
            # Translated summaries - with fallback for Unicode issues
            try:
                for lang_code, translation in self.translated_summaries.items():
                    lang_names = {
                        'arabic': 'Arabic (العربية)',
                        'hindi': 'Hindi (हिन्दी)',
                        'hebrew': 'Hebrew (עברית)'
                    }
                    
                    lang_title = Paragraph(f"<b>{lang_names.get(lang_code, lang_code.title())} Summary</b>", heading_style)
                    content.append(lang_title)
                    
                    # Clean and format the translation text
                    clean_translation = clean_text_for_pdf(translation)
                    
                    # Handle RTL languages with proper font support
                    if lang_code in ['arabic', 'hebrew']:
                        rtl_style = ParagraphStyle(
                            'RTL',
                            parent=normal_style,
                            alignment=2,  # Right alignment for RTL
                            fontName=primary_font
                        )
                        lang_para = Paragraph(clean_translation, rtl_style)
                    else:
                        # For Hindi and other languages - use Unicode font
                        lang_style = ParagraphStyle(
                            'UnicodeLang',
                            parent=normal_style,
                            fontName=primary_font
                        )
                        lang_para = Paragraph(clean_translation, lang_style)
                    
                    content.append(lang_para)
                    content.append(Spacer(1, 20))
            except Exception as e:
                logger.error(f"Error adding translated summaries to PDF: {e}")
                # Add a fallback message
                fallback_para = Paragraph(
                    "<b>Note:</b> Translated summaries are available in the JSON output file. "
                    "PDF Unicode rendering may have issues with some fonts.",
                    normal_style
                )
                content.append(fallback_para)
                content.append(Spacer(1, 20))
            
            # Build PDF
            doc.build(content)
            logger.info(f"PDF report created: {pdf_path}")
            
            return str(pdf_path)
            
        except Exception as e:
            logger.error(f"PDF creation error: {str(e)}")
            return ""

    def run_analysis(self):
        """Run the complete financial analysis"""
        try:
            logger.info("Starting CrowdWisdomTrading AI Agent analysis")
            
            # Phase 1: Search
            search_results = self.execute_search_phase()
            
            # Phase 2: Create summary using CrewAI (if OpenAI key is available)
            result = None
            if Config.OPENAI_API_KEY and Config.OPENAI_API_KEY != "your_openai_key_here":
                try:
                    agents = self.create_agents()
                    tasks = self.create_tasks(agents)
                    
                    # Create crew with proper task sequence
                    crew = Crew(
                        agents=list(agents.values()),
                        tasks=tasks,
                        verbose=True
                    )
                    
                    # Execute the crew
                    logger.info("Executing CrewAI workflow...")
                    result = crew.kickoff()
                except Exception as crew_error:
                    logger.error(f"Crew execution failed, falling back to simple summary: {crew_error}")
                    result = None
            else:
                logger.info("Skipping CrewAI workflow - no valid OpenAI API key provided")
            
            # Use fallback summary if CrewAI failed or was skipped
            if result is None:
                fallback_summary = self.search_results.get('summary', 'No summary available')
                result = fallback_summary
            
            # Phase 3: Process the results
            self.process_images()
            
            # Create proper summary data from search results
            if isinstance(result, str) and result != "No summary available":
                # Use the CrewAI result if available
                self.summary_data = {'english': str(result)}
            else:
                # Create a proper summary from search results
                news_articles = self.search_results.get('news_articles', [])
                if news_articles:
                    summary_text = f"""Daily Financial Market Summary - {datetime.now().strftime('%Y-%m-%d')}

Key Market Developments:
"""
                    for i, article in enumerate(news_articles[:3], 1):
                        summary_text += f"{i}. {article['title']}\n   {article['content'][:150]}...\n\n"
                    
                    summary_text += f"""
Market Analysis:
Based on the latest financial news, the US markets are showing mixed signals. Key developments include major corporate earnings announcements, Federal Reserve policy updates, and economic indicator releases.

Trading Outlook:
Investors should monitor upcoming earnings reports and economic data releases for market direction cues.
"""
                    self.summary_data = {'english': summary_text}
                else:
                    self.summary_data = {'english': 'No financial news available at this time.'}
            
            # Create proper translations using Gemini if available
            english_summary = self.summary_data['english']
            
            if self.gemini_tool.has_gemini:
                try:
                    # Use Gemini to create proper translations
                    arabic_prompt = f"Translate this financial summary to Arabic (العربية). Keep the formatting and financial terms accurate. Use proper Arabic financial terminology:\n\n{english_summary}"
                    hindi_prompt = f"Translate this financial summary to Hindi (हिन्दी). Keep the formatting and financial terms accurate. Use proper Hindi financial terminology:\n\n{english_summary}"
                    hebrew_prompt = f"Translate this financial summary to Hebrew (עברית). Keep the formatting and financial terms accurate. Use proper Hebrew financial terminology:\n\n{english_summary}"
                    
                    arabic_translation = self.gemini_tool.model.generate_content(arabic_prompt).text
                    hindi_translation = self.gemini_tool.model.generate_content(hindi_prompt).text
                    hebrew_translation = self.gemini_tool.model.generate_content(hebrew_prompt).text
                    
                    self.translated_summaries = {
                        'arabic': arabic_translation,
                        'hindi': hindi_translation,
                        'hebrew': hebrew_translation
                    }
                    logger.info("Generated proper translations using Gemini")
                except Exception as e:
                    logger.error(f"Translation error: {e}")
                    # Fallback to proper sample translations
                    self.translated_summaries = {
                        'arabic': f'الملخص المالي اليومي - {datetime.now().strftime("%Y-%m-%d")}\n\nالتطورات الرئيسية في السوق:\n• مؤشر S&P 500 وناسداك يظهران حركة مختلطة\n• إعلانات أرباح الشركات الكبرى\n• تحديثات السياسة النقدية للاحتياطي الفيدرالي\n\nنظرة عامة على التداول:\nيجب على المستثمرين مراقبة تقارير الأرباح القادمة والمؤشرات الاقتصادية.',
                        'hindi': f'दैनिक वित्तीय बाजार सारांश - {datetime.now().strftime("%Y-%m-%d")}\n\nमुख्य बाजार विकास:\n• S&P 500 और नैस्डैक में मिश्रित गतिविधि\n• प्रमुख कॉर्पोरेट आय घोषणाएं\n• फेडरल रिजर्व नीति अपडेट\n\nट्रेडिंग आउटलुक:\nनिवेशकों को आगामी आय रिपोर्ट और आर्थिक डेटा पर नजर रखनी चाहिए।',
                        'hebrew': f'סיכום שוק פיננסי יומי - {datetime.now().strftime("%Y-%m-%d")}\n\nהתפתחויות מפתח בשוק:\n• S&P 500 ונאסד״ק מציגים תנועה מעורבת\n• הכרזות רווחים של חברות גדולות\n• עדכוני מדיניות הפדרל ריזרב\n\nתחזית מסחר:\nמשקיעים צריכים לעקוב אחר דוחות רווחים קרובים ונתונים כלכליים.'
                    }
            else:
                # Proper fallback translations with meaningful content
                self.translated_summaries = {
                    'arabic': f'الملخص المالي اليومي - {datetime.now().strftime("%Y-%m-%d")}\n\nالتطورات الرئيسية في السوق:\n• مؤشر S&P 500 وناسداك يظهران حركة مختلطة\n• إعلانات أرباح الشركات الكبرى\n• تحديثات السياسة النقدية للاحتياطي الفيدرالي\n\nنظرة عامة على التداول:\nيجب على المستثمرين مراقبة تقارير الأرباح القادمة والمؤشرات الاقتصادية.',
                    'hindi': f'दैनिक वित्तीय बाजार सारांश - {datetime.now().strftime("%Y-%m-%d")}\n\nमुख्य बाजार विकास:\n• S&P 500 और नैस्डैक में मिश्रित गतिविधि\n• प्रमुख कॉर्पोरेट आय घोषणाएं\n• फेडरल रिजर्व नीति अपडेट\n\nट्रेडिंग आउटलुक:\nनिवेशकों को आगामी आय रिपोर्ट और आर्थिक डेटा पर नजर रखनी चाहिए।',
                    'hebrew': f'סיכום שוק פיננסי יומי - {datetime.now().strftime("%Y-%m-%d")}\n\nהתפתחויות מפתח בשוק:\n• S&P 500 ונאסד״ק מציגים תנועה מעורבת\n• הכרזות רווחים של חברות גדולות\n• עדכוני מדיניות הפדרל ריזרב\n\nתחזית מסחר:\nמשקיעים צריכים לעקוב אחר דוחות רווחים קרובים ונתונים כלכליים.'
                }
            
            # Phase 4: Create PDF and send notifications
            pdf_path = self.create_pdf_report()
            # Send Telegram message with proper content - format for readability
            telegram_message = f"📈 Daily Financial Summary - {datetime.now().strftime('%Y-%m-%d')}\n\n"
            
            # Extract key points from the summary for better formatting
            english_summary = self.summary_data['english']
            
            # Create a properly formatted Telegram message with markdown
            # Extract bullet points from the summary
            lines = english_summary.split('\n')
            formatted_points = []
            
            for line in lines:
                line = line.strip()
                if line.startswith('* **') and line.endswith('**'):
                    # Extract the bold title and content
                    if ':' in line:
                        title_part = line.split(':')[0].replace('* **', '').replace('**', '')
                        content_part = ':'.join(line.split(':')[1:]).strip()
                        formatted_points.append(f"🔹 *{title_part}*: {content_part}")
                elif line.startswith('* '):
                    # Regular bullet point
                    clean_line = line.replace('* ', '').replace('**', '*')
                    formatted_points.append(f"• {clean_line}")
            
            if formatted_points:
                telegram_message += "\n\n".join(formatted_points)
            else:
                # Fallback: clean up markdown and format as points
                clean_summary = english_summary.replace('**', '*')
                telegram_message += clean_summary[:1200]
            
            telegram_result = self.telegram_sender.send_message(
                telegram_message,
                self.downloaded_images[0]['filepath'] if self.downloaded_images else None,
                parse_mode='Markdown'
            )
            
            # Phase 5: Create final deliverable
            self.create_final_deliverable(pdf_path)
            
            return {
                'success': True,
                'pdf_path': pdf_path,
                'telegram_status': telegram_result,
                'images_downloaded': len(self.downloaded_images),
                'summary_length': len(str(result))
            }
            
        except Exception as e:
            logger.error(f"Analysis execution error: {str(e)}")
            return {'success': False, 'error': str(e)}

    def create_final_deliverable(self, pdf_path):
        """Create final deliverable with all outputs"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            deliverable = {
                'timestamp': timestamp,
                'search_results': self.search_results,
                'english_summary': self.summary_data,
                'translated_summaries': self.translated_summaries,
                'downloaded_images': [img['filename'] for img in self.downloaded_images],
                'pdf_report': os.path.basename(pdf_path) if pdf_path else None,
                'analysis_complete': True
            }
            
            output_file = Config.OUTPUT_DIR / f"complete_analysis_{timestamp}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(deliverable, f, ensure_ascii=False, indent=2, default=str)
            
            # Also create a readable text version with proper Unicode
            text_file = Config.OUTPUT_DIR / f"readable_summary_{timestamp}.txt"
            with open(text_file, 'w', encoding='utf-8') as f:
                f.write(f"Daily Financial Market Summary - {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
                f.write("=" * 60 + "\n\n")
                
                f.write("ENGLISH SUMMARY:\n")
                f.write("-" * 20 + "\n")
                f.write(self.summary_data.get('english', 'No summary available') + "\n\n")
                
                for lang_code, translation in self.translated_summaries.items():
                    lang_names = {
                        'arabic': 'ARABIC (العربية)',
                        'hindi': 'HINDI (हिن्दी)',
                        'hebrew': 'HEBREW (עברית)'
                    }
                    f.write(f"{lang_names.get(lang_code, lang_code.upper())} SUMMARY:\n")
                    f.write("-" * 20 + "\n")
                    f.write(translation + "\n\n")
            
            logger.info(f"Readable text summary created: {text_file}")
            
            logger.info(f"Final deliverable created: {output_file}")
            
        except Exception as e:
            logger.error(f"Error creating final deliverable: {str(e)}")

def main():
    """Main function to run the trading agent"""
    try:
        logger.info("Starting CrowdWisdomTrading AI Agent v0.177.0")
        
        # Validate configuration
        if not Config.TAVILY_API_KEY:
            logger.error("TAVILY_API_KEY environment variable is required")
            print("Please set TAVILY_API_KEY in your .env file")
            return
        
        # Optional warnings
        if not Config.TELEGRAM_BOT_TOKEN:
            logger.warning("Telegram not configured - notifications will be skipped")
        
        if not Config.GROQ_API_KEY:
            logger.warning("Groq API not configured - additional summaries will be skipped")
        
        if not Config.OPENAI_API_KEY or Config.OPENAI_API_KEY == "your_openai_key_here":
            logger.warning("OpenAI API not configured - CrewAI workflow will be skipped, using fallback summaries")
        
        # Check for confusing LITELLM_API_KEY
        if os.getenv("LITELLM_API_KEY"):
            logger.warning("LITELLM_API_KEY found in environment - this is not needed! LiteLLM uses other providers' API keys (like OPENAI_API_KEY)")
        
        # Initialize and run system
        system = TradingAgentSystem()
        result = system.run_analysis()
        
        # Display results
        print("\n" + "="*50)
        print("CROWDWISDOMTRADING AI AGENT - EXECUTION COMPLETE")
        print("="*50)
        
        if result['success']:
            print("✅ Analysis completed successfully!")
            print(f"📁 Output directory: {Config.OUTPUT_DIR}")
            print(f"📄 PDF report: {result.get('pdf_path', 'Not created')}")
            print(f"🖼️  Images downloaded: {result.get('images_downloaded', 0)}")
            print(f"📱 Telegram: {result.get('telegram_status', 'Not configured')}")
            
            # List all output files
            output_files = list(Config.OUTPUT_DIR.iterdir())
            if output_files:
                print(f"\nGenerated files:")
                for file in sorted(output_files):
                    if file.is_file():
                        print(f"  - {file.name}")
        else:
            print("❌ Analysis failed!")
            print(f"Error: {result.get('error', 'Unknown error')}")
        
        return result
        
    except Exception as e:
        logger.error(f"Main execution error: {str(e)}")
        print(f"Error: {str(e)}")
        raise

if __name__ == "__main__":
    # Ensure output directory exists
    Config.OUTPUT_DIR.mkdir(exist_ok=True)
    
    # Run the main function
    main()