#!/usr/bin/env python3
"""
Convert Flight Booking Diagrams HTML to PDF
"""

import os
import sys
import webbrowser
from pathlib import Path

def convert_html_to_pdf():
    """Convert the HTML diagrams to PDF format"""
    
    html_file = "flight_booking_diagrams.html"
    
    if not os.path.exists(html_file):
        print(f"❌ HTML file '{html_file}' not found!")
        return False
    
    print("🛫 Flight Booking Chatbot - Diagram PDF Converter")
    print("=" * 50)
    
    # Get the absolute path
    html_path = os.path.abspath(html_file)
    file_url = f"file://{html_path}"
    
    print(f"📄 HTML file located: {html_file}")
    print(f"🌐 Opening in browser: {file_url}")
    
    # Open in default browser
    webbrowser.open(file_url)
    
    print("\n📋 Instructions to Convert to PDF:")
    print("-" * 40)
    print("1. The HTML file should now be open in your browser")
    print("2. Press Ctrl+P (or Cmd+P on Mac) to open print dialog")
    print("3. Select 'Save as PDF' as the destination")
    print("4. Choose 'More settings' if needed")
    print("5. Recommended settings:")
    print("   - Paper size: A4")
    print("   - Margins: Minimum")
    print("   - Scale: Custom (80-90%)")
    print("   - Options: Background graphics ✓")
    print("6. Click 'Save' and choose filename")
    print("\n✅ Your diagrams will be saved as PDF!")
    
    # Alternative methods
    print("\n🔄 Alternative Methods:")
    print("-" * 40)
    print("Option 1: Use Chrome headless")
    print("chrome --headless --disable-gpu --print-to-pdf=diagrams.pdf flight_booking_diagrams.html")
    print("\nOption 2: Install wkhtmltopdf")
    print("pip install pdfkit")
    print("Then use: pdfkit.from_file('flight_booking_diagrams.html', 'diagrams.pdf')")
    
    return True

def install_pdf_dependencies():
    """Install required dependencies for PDF conversion"""
    print("🔧 Installing PDF conversion dependencies...")
    
    try:
        import subprocess
        
        # Try to install pdfkit and wkhtmltopdf
        subprocess.run([sys.executable, "-m", "pip", "install", "pdfkit"], check=True)
        print("✅ pdfkit installed successfully")
        
        print("\n📦 Additional requirement:")
        print("You need to install wkhtmltopdf:")
        print("- macOS: brew install wkhtmltopdf")
        print("- Ubuntu: sudo apt-get install wkhtmltopdf")
        print("- Windows: Download from https://wkhtmltopdf.org/downloads.html")
        
        return True
        
    except subprocess.CalledProcessError:
        print("❌ Failed to install dependencies")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def convert_with_pdfkit():
    """Convert using pdfkit if available"""
    try:
        import pdfkit
        
        options = {
            'page-size': 'A4',
            'margin-top': '0.5in',
            'margin-right': '0.5in',
            'margin-bottom': '0.5in',
            'margin-left': '0.5in',
            'encoding': "UTF-8",
            'no-outline': None,
            'enable-local-file-access': None
        }
        
        pdfkit.from_file('flight_booking_diagrams.html', 'flight_booking_diagrams.pdf', options=options)
        print("✅ PDF generated successfully: flight_booking_diagrams.pdf")
        return True
        
    except ImportError:
        print("❌ pdfkit not installed. Run with --install flag first.")
        return False
    except Exception as e:
        print(f"❌ Error generating PDF: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "--install":
            install_pdf_dependencies()
        elif sys.argv[1] == "--pdfkit":
            convert_with_pdfkit()
        elif sys.argv[1] == "--help":
            print("Usage:")
            print("python convert_to_pdf.py          # Open in browser for manual conversion")
            print("python convert_to_pdf.py --install  # Install PDF dependencies")
            print("python convert_to_pdf.py --pdfkit   # Auto-convert using pdfkit")
        else:
            print("Unknown option. Use --help for usage information.")
    else:
        convert_html_to_pdf() 