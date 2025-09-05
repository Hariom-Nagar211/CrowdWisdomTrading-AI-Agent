"""
English-Only PDF Generator for CrowdWisdomTrading AI Agent
Creates clean pointwise summary PDF without asterisks
"""

import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_LEFT, TA_CENTER
import requests

class EnglishPDFGenerator:
    """Generate clean English-only PDF with pointwise summary"""
    
    def __init__(self, output_dir: Path = Path("outputs")):
        self.output_dir = output_dir
        self.output_dir.mkdir(exist_ok=True)
        self.fonts_registered = False
        
    def register_fonts(self):
        """Register fonts for better text rendering"""
        if self.fonts_registered:
            return
            
        try:
            fonts_dir = Path("fonts")
            fonts_dir.mkdir(exist_ok=True)
            
            # Check if Noto Sans exists
            noto_path = fonts_dir / "NotoSans-Regular.ttf"
            if not noto_path.exists():
                print("📥 Downloading Noto Sans font...")
                font_url = "https://github.com/googlefonts/noto-fonts/raw/main/hinted/ttf/NotoSans/NotoSans-Regular.ttf"
                try:
                    response = requests.get(font_url, timeout=30)
                    response.raise_for_status()
                    with open(noto_path, 'wb') as f:
                        f.write(response.content)
                    print("✅ Downloaded Noto Sans font")
                except Exception as e:
                    print(f"⚠️ Could not download font: {e}")
            
            # Register the font
            if noto_path.exists():
                pdfmetrics.registerFont(TTFont('NotoSans', str(noto_path)))
                print("✅ Registered Noto Sans font")
                self.fonts_registered = True
            else:
                print("⚠️ Using default font")
                
        except Exception as e:
            print(f"⚠️ Font registration error: {e}")
    
    def parse_english_content(self, content: str) -> Dict[str, Any]:
        """Parse and extract English content from text file"""
        sections = {'english': [], 'date': ''}
        
        # Extract date from first line
        lines = content.split('\n')
        if lines and 'Daily Financial Market Summary' in lines[0]:
            date_part = lines[0].split(' - ')[-1] if ' - ' in lines[0] else ''
            sections['date'] = date_part
        
        # Find English section
        in_english_section = False
        
        for line in lines:
            line = line.strip()
            
            if 'ENGLISH SUMMARY:' in line:
                in_english_section = True
                continue
            elif any(lang in line for lang in ['ARABIC', 'HINDI', 'HEBREW']) and 'SUMMARY:' in line:
                in_english_section = False
                continue
            elif line.startswith('----') or line.startswith('====') or not line:
                continue
            elif in_english_section and line:
                # Clean the line - properly decode markdown formatting
                clean_line = self.clean_markdown(line)
                if clean_line:
                    sections['english'].append(clean_line)
        
        return sections
    
    def clean_markdown(self, text: str) -> str:
        """Remove markdown formatting from text"""
        if not text.strip():
            return ""
        
        # Remove leading asterisks and spaces
        clean_text = text.strip()
        
        # Remove bullet point asterisks at the beginning
        while clean_text.startswith('*'):
            clean_text = clean_text[1:].strip()
        
        # Remove bold markdown (**text**)
        import re
        clean_text = re.sub(r'\*\*(.*?)\*\*', r'\1', clean_text)
        
        # Remove any remaining single asterisks
        clean_text = clean_text.replace('*', '')
        
        # Clean up extra spaces
        clean_text = ' '.join(clean_text.split())
        
        return clean_text.strip()
    
    def create_english_pdf(self, txt_file_path: str, images: List[str] = None) -> str:
        """Create clean English PDF"""
        try:
            # Register fonts
            self.register_fonts()
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            pdf_filename = f"english_financial_report_{timestamp}.pdf"
            pdf_path = self.output_dir / pdf_filename
            
            # Read and parse text file
            with open(txt_file_path, 'r', encoding='utf-8') as f:
                content_text = f.read()
            
            sections = self.parse_english_content(content_text)
            date = sections.get('date', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            
            # Create PDF document
            doc = SimpleDocTemplate(str(pdf_path), pagesize=A4, 
                                  rightMargin=72, leftMargin=72, 
                                  topMargin=72, bottomMargin=72)
            
            # Build story (content)
            story = []
            
            # Styles
            styles = getSampleStyleSheet()
            
            # Custom styles
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                spaceAfter=20,
                textColor=HexColor('#2c5aa0'),
                alignment=TA_CENTER,
                fontName='NotoSans-Bold' if self.fonts_registered else 'Helvetica-Bold'
            )
            
            subtitle_style = ParagraphStyle(
                'CustomSubtitle',
                parent=styles['Heading2'],
                fontSize=18,
                spaceAfter=15,
                textColor=HexColor('#2c5aa0'),
                alignment=TA_CENTER,
                fontName='NotoSans' if self.fonts_registered else 'Helvetica-Bold'
            )
            
            meta_style = ParagraphStyle(
                'MetaStyle',
                parent=styles['Normal'],
                fontSize=11,
                spaceAfter=8,
                textColor=HexColor('#666666'),
                fontName='NotoSans' if self.fonts_registered else 'Helvetica'
            )
            
            point_style = ParagraphStyle(
                'PointStyle',
                parent=styles['Normal'],
                fontSize=12,
                spaceAfter=12,
                leftIndent=20,
                bulletIndent=10,
                fontName='NotoSans' if self.fonts_registered else 'Helvetica',
                alignment=TA_LEFT
            )
            
            # Title
            story.append(Paragraph("📈 CrowdWisdomTrading AI Agent", title_style))
            story.append(Paragraph("Daily Financial Market Analysis", subtitle_style))
            story.append(Spacer(1, 30))
            
            # Meta information box
            meta_info = [
                f"<b>Report Date:</b> {date}",
                "<b>Analysis Type:</b> English Financial Summary",
                "<b>Data Sources:</b> Tavily Financial News API",
                "<b>Generated By:</b> CrowdWisdomTrading AI Agent v0.177.0"
            ]
            
            for info in meta_info:
                story.append(Paragraph(info, meta_style))
            
            story.append(Spacer(1, 30))
            
            # Add images if available
            if images:
                story.append(Paragraph("📊 Market Charts & Visualizations", subtitle_style))
                story.append(Spacer(1, 15))
                
                for i, img_path in enumerate(images[:2]):
                    if os.path.exists(img_path):
                        try:
                            # Add image with proper sizing
                            img = Image(img_path, width=6*inch, height=3.5*inch)
                            story.append(img)
                            
                            # Add caption
                            caption_style = ParagraphStyle(
                                'Caption',
                                parent=styles['Normal'],
                                fontSize=10,
                                spaceAfter=20,
                                alignment=TA_CENTER,
                                textColor=HexColor('#666666'),
                                fontName='NotoSans' if self.fonts_registered else 'Helvetica'
                            )
                            story.append(Paragraph(f"Figure {i+1}: Financial Market Chart", caption_style))
                            
                        except Exception as e:
                            print(f"⚠️ Error adding image {img_path}: {e}")
                
                story.append(Spacer(1, 25))
            
            # Market Summary Header
            story.append(Paragraph("📋 Market Summary", subtitle_style))
            story.append(Spacer(1, 20))
            
            # Add content points
            if sections['english']:
                point_number = 1
                for content_line in sections['english']:
                    if content_line.strip():
                        # Content is already cleaned by clean_markdown method
                        clean_point = content_line.strip()
                        
                        # Add numbering
                        formatted_point = f"{point_number}. {clean_point}"
                        
                        story.append(Paragraph(formatted_point, point_style))
                        point_number += 1
            else:
                story.append(Paragraph("No English summary content available.", point_style))
            
            story.append(Spacer(1, 40))
            
            # Disclaimer
            disclaimer_style = ParagraphStyle(
                'Disclaimer',
                parent=styles['Normal'],
                fontSize=10,
                spaceAfter=12,
                leftIndent=20,
                rightIndent=20,
                textColor=HexColor('#666666'),
                fontName='NotoSans' if self.fonts_registered else 'Helvetica'
            )
            
            story.append(Paragraph("<b>⚠️ Disclaimer</b>", disclaimer_style))
            disclaimer_text = """This report is generated by an AI system for informational purposes only. It should not be considered as financial advice. Always consult with qualified financial professionals before making investment decisions. Market data and analysis are based on publicly available information and may not reflect real-time market conditions."""
            
            story.append(Paragraph(disclaimer_text, disclaimer_style))
            
            # Build PDF
            doc.build(story)
            
            print(f"✅ English PDF created: {pdf_filename}")
            return str(pdf_path)
            
        except Exception as e:
            print(f"❌ Error creating English PDF: {e}")
            return ""

