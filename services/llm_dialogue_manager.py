import logging
from typing import Dict, Optional
from models.conversation import ConversationState, ConversationSession
from services.llm_service import LLMService
from services.flight_service import FlightService
from services.whatsapp_service import WhatsAppService
from services.intent_service import IntentService

logger = logging.getLogger(__name__)

class LLMDialogueManager:
    def __init__(self, whatsapp_service: WhatsAppService):
        self.llm_service = LLMService()
        self.flight_service = FlightService()
        self.whatsapp_service = whatsapp_service
        self.intent_service = IntentService()  # Keep for city/date extraction
        self.max_retries = 3
        
    def process_message(self, session: ConversationSession, message: str) -> str:
        """Process message using LLM-powered understanding"""
        try:
            session.set_context('last_message', message)
            
            # Detect if user wants to start a new booking (reset intent) - works in any state
            reset_phrases = [
                'i need to book flight', 'i want to book flight', 'book me a flight',
                'i need another flight', 'i want another flight', 'book another flight',
                'i need a new flight', 'i want a new flight', 'book a new flight',
                'new booking', 'fresh booking', 'start over', 'book flight',
                'i need flight', 'i want flight'
            ]
            
            message_lower = message.lower().strip()
            is_reset_intent = any(phrase in message_lower for phrase in reset_phrases)
            
            # If user is asking for a new booking and we have previous data, reset it
            if (is_reset_intent and 
                (session.get_data('source_city') or session.get_data('destination_city'))):
                
                logger.info(f"🔄 Detected new booking intent, resetting session data for {session.phone_number}")
                
                # Reset booking data to start fresh
                session.set_data('source_city', None)
                session.set_data('destination_city', None) 
                session.set_data('departure_date', None)
                session.set_data('adults', 1)
                session.set_data('children', 0)
                session.set_data('infants', 0)
                session.set_data('passengers', [])
                session.set_data('ssr', [])
                session.set_data('selected_flight', None)
                
                # Clear any flight search context
                session.set_context('available_flights', None)
                session.set_state(ConversationState.GREETING)
                
                # Process the reset message through LLM to generate appropriate response
                return self._handle_with_llm(session, message)
            
            # Special handling for specific states that don't need LLM
            if session.state == ConversationState.COLLECT_SELECTION:
                return self._handle_flight_selection(session, message)
            elif session.state == ConversationState.COLLECT_PASSENGER_DETAILS:
                return self._handle_passenger_details(session, message)
            elif session.state == ConversationState.COLLECT_SSR:
                return self._handle_ssr_collection(session, message)
            elif session.state == ConversationState.CONFIRM_BOOKING:
                return self._handle_booking_confirmation(session, message)
            elif session.state == ConversationState.COMPLETED:
                return self._handle_completed_state(session, message)
            
            # Use LLM for intelligent understanding
            return self._handle_with_llm(session, message)
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return "❌ Something went wrong. Please tell me about your travel plans again."
    
    def _handle_with_llm(self, session: ConversationSession, message: str) -> str:
        """Handle message using LLM intelligence"""
        
        # Get current booking data (after potential reset)
        current_data = {
            "source_city": session.get_data('source_city'),
            "destination_city": session.get_data('destination_city'),
            "departure_date": session.get_data('departure_date'),
            "adults": session.get_data('adults', 1),
            "children": session.get_data('children', 0),
            "infants": session.get_data('infants', 0)
        }
        
        # Analyze message with LLM
        analysis = self.llm_service.analyze_flight_booking_message(message, current_data)
        
        if analysis["intent"] != "flight_booking":
            return self.llm_service.generate_response(analysis, current_data)
        
        # Extract and update information
        extracted = analysis.get("extracted_data", {})
        updated = False
        
        # Update source city using LLM extraction
        if extracted.get('source_city') and not current_data['source_city']:
            cities = self.intent_service.extract_cities(extracted['source_city'])
            if cities:
                session.set_data('source_city', cities[0])
                updated = True
        
        # Update destination city using LLM extraction  
        if extracted.get('destination_city') and not current_data['destination_city']:
            cities = self.intent_service.extract_cities(extracted['destination_city'])
            if cities:
                session.set_data('destination_city', cities[0])
                updated = True
        
        # Only use fallback city extraction if BOTH cities are still missing
        if not session.get_data('source_city') and not session.get_data('destination_city'):
            cities = self.intent_service.extract_cities(message)
            if len(cities) >= 2:
                # Assume first city is source, second is destination
                session.set_data('source_city', cities[0])
                session.set_data('destination_city', cities[1])
                updated = True
            elif len(cities) == 1:
                # Only one city found, ask for the missing one
                session.set_data('destination_city', cities[0])
                updated = True
        
        # Update date
        if extracted.get('departure_date') and not current_data['departure_date']:
            session.set_data('departure_date', extracted['departure_date'])
            updated = True
        elif not current_data['departure_date']:
            # Try existing date extraction
            date = self.intent_service.extract_date(message)
            if date:
                session.set_data('departure_date', date)
                updated = True
        
        # Update passengers
        if extracted.get('adults'):
            session.set_data('adults', extracted['adults'])
            updated = True
        if extracted.get('children'):
            session.set_data('children', extracted['children'])
            updated = True
        if extracted.get('infants'):
            session.set_data('infants', extracted['infants'])
            updated = True
        
        # Check if we have enough information to search flights
        if self._has_enough_info(session):
            return self._search_and_display_flights(session)
        
        # Generate appropriate next question
        return self.llm_service.generate_response(analysis, session.data)
    
    def _has_enough_info(self, session: ConversationSession) -> bool:
        """Check if we have enough information to search flights"""
        return (session.get_data('source_city') and 
                session.get_data('destination_city') and 
                session.get_data('departure_date'))
    
    def _search_and_display_flights(self, session: ConversationSession) -> str:
        """Search and display available flights"""
        source_city = session.get_data('source_city')
        destination_city = session.get_data('destination_city')
        departure_date = session.get_data('departure_date')
        adults = session.get_data('adults', 1)
        children = session.get_data('children', 0)
        infants = session.get_data('infants', 0)
        
        # Search flights
        flights = self.flight_service.search_flights(
            origin=source_city['iata'],
            destination=destination_city['iata'],
            date=departure_date,
            adults=adults,
            children=children,
            infants=infants
        )
        
        if not flights:
            return f"""❌ *No flights found*

Sorry, no flights available from {source_city['name']} to {destination_city['name']} on {departure_date}.

*Try:*
• Different dates
• Different destinations
• Or tell me about alternative travel plans"""
        
        # Store flights and move to selection
        session.set_context('available_flights', flights)
        session.set_state(ConversationState.COLLECT_SELECTION)
        
        return self.flight_service.format_flights_for_whatsapp(flights)
    
    def _handle_flight_selection(self, session: ConversationSession, message: str) -> str:
        """Handle flight selection using existing logic"""
        selection = self.intent_service.extract_flight_selection(message)
        available_flights = session.get_context('available_flights', [])
        
        if selection and 1 <= selection <= len(available_flights):
            selected_flight = available_flights[selection - 1]
            session.set_data('selected_flight', selected_flight)
            session.set_state(ConversationState.COLLECT_PASSENGER_DETAILS)
            session.reset_retry()
            
            adults = session.get_data('adults', 1)
            if adults == 1:
                return f"""✅ *Flight Selected:* {selected_flight.airline} {selected_flight.flight_id}

👤 *Passenger Details Required:*
Please provide passenger information in this format:
*Full Name, Date of Birth, Passport Number, Nationality*

*Example:*
John Doe, 10-May-1990, A1234567, Indian

*Please enter passenger details:*"""
            else:
                return f"""✅ *Flight Selected:* {selected_flight.airline} {selected_flight.flight_id}

👥 *Passenger Details Required ({adults} passengers):*
Please provide details for passenger 1 in this format:
*Full Name, Date of Birth, Passport Number, Nationality*

*Example:*
John Doe, 10-May-1990, A1234567, Indian

*Passenger 1 details:*"""
        else:
            session.increment_retry()
            if session.get_retry_count() >= self.max_retries:
                return self._offer_human_support(session)
            
            return f"""❌ Invalid selection. Please choose a number between 1 and {len(available_flights)}.

*Example:* Type "*1*" to select the first option.

*Which flight would you like to select?*"""
    
    def _handle_passenger_details(self, session: ConversationSession, message: str) -> str:
        """Handle passenger details collection"""
        passenger_details = self.intent_service.extract_passenger_details(message)
        
        if passenger_details:
            passengers = session.get_data('passengers', [])
            passengers.append(passenger_details)
            session.set_data('passengers', passengers)
            
            adults = session.get_data('adults', 1)
            current_passenger_count = len(passengers)
            
            if current_passenger_count < adults:
                # Need more passenger details
                next_passenger = current_passenger_count + 1
                return f"""✅ *Passenger {current_passenger_count} details saved!*

👤 *Please provide details for passenger {next_passenger}:*
*Full Name, Date of Birth, Passport Number, Nationality*

*Passenger {next_passenger} details:*"""
            else:
                # All passenger details collected
                session.reset_retry()
                session.set_state(ConversationState.COLLECT_SSR)
                
                return f"""✅ *All passenger details saved!*

🍽️ *Special Requests (Optional):*
Do you have any special requests for your flight?

*Examples:*
• "Vegetarian meal and window seat"
• "Wheelchair assistance"
• "Extra baggage"
• "No special requests"

*Any special requests?*"""
        else:
            session.increment_retry()
            if session.get_retry_count() >= self.max_retries:
                return self._offer_human_support(session)
            
            return f"""❌ Invalid format. Please provide passenger details in this format:

*Full Name, Date of Birth, Passport Number, Nationality*

*Example:*
John Doe, 10-May-1990, A1234567, Indian

*Please try again:*"""
    
    def _handle_ssr_collection(self, session: ConversationSession, message: str) -> str:
        """Handle special service requests collection"""
        if self.intent_service.is_negative(message) or 'no special' in message.lower() or 'skip' in message.lower():
            # No special requests
            session.set_data('ssr', [])
        else:
            # Extract SSR requests
            ssr_requests = self.intent_service.extract_ssr_requests(message)
            session.set_data('ssr', ssr_requests)
        
        # Move to booking confirmation
        session.set_state(ConversationState.CONFIRM_BOOKING)
        return self._generate_booking_summary(session)
    
    def _handle_booking_confirmation(self, session: ConversationSession, message: str) -> str:
        """Handle final booking confirmation"""
        if self.intent_service.is_affirmative(message) or 'confirm' in message.lower():
            return self._process_booking(session)
        elif self.intent_service.is_negative(message) or 'cancel' in message.lower():
            session.set_state(ConversationState.COMPLETED)
            return "❌ *Booking Cancelled*\n\nNo worries! Feel free to start a new search anytime. Just tell me about your travel plans! ✈️"
        else:
            return """Please confirm your booking:

• Type "*yes*" or "*confirm*" to proceed with booking
• Type "*no*" or "*cancel*" to cancel

*Would you like to proceed?*"""
    
    def _handle_completed_state(self, session: ConversationSession, message: str) -> str:
        """Handle completed state - start new booking"""
        # Reset session for new booking
        session.state = ConversationState.GREETING
        session.data = {
            'source_city': None,
            'destination_city': None,
            'departure_date': None,
            'return_date': None,
            'adults': 1,
            'children': 0,
            'infants': 0,
            'selected_flight': None,
            'passengers': [],
            'ssr': [],
            'pnr': None,
            'booking_confirmed': False
        }
        return self._handle_with_llm(session, message)
    
    def _generate_booking_summary(self, session: ConversationSession) -> str:
        """Generate booking summary for confirmation"""
        source_city = session.get_data('source_city')
        destination_city = session.get_data('destination_city')
        departure_date = session.get_data('departure_date')
        selected_flight = session.get_data('selected_flight')
        passengers = session.get_data('passengers', [])
        ssr_requests = session.get_data('ssr', [])
        
        # Passenger summary
        if len(passengers) == 1:
            passenger_summary = f"👤 *Passenger:* {passengers[0]['first_name']} {passengers[0]['last_name']}"
        else:
            passenger_names = [f"• {p['first_name']} {p['last_name']}" for p in passengers]
            passenger_summary = f"👥 *Passengers:*\n" + "\n".join(passenger_names)
        
        # SSR summary
        ssr_summary = ""
        if ssr_requests:
            ssr_descriptions = []
            for ssr in ssr_requests:
                if ssr['type'] == 'meal':
                    ssr_descriptions.append(f"• {ssr['preference'].title()} meal")
                elif ssr['type'] == 'seat':
                    ssr_descriptions.append(f"• {ssr['preference'].replace('_', ' ').title()} seat")
                else:
                    ssr_descriptions.append(f"• {ssr['preference'].title()}")
            ssr_summary = f"\n\n🍽️ *Special Requests:*\n" + "\n".join(ssr_descriptions)
        
        return f"""📋 *BOOKING SUMMARY*

✈️ *Flight:* {selected_flight.airline} {selected_flight.flight_id}
🛫 *Route:* {source_city['name']} → {destination_city['name']}
📅 *Date:* {departure_date}
🕐 *Time:* {selected_flight.departure_time} - {selected_flight.arrival_time}
💰 *Total Price:* ₹{selected_flight.price:,}

{passenger_summary}{ssr_summary}

*Please confirm your booking:*
• Type "*yes*" or "*confirm*" to proceed
• Type "*no*" or "*cancel*" to cancel

*Proceed with booking?*"""
    
    def _process_booking(self, session: ConversationSession) -> str:
        """Process the actual booking"""
        try:
            selected_flight = session.get_data('selected_flight')
            passengers = session.get_data('passengers', [])
            ssr_requests = session.get_data('ssr', [])
            
            # Create booking
            booking = self.flight_service.create_booking(
                flight=selected_flight,
                passengers_data=passengers,
                contact_email="customer@example.com",  # In real implementation, collect this
                contact_phone=session.phone_number
            )
            
            if not booking:
                return "❌ *Booking Failed*\n\nSorry, there was an issue creating your booking. Please try again or contact support."
            
            # Add special requests if any
            if ssr_requests:
                self.flight_service.add_special_requests(booking.pnr, ssr_requests)
            
            # Issue ticket
            self.flight_service.issue_ticket(booking.pnr)
            
            # Update session
            session.set_data('pnr', booking.pnr)
            session.set_data('booking_confirmed', True)
            session.set_state(ConversationState.COMPLETED)
            
            # Return confirmation message
            return booking.generate_confirmation_message()
            
        except Exception as e:
            logger.error(f"Error processing booking: {e}")
            return "❌ *Booking Failed*\n\nSorry, there was an issue processing your booking. Please try again or contact support."
    
    def _offer_human_support(self, session: ConversationSession) -> str:
        """Offer human support when bot reaches retry limit"""
        session.set_state(ConversationState.COMPLETED)
        return """🆘 *Need Human Assistance*

I'm having trouble understanding your request. Let me connect you with our support team.

*Your support ticket ID: #12345*

Meanwhile, you can:
• Try rephrasing your request
• Type "*help*" for assistance
• Tell me about your travel plans in different words

Our team will contact you shortly! 📞""" 