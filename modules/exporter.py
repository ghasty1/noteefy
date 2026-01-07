import markdown
from xhtml2pdf import pisa
import os

class Exporter:
    def __init__(self):
        pass

    def export_to_pdf(self, markdown_text, output_filename):
        """
        Converts markdown text to a PDF file.
        """
        print(f"Exporting to PDF: {output_filename}...")

        # 1. Convert Markdown to HTML
        html_text = markdown.markdown(
            markdown_text, 
            extensions=['tables', 'fenced_code']
        )

        # 2. Add some basic CSS for styling
        styled_html = f"""
        <html>
        <head>
            <style>
                body {{
                    font-family: Helvetica, sans-serif;
                    font-size: 12pt;
                    line-height: 1.5;
                }}
                h1 {{ color: #2E3E50; font-size: 24pt; border-bottom: 1px solid #ccc; }}
                h2 {{ color: #2E3E50; font-size: 18pt; margin-top: 20px; }}
                h3 {{ color: #2E3E50; font-size: 14pt; }}
                code {{ background-color: #f4f4f4; padding: 2px; }}
                pre {{ background-color: #f4f4f4; padding: 10px; border-radius: 5px; }}
                table {{ border-collapse: collapse; width: 100%; margin-top: 10px; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
            </style>
        </head>
        <body>
            {html_text}
        </body>
        </html>
        """

        # 3. Write HTML to PDF
        try:
            with open(output_filename, "wb") as pdf_file:
                pisa_status = pisa.CreatePDF(
                    src=styled_html, 
                    dest=pdf_file
                )

            if pisa_status.err:
                return f"Error creating PDF: {pisa_status.err}"
            
            return output_filename

        except Exception as e:
            return f"Export failed: {str(e)}"

if __name__ == "__main__":
    # Test script
    md = "# Hello World\nThis is a *test* of the PDF export.\n\n## Section 1\n- Item A\n- Item B"
    exp = Exporter()
    print(exp.export_to_pdf(md, "test_note.pdf"))
