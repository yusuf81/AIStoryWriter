import Writer.Config
import os
import re
import markdown
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, PageBreak, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.rl_config import defaultPageSize
from reportlab.pdfgen import canvas
from reportlab.lib.colors import black


class NumberedCanvas(canvas.Canvas):
    """Canvas for adding page numbers"""
    def __init__(self, *args, **kwargs):
        canvas.Canvas.__init__(self, *args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        """Add page numbers to each page and save"""
        num_pages = len(self._saved_page_states)
        for page_state in self._saved_page_states:
            self.__dict__.update(page_state)
            self.draw_page_number(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_number(self, page_count):
        """Draw page number at bottom center"""
        self.setFont("Times-Roman", 9)
        self.drawRightString(
            defaultPageSize[0] - inch,
            0.75 * inch,
            f"Page {self._pageNumber} of {page_count}"
        )


def extract_story_content(markdown_content):
    """
    Extract only story content from markdown, removing YAML front matter and metadata sections.

    Args:
        markdown_content: Full markdown content with YAML and metadata

    Returns:
        Cleaned content with only title and chapters
    """
    lines = markdown_content.split('\n')
    in_yaml = False
    in_metadata = False
    story_started = False
    cleaned_lines = []

    for line in lines:
        # Skip YAML front matter
        if line.strip() == '---' and not story_started and not in_yaml:
            in_yaml = True
            continue
        elif line.strip() == '---' and in_yaml:
            in_yaml = False
            continue
        elif in_yaml:
            continue

        # Look for the first H1 title
        if line.startswith('# ') and not story_started:
            story_started = True
            cleaned_lines.append(line)
            continue

        # Skip metadata sections
        if line.startswith('## Summary') or line.startswith('## Tags'):
            in_metadata = True
            continue
        elif line.startswith('---') and story_started and in_metadata:
            # This marks the end of metadata and start of story content
            in_metadata = False
            cleaned_lines.append(line)
            continue
        elif in_metadata:
            continue

        # Handle chapter markers
        if story_started and not in_metadata:
            cleaned_lines.append(line)

    return '\n'.join(cleaned_lines)


def GeneratePDF(Interface, _Logger, MDContent, OutputPath, Title):
    """
    Generate PDF from markdown content using reportlab

    Args:
        Interface: Interface wrapper (for compatibility, not used here)
        _Logger: Logger instance
        MDContent: Markdown content string
        OutputPath: Path to save PDF file
        Title: Story title

    Returns:
        tuple: (success: bool, message: str)
    """
    try:
        # Extract story-only content
        story_content = extract_story_content(MDContent)

        # Create output directory if needed
        os.makedirs(os.path.dirname(OutputPath), exist_ok=True)

        # Create PDF document
        doc = SimpleDocTemplate(
            OutputPath,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )

        # Get styles
        styles = getSampleStyleSheet()

        # Use standard fonts available in reportlab
        font_family = "Times-Roman"  # Always available
        if Writer.Config.PDF_FONT_FAMILY.lower() == "georgia":
            font_family = "Times-Roman"  # Georgia not available, fallback to Times

        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Title'],
            fontName=font_family,
            fontSize=Writer.Config.PDF_TITLE_SIZE,
            textColor=black,
            alignment=1,  # Center
            spaceAfter=30
        )

        chapter_style = ParagraphStyle(
            'Chapter',
            parent=styles['Heading1'],
            fontName=font_family,
            fontSize=Writer.Config.PDF_CHAPTER_SIZE,
            textColor=black,
            spaceBefore=30,
            spaceAfter=20
        )

        normal_style = ParagraphStyle(
            'Normal',
            parent=styles['Normal'],
            fontName=font_family,
            fontSize=Writer.Config.PDF_FONT_SIZE,
            textColor=black,
            spaceAfter=12
        )

        story = []

        # Parse markdown and extract chapters
        lines = story_content.split('\n')
        current_chapter = []
        chapter_num = 0

        for line in lines:
            # Title page
            if line.startswith('# ') and chapter_num == 0:
                # Add title page
                story.append(Spacer(1, 2*inch))  # Space at top
                story.append(Paragraph(line[2:].strip(), title_style))
                story.append(Spacer(1, 1.5*inch))  # Space after title
                story.append(PageBreak())  # New page for content
                continue

            # Chapter headings
            if line.startswith('## ') and not line.startswith('## Summary') and not line.startswith('## Tags'):
                # Save previous chapter content
                if current_chapter:
                    content = '\n'.join(current_chapter).strip()
                    if content:
                        # Convert markdown to HTML, then to paragraphs
                        html = markdown.markdown(content)
                        # Convert to simple paragraphs (handle <p> and <h3> etc)
                        for para in re.split(r'\n\n+', content):
                            if para.strip():
                                if para.startswith('### '):
                                    # Chapter sections
                                    p_text = para[4:].strip()
                                    if p_text:
                                        story.append(Paragraph(p_text, chapter_style))
                                else:
                                    story.append(Paragraph(para.replace('\n', ' '), normal_style))

                # Start new chapter
                chapter_num += 1
                chapter_title = line[3:].strip()
                if chapter_num > 1:
                    story.append(PageBreak())  # New page for each chapter
                story.append(Paragraph(f"Chapter {chapter_num}", chapter_style))
                current_chapter = []
            else:
                if line.strip() and not line.strip() == '---':
                    current_chapter.append(line)

        # Add final chapter
        if current_chapter:
            content = '\n'.join(current_chapter).strip()
            if content:
                for para in re.split(r'\n\n+', content):
                    if para.strip() and not para.startswith('### '):
                        story.append(Paragraph(para.replace('\n', ' '), normal_style))

        # Build PDF with page numbers
        doc.build(story, canvasmaker=NumberedCanvas)

        _Logger.Log(f"PDFGenerator: Successfully generated PDF at {OutputPath}", 5)
        return True, f"PDF generated successfully at {OutputPath}"

    except Exception as e:
        error_msg = f"PDF generation failed: {str(e)}"
        _Logger.Log(f"PDFGenerator: {error_msg}", 7)
        return False, error_msg