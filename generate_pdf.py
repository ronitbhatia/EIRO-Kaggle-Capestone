"""
Script to convert WRITEUP.md to PDF using reportlab
"""

import os
import sys
import re
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Preformatted
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.lib.colors import HexColor

def clean_markdown(text):
    """Remove markdown formatting for plain text"""
    # Remove bold
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    # Remove inline code
    text = re.sub(r'`(.+?)`', r'\1', text)
    return text

def markdown_to_html(text):
    """Convert markdown to HTML for reportlab"""
    # Bold
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
    # Inline code
    text = re.sub(r'`([^`]+)`', r'<font face="Courier" size="9">\1</font>', text)
    # Escape HTML
    text = text.replace('&', '&amp;')
    text = text.replace('<', '&lt;')
    text = text.replace('>', '&gt;')
    # Restore our HTML tags
    text = re.sub(r'&lt;(b|font)([^&]*)&gt;', r'<\1\2>', text)
    text = re.sub(r'&lt;/(b|font)&gt;', r'</\1>', text)
    return text

def convert_markdown_to_pdf(md_path, pdf_path):
    """Convert markdown file to PDF"""
    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Create PDF document
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=letter,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=72
    )
    
    # Define styles
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=HexColor('#2c3e50'),
        spaceAfter=20,
        spaceBefore=0,
        alignment=TA_LEFT,
        fontName='Helvetica-Bold'
    )
    
    subtitle_style = ParagraphStyle(
        'Subtitle',
        parent=styles['Normal'],
        fontSize=14,
        textColor=HexColor('#7f8c8d'),
        spaceAfter=30,
        alignment=TA_LEFT,
        fontName='Helvetica-Oblique'
    )
    
    h1_style = ParagraphStyle(
        'H1',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=HexColor('#34495e'),
        spaceAfter=12,
        spaceBefore=24,
        alignment=TA_LEFT,
        fontName='Helvetica-Bold'
    )
    
    h2_style = ParagraphStyle(
        'H2',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=HexColor('#555'),
        spaceAfter=10,
        spaceBefore=18,
        alignment=TA_LEFT,
        fontName='Helvetica-Bold'
    )
    
    h3_style = ParagraphStyle(
        'H3',
        parent=styles['Heading3'],
        fontSize=12,
        textColor=HexColor('#666'),
        spaceAfter=8,
        spaceBefore=12,
        alignment=TA_LEFT,
        fontName='Helvetica-Bold'
    )
    
    normal_style = ParagraphStyle(
        'Normal',
        parent=styles['Normal'],
        fontSize=11,
        spaceAfter=8,
        alignment=TA_JUSTIFY,
        fontName='Helvetica'
    )
    
    code_style = ParagraphStyle(
        'Code',
        parent=styles['Code'],
        fontSize=9,
        fontName='Courier',
        leftIndent=20,
        rightIndent=20,
        spaceAfter=12,
        backColor=HexColor('#f5f5f5'),
        borderColor=HexColor('#ddd'),
        borderWidth=1,
        borderPadding=10
    )
    
    story = []
    lines = content.split('\n')
    i = 0
    in_code_block = False
    code_lines = []
    
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        
        # Handle code blocks
        if stripped.startswith('```'):
            if in_code_block:
                # End of code block
                code_text = '\n'.join(code_lines)
                story.append(Preformatted(code_text, code_style))
                story.append(Spacer(1, 12))
                code_lines = []
                in_code_block = False
            else:
                # Start of code block
                in_code_block = True
            i += 1
            continue
        
        if in_code_block:
            code_lines.append(line)
            i += 1
            continue
        
        # Empty lines
        if not stripped:
            story.append(Spacer(1, 6))
            i += 1
            continue
        
        # Headers
        if stripped.startswith('# '):
            text = markdown_to_html(stripped[2:].strip())
            story.append(Paragraph(text, title_style))
            story.append(Spacer(1, 12))
        elif stripped.startswith('## '):
            text = markdown_to_html(stripped[3:].strip())
            story.append(Paragraph(text, h1_style))
            story.append(Spacer(1, 10))
        elif stripped.startswith('### '):
            text = markdown_to_html(stripped[4:].strip())
            story.append(Paragraph(text, h2_style))
            story.append(Spacer(1, 8))
        elif stripped.startswith('#### '):
            text = markdown_to_html(stripped[5:].strip())
            story.append(Paragraph(text, h3_style))
            story.append(Spacer(1, 6))
        # List items
        elif stripped.startswith('- ') or stripped.startswith('* '):
            text = markdown_to_html(stripped[2:].strip())
            # Use bullet
            story.append(Paragraph(f'&bull; {text}', normal_style))
            story.append(Spacer(1, 4))
        elif re.match(r'^\d+\.\s+', stripped):
            text = markdown_to_html(re.sub(r'^\d+\.\s+', '', stripped))
            story.append(Paragraph(text, normal_style))
            story.append(Spacer(1, 4))
        # Regular text
        else:
            text = markdown_to_html(stripped)
            if text.strip():
                story.append(Paragraph(text, normal_style))
                story.append(Spacer(1, 6))
        
        i += 1
    
    # Build PDF
    doc.build(story)
    print(f"PDF generated successfully: {pdf_path}")

def main():
    writeup_path = "WRITEUP.md"
    output_path = "WRITEUP.pdf"
    
    if not os.path.exists(writeup_path):
        print(f"Error: {writeup_path} not found")
        sys.exit(1)
    
    try:
        convert_markdown_to_pdf(writeup_path, output_path)
        print(f"\nSuccess! PDF saved as: {output_path}")
    except Exception as e:
        print(f"Error generating PDF: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