def create_english_report():
    """Create English PDF report from latest readable text file"""
    try:
        output_dir = Path("outputs")
        
        # Find latest readable summary file
        txt_files = list(output_dir.glob("readable_summary_*.txt"))
        if not txt_files:
            print("❌ No readable summary files found")
            return None
        
        latest_txt_file = max(txt_files, key=lambda x: x.stat().st_mtime)
        print(f"📖 Using text file: {latest_txt_file.name}")
        
        # Find latest images
        image_files = list(output_dir.glob("financial_chart_*.png"))
        latest_images = sorted(image_files, key=lambda x: x.stat().st_mtime, reverse=True)[:2]
        image_paths = [str(img) for img in latest_images]
        
        print(f"🖼️ Found {len(image_paths)} images to include")
        
        # Create English PDF
        generator = EnglishPDFGenerator(output_dir)
        pdf_path = generator.create_english_pdf(str(latest_txt_file), image_paths)
        
        if pdf_path:
            print(f"🎉 English PDF report created successfully!")
            print(f"📄 Location: {pdf_path}")
            return pdf_path
        else:
            print("❌ Failed to create English PDF")
            return None
            
    except Exception as e:
        print(f"❌ Error creating English report: {e}")
        return None

if __name__ == "__main__":
    create_english_report()
