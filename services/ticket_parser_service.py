import logging
import tempfile
import os
from typing import Dict, Optional, List
import PyPDF2
import pdfplumber
import google.generativeai as genai
from config.settings import Config

logger = logging.getLogger(__name__)

class TicketParserService:
    def __init__(self):
        # Configure Google AI
        genai.configure(api_key=Config.GOOGLE_API_KEY)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        
    def extract_text_from_pdf(self, pdf_content: bytes) -> str:
        """Extract text from PDF using multiple methods for better accuracy"""
        extracted_text = ""
        
        try:
            # Method 1: Using pdfplumber (better for complex layouts)
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
                temp_file.write(pdf_content)
                temp_file.flush()
                
                try:
                    with pdfplumber.open(temp_file.name) as pdf:
                        for page in pdf.pages:
                            text = page.extract_text()
                            if text:
                                extracted_text += text + "\n"
                except Exception as e:
                    logger.warning(f"pdfplumber extraction failed: {e}")
                
                # Method 2: Fallback to PyPDF2 if pdfplumber fails
                if not extracted_text.strip():
                    try:
                        with open(temp_file.name, 'rb') as pdf_file:
                            pdf_reader = PyPDF2.PdfReader(pdf_file)
                            for page in pdf_reader.pages:
                                text = page.extract_text()
                                if text:
                                    extracted_text += text + "\n"
                    except Exception as e:
                        logger.warning(f"PyPDF2 extraction failed: {e}")
                
                # Clean up temp file
                os.unlink(temp_file.name)
                
        except Exception as e:
            logger.error(f"PDF text extraction failed: {e}")
            
        return extracted_text.strip()
    
    def parse_flight_ticket(self, pdf_content: bytes) -> Dict:
        """Parse flight ticket and extract detailed information using LLM"""
        
        # Extract text from PDF
        ticket_text = self.extract_text_from_pdf(pdf_content)
        
        if not ticket_text:
            return {
                "success": False,
                "error": "Could not extract text from PDF. Please ensure it's a valid flight ticket."
            }
        
        # Use LLM to parse ticket information
        return self._analyze_ticket_with_llm(ticket_text)
    
    def _analyze_ticket_with_llm(self, ticket_text: str) -> Dict:
        """Use Google Gemini to analyze and extract flight information"""
        
        system_prompt = f"""You are an expert flight ticket parser. Analyze the provided flight ticket text and extract ALL relevant flight information.

TICKET TEXT:
{ticket_text}

Extract the following information and respond ONLY with valid JSON:

{{
    "success": true,
    "flight_details": {{
        "airline": "Airline name",
        "flight_number": "Flight number (e.g., AI915, EK203)",
        "origin_city": "Departure city name",
        "origin_airport": "Departure airport code (e.g., DEL, BOM)",
        "destination_city": "Arrival city name", 
        "destination_airport": "Arrival airport code (e.g., DXB, LHR)",
        "departure_date": "YYYY-MM-DD format",
        "departure_time": "HH:MM format",
        "arrival_date": "YYYY-MM-DD format", 
        "arrival_time": "HH:MM format",
        "class_of_service": "Economy/Business/First",
        "seat_number": "Seat assignment if available",
        "booking_reference": "PNR/Booking reference",
        "passenger_name": "Primary passenger name",
        "total_passengers": "Number of passengers",
        "ticket_price": "Total price with currency (e.g., ₹45000, $500)",
        "ticket_price_numeric": "Numeric price only (e.g., 45000)",
        "currency": "Currency code (INR, USD, EUR, etc.)"
    }},
    "confidence": 0.0-1.0,
    "additional_info": {{
        "baggage_allowance": "Baggage details if available",
        "meal_preference": "Meal type if mentioned",
        "special_requests": "Any special services",
        "check_in_status": "Checked in or not",
        "gate_terminal": "Gate/Terminal info if available"
    }}
}}

IMPORTANT PARSING RULES:
1. Look for airline codes: AI (Air India), EK (Emirates), 6E (IndiGo), SG (SpiceJet), etc.
2. Airport codes are usually 3 letters: DEL, BOM, DXB, LHR, etc.  
3. Flight numbers combine airline code + numbers: AI915, EK203, 6E1745
4. Dates can be in various formats - convert to YYYY-MM-DD
5. Times are usually in 24-hour format
6. PNR/Booking reference is alphanumeric (6-10 characters usually)
7. Price can be in various currencies - extract both formatted and numeric
8. If information is not clearly available, set as null
9. Be very careful with origin/destination - don't confuse them
10. Class of service: Economy, Business, First Class, Premium Economy

If parsing fails or ticket format is unrecognizable, respond with:
{{
    "success": false,
    "error": "Unable to parse ticket. Please ensure it's a valid flight ticket with clear text."
}}"""

        try:
            response = self.model.generate_content(system_prompt)
            result_text = response.text.strip()
            
            # Clean the response - remove markdown code blocks if present
            if result_text.startswith('```json'):
                result_text = result_text.replace('```json', '').replace('```', '').strip()
            elif result_text.startswith('```'):
                result_text = result_text.replace('```', '').strip()
            
            # Parse JSON response
            import json
            result = json.loads(result_text)
            
            logger.info(f"Ticket parsing successful: {result.get('confidence', 0)}")
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"LLM response parsing error: {e}")
            return {
                "success": False,
                "error": "Failed to parse ticket information. Please try with a clearer ticket image."
            }
        except Exception as e:
            logger.error(f"Ticket analysis error: {e}")
            return {
                "success": False,
                "error": "Ticket analysis failed. Please try again or contact support."
            }
    
    def compare_prices_with_system(self, ticket_info: Dict, origin: str, destination: str, date: str) -> Dict:
        """Compare ticket price with current system prices"""
        
        if not ticket_info.get("success"):
            return {"error": "Cannot compare prices - ticket parsing failed"}
        
        try:
            # Import here to avoid circular imports
            from services.flight_service import FlightService
            
            flight_service = FlightService()
            
            # Search for flights on the same route and date
            system_flights = flight_service.search_flights(
                origin=origin,
                destination=destination, 
                date=date,
                adults=1
            )
            
            if not system_flights:
                return {
                    "comparison_available": False,
                    "message": f"No flights found in our system for route {origin} → {destination}",
                    "suggestion": f"We currently don't offer flights on the {origin} → {destination} route. You can check our available routes or search for alternative connections.",
                    "available_origins": ["DEL", "BOM", "DXB", "HYD", "LHR", "JAI"],
                    "popular_destinations": ["DXB", "LHR", "BLR", "DEL", "SIN", "BKK", "JAI", "HYD"]
                }
            
            ticket_price = ticket_info["flight_details"]["ticket_price_numeric"]
            currency = ticket_info["flight_details"]["currency"]
            
            # Find comparable flights (same airline if possible)
            airline = ticket_info["flight_details"]["airline"]
            comparable_flights = []
            
            for flight in system_flights:
                comparable_flights.append({
                    "airline": flight.airline,
                    "flight_number": flight.flight_id,  # Using flight_id from Flight model
                    "price": flight.price,
                    "is_same_airline": airline.lower() in flight.airline.lower()
                })
            
            # Find best price in our system
            best_system_price = min(flight.price for flight in system_flights)
            price_difference = ticket_price - best_system_price
            
            return {
                "comparison_available": True,
                "ticket_price": ticket_price,
                "currency": currency,
                "best_system_price": best_system_price,
                "price_difference": price_difference,
                "savings_percentage": round((price_difference / ticket_price) * 100, 1) if ticket_price > 0 else 0,
                "comparable_flights": comparable_flights,
                "recommendation": "cheaper" if price_difference > 0 else "similar" if abs(price_difference) < 500 else "expensive"
            }
            
        except Exception as e:
            logger.error(f"Price comparison error: {e}")
            return {
                "comparison_available": False,
                "error": "Unable to compare prices at this time"
            }
    
    def format_ticket_analysis_for_whatsapp(self, ticket_info: Dict, price_comparison: Optional[Dict] = None) -> str:
        """Format ticket analysis results for WhatsApp display"""
        
        if not ticket_info.get("success"):
            return f"❌ *Ticket Parsing Failed*\n\n{ticket_info.get('error', 'Unknown error occurred')}"
        
        details = ticket_info["flight_details"]
        confidence = ticket_info.get("confidence", 0)
        
        # Build main ticket info
        message = f"""✅ *Ticket Successfully Analyzed!*
📊 *Confidence:* {int(confidence * 100)}%

✈️ *Flight Details:*
🛫 *{details['airline']} {details['flight_number']}*
📍 {details['origin_city']} ({details['origin_airport']}) → {details['destination_city']} ({details['destination_airport']})
📅 {details['departure_date']} | ⏰ {details['departure_time']} - {details['arrival_time']}
🎫 *Class:* {details['class_of_service']}
👤 *Passenger:* {details['passenger_name']}
🆔 *PNR:* {details['booking_reference']}
💰 *Ticket Price:* {details['ticket_price']}"""

        # Add seat info if available
        if details.get('seat_number'):
            message += f"\n🪑 *Seat:* {details['seat_number']}"
        
        # Add price comparison if available
        if price_comparison and price_comparison.get("comparison_available"):
            comp = price_comparison
            message += f"\n\n💰 *Price Comparison:*"
            message += f"\n📋 *Your Ticket:* ₹{comp['ticket_price']:,}"
            message += f"\n🏷️ *Our Best Price:* ₹{comp['best_system_price']:,}"
            
            if comp['recommendation'] == "cheaper":
                message += f"\n💸 *You could save ₹{abs(comp['price_difference']):,}* ({comp['savings_percentage']}%)"
                message += f"\n✨ *Good news!* Our system has cheaper options available."
            elif comp['recommendation'] == "similar":
                message += f"\n✅ *Great choice!* Your price is competitive (±₹{abs(comp['price_difference']):,})"
            else:
                message += f"\n💰 *Your ticket cost ₹{abs(comp['price_difference']):,} more than our best price*"
        elif price_comparison and not price_comparison.get("comparison_available"):
            # Handle route not available case
            message += f"\n\n🗺️ *Route Information:*"
            message += f"\n📍 *Your Route:* {details['origin_city']} → {details['destination_city']}"
            if price_comparison.get("suggestion"):
                message += f"\n💡 *Note:* {price_comparison['suggestion']}"
            
            # Show available routes if provided
            if price_comparison.get("available_origins"):
                origins = ", ".join(price_comparison['available_origins'])
                message += f"\n✈️ *We offer flights from:* {origins}"
        
        # Add booking options
        message += f"\n\n🔄 *What would you like to do?*"
        message += f"\n• Type '*search similar*' to find flights on this route"
        message += f"\n• Type '*book new flight*' to start a new booking"
        message += f"\n• Type '*compare prices*' for detailed price comparison"
        
        return message
    
    def validate_pdf_file(self, file_content: bytes) -> bool:
        """Validate if the uploaded file is a valid PDF"""
        try:
            # Check PDF magic number
            if not file_content.startswith(b'%PDF-'):
                return False
            
            # Try to open with PyPDF2
            import io
            pdf_stream = io.BytesIO(file_content)
            PyPDF2.PdfReader(pdf_stream)
            return True
            
        except Exception:
            return False 