import Writer.Config
import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, PageBreak, Paragraph
from reportlab.lib.units import inch
from reportlab.rl_config import defaultPageSize
from reportlab.pdfgen import canvas
from Writer.MarkdownProcessor import MarkdownProcessor
from Writer.PDFStyles import get_pdf_styles


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


def _create_readable_document(output_path):
    """
    Create SimpleDocTemplate with improved margins for readability.

    Args:
        output_path: Path for the PDF output file

    Returns:
        SimpleDocTemplate: Configured document with readable margins
    """
    return SimpleDocTemplate(
        output_path,
        pagesize=letter,
        rightMargin=Writer.Config.PDF_MARGIN_RIGHT,
        leftMargin=Writer.Config.PDF_MARGIN_LEFT,
        topMargin=Writer.Config.PDF_MARGIN_TOP,
        bottomMargin=Writer.Config.PDF_MARGIN_BOTTOM
    )


def _format_chapter_title(chapter_num, chapter_title):
    """
    Format chapter title with proper numbering and title display.

    Args:
        chapter_num: Chapter number as string
        chapter_title: Chapter title text (may be empty or include "Chapter X")

    Returns:
        str: Formatted chapter title like "Chapter 1: The Adventure Begins"
    """
    formatted_title = f"Chapter {chapter_num}"

    # Only add colon and title if title exists and doesn't already contain "Chapter X"
    if chapter_title and not chapter_title.startswith(f"Chapter {chapter_num}"):
        formatted_title = f"Chapter {chapter_num}: {chapter_title}"

    return formatted_title


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
    Generate PDF from markdown content using reportlab and MarkdownProcessor

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

        # Create PDF document with improved margins for readability
        doc = _create_readable_document(OutputPath)

        # Get centralized PDF styles
        pdf_styles = get_pdf_styles()
        font_family = pdf_styles['font_family']
        chapter_style = pdf_styles['chapter']

        # Initialize MarkdownProcessor with centralized styles
        processor = MarkdownProcessor(pdf_styles)

        story = []

        # Process content with MarkdownProcessor
        lines = story_content.split('\n')
        current_chapter = []
        chapter_num = 0
        title_processed = False

        for line in lines:
            # Title page
            if line.startswith('# ') and not title_processed:
                # Add title page using MarkdownProcessor
                title_elements = processor.create_title_page(
                    line[2:].strip(),
                    font_family,
                    Writer.Config.PDF_TITLE_SIZE
                )
                story.extend(title_elements)
                title_processed = True
                continue

            # Chapter headings
            if line.startswith('## ') and not line.startswith('## Summary') and not line.startswith('## Tags'):
                # Save previous chapter content using MarkdownProcessor
                if current_chapter:
                    chapter_text = '\n'.join(current_chapter).strip()
                    if chapter_text:
                        chapter_elements = processor.process_content(chapter_text)
                        story.extend(chapter_elements)

                # Process new chapter title
                chapter_num += 1
                ch_num, ch_title = processor.process_chapter_title(line)

                # Start chapters on new pages (except first chapter - title page already has PageBreak)
                if chapter_num > 1:
                    story.append(PageBreak())  # New page for subsequent chapters

                # Add chapter header with proper formatting
                formatted_title = _format_chapter_title(ch_num, ch_title)
                story.append(Paragraph(formatted_title, chapter_style))
                current_chapter = []
            # Story Outline section handling
            elif line.startswith('# Story Outline'):
                # Save previous chapter content using MarkdownProcessor
                if current_chapter:
                    chapter_text = '\n'.join(current_chapter).strip()
                    if chapter_text:
                        chapter_elements = processor.process_content(chapter_text)
                        story.extend(chapter_elements)
                    current_chapter = []

                # Add PageBreak before Story Outline section
                story.append(PageBreak())

                # Add Story Outline header with different styling
                story.append(Paragraph(line[2:].strip(), chapter_style))
            # Generation Statistics section handling
            elif line.startswith('# Generation Statistics'):
                # Save previous chapter content using MarkdownProcessor
                if current_chapter:
                    chapter_text = '\n'.join(current_chapter).strip()
                    if chapter_text:
                        chapter_elements = processor.process_content(chapter_text)
                        story.extend(chapter_elements)
                    current_chapter = []

                # Add Generation Statistics header (continue on same page after Story Outline)
                story.append(Paragraph(line[2:].strip(), chapter_style))
            else:
                # Add ALL lines including empty ones for paragraph breaks
                current_chapter.append(line)

        # Add final chapter content
        if current_chapter:
            chapter_text = '\n'.join(current_chapter).strip()
            if chapter_text:
                chapter_elements = processor.process_content(chapter_text)
                story.extend(chapter_elements)

        # Build PDF with page numbers
        doc.build(story, canvasmaker=NumberedCanvas)

        _Logger.Log(f"PDFGenerator: Successfully generated PDF at {OutputPath}", 5)
        return True, f"PDF generated successfully at {OutputPath}"

    except Exception as e:
        error_msg = f"PDF generation failed: {str(e)}"
        _Logger.Log(f"PDFGenerator: {error_msg}", 7)
        return False, error_msg
