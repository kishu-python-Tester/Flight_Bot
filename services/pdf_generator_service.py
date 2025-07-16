import os
import tempfile
from datetime import datetime
from typing import Dict, Optional
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
import logging

logger = logging.getLogger(__name__)

class PDFGeneratorService:
    """Service for generating flight ticket PDFs"""
    
    def __init__(self):
        self.temp_dir = tempfile.gettempdir()
        
    def generate_ticket_pdf(self, booking_data: Dict) -> Optional[str]:
        """Generate a flight ticket PDF with booking details and office ID"""
        try:
            # Create temporary file
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"ticket_{booking_data.get('pnr', 'unknown')}_{timestamp}.pdf"
            pdf_path = os.path.join(self.temp_dir, filename)
            
            # Create PDF document
            doc = SimpleDocTemplate(pdf_path, pagesize=A4)
            story = []
            
            # Get styles
            styles = getSampleStyleSheet()
            
            # Custom styles
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                spaceAfter=30,
                alignment=TA_CENTER,
                textColor=colors.darkblue
            )
            
            header_style = ParagraphStyle(
                'CustomHeader',
                parent=styles['Heading2'],
                fontSize=16,
                spaceAfter=20,
                alignment=TA_LEFT,
                textColor=colors.darkblue
            )
            
            normal_style = ParagraphStyle(
                'CustomNormal',
                parent=styles['Normal'],
                fontSize=12,
                spaceAfter=12,
                alignment=TA_LEFT
            )
            
            # Title
            story.append(Paragraph("✈️ FLIGHT TICKET", title_style))
            story.append(Spacer(1, 20))
            
            # Ticket Header
            story.append(Paragraph("📋 BOOKING DETAILS", header_style))
            
            # Booking Information Table
            booking_info = [
                ['PNR:', booking_data.get('pnr', 'N/A')],
                ['Booking Date:', booking_data.get('booking_date', 'N/A')],
                ['Booking Time:', booking_data.get('booking_time', 'N/A')],
                ['Office ID:', booking_data.get('office_id', 'N/A')]
            ]
            
            booking_table = Table(booking_info, colWidths=[2*inch, 3*inch])
            booking_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 12),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(booking_table)
            story.append(Spacer(1, 20))
            
            # Flight Details
            story.append(Paragraph("✈️ FLIGHT DETAILS", header_style))
            
            flight_info = [
                ['Airline:', booking_data.get('airline', 'N/A')],
                ['Flight Number:', booking_data.get('flight_number', 'N/A')],
                ['Departure City:', booking_data.get('origin_city', 'N/A')],
                ['Departure Airport:', booking_data.get('origin_airport', 'N/A')],
                ['Arrival City:', booking_data.get('destination_city', 'N/A')],
                ['Arrival Airport:', booking_data.get('destination_airport', 'N/A')],
                ['Travel Date:', booking_data.get('departure_date', 'N/A')],
                ['Departure Time:', booking_data.get('departure_time', 'N/A')],
                ['Arrival Time:', booking_data.get('arrival_time', 'N/A')],
                ['Class of Service:', booking_data.get('class_of_service', 'Economy')]
            ]
            
            flight_table = Table(flight_info, colWidths=[2*inch, 3*inch])
            flight_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.lightblue),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 12),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(flight_table)
            story.append(Spacer(1, 20))
            
            # Passenger Details
            story.append(Paragraph("👤 PASSENGER DETAILS", header_style))
            
            passenger_info = [
                ['Passenger Name:', booking_data.get('passenger_name', 'N/A')],
                ['Ticket Price:', f"₹{booking_data.get('ticket_price', 0):,}"],
                ['Currency:', booking_data.get('currency', 'INR')]
            ]
            
            passenger_table = Table(passenger_info, colWidths=[2*inch, 3*inch])
            passenger_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.lightgreen),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 12),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(passenger_table)
            story.append(Spacer(1, 30))
            
            # Footer
            footer_style = ParagraphStyle(
                'Footer',
                parent=styles['Normal'],
                fontSize=10,
                alignment=TA_CENTER,
                textColor=colors.grey
            )
            
            story.append(Paragraph("🏢 Office ID: " + booking_data.get('office_id', 'N/A'), footer_style))
            story.append(Spacer(1, 10))
            story.append(Paragraph("Thank you for choosing our airline! ✈️", footer_style))
            story.append(Paragraph("This is a system-generated ticket.", footer_style))
            
            # Build PDF
            doc.build(story)
            
            logger.info(f"✅ PDF ticket generated: {pdf_path}")
            return pdf_path
            
        except Exception as e:
            logger.error(f"❌ Error generating PDF ticket: {e}")
            return None
    
    def get_ticket_file_size(self, pdf_path: str) -> int:
        """Get file size of generated PDF"""
        try:
            return os.path.getsize(pdf_path)
        except Exception:
            return 0
    
    def cleanup_ticket_file(self, pdf_path: str) -> bool:
        """Clean up generated PDF file"""
        try:
            if os.path.exists(pdf_path):
                os.remove(pdf_path)
                return True
            return False
        except Exception as e:
            logger.error(f"Error cleaning up PDF file: {e}")
            return False 