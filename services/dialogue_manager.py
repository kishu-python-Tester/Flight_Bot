import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime

from models.conversation import ConversationState, ConversationSession
from services.intent_service import IntentService
from services.flight_service import FlightService
from services.whatsapp_service import WhatsAppService
from models.flight_data import Flight, Passenger

logger = logging.getLogger(__name__)

class DialogueManager:
    def __init__(self, whatsapp_service: WhatsAppService):
        self.intent_service = IntentService()
        self.flight_service = FlightService()
        self.whatsapp_service = whatsapp_service
        
        # Maximum retry attempts before offering human support
        self.max_retries = 3
    
    def process_message(self, session: ConversationSession, message: str) -> str:
        """Process incoming message and return response"""
        try:
            session.set_context('last_message', message)
            
            # Route to appropriate handler based on current state
            if session.state == ConversationState.GREETING:
                return self._handle_greeting(session, message)
            elif session.state == ConversationState.COLLECT_SOURCE:
                return self._handle_source_collection(session, message)
            elif session.state == ConversationState.COLLECT_DESTINATION:
                return self._handle_destination_collection(session, message)
            elif session.state == ConversationState.COLLECT_DATE:
                return self._handle_date_collection(session, message)
            elif session.state == ConversationState.COLLECT_PASSENGERS:
                return self._handle_passenger_collection(session, message)
            elif session.state == ConversationState.SHOW_FLIGHTS:
                return self._handle_flight_display(session, message)
            elif session.state == ConversationState.COLLECT_SELECTION:
                return self._handle_flight_selection(session, message)
            elif session.state == ConversationState.COLLECT_PASSENGER_DETAILS:
                return self._handle_passenger_details_collection(session, message)
            elif session.state == ConversationState.COLLECT_SSR:
                return self._handle_ssr_collection(session, message)
            elif session.state == ConversationState.CONFIRM_BOOKING:
                return self._handle_booking_confirmation(session, message)
            elif session.state == ConversationState.COMPLETED:
                return self._handle_completed_state(session, message)
            else:
                return self._handle_unknown_state(session, message)
                
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return "❌ Something went wrong. Please try again or type 'help' for assistance."
    
    def _handle_greeting(self, session: ConversationSession, message: str) -> str:
        """Handle initial greeting and intent detection"""
        
        # Check if user wants to book a flight
        if self.intent_service.detect_flight_booking_intent(message):
            # Try to extract information from the initial message
            cities = self.intent_service.extract_cities(message)
            date = self.intent_service.extract_date(message)
            passenger_counts = self.intent_service.extract_passenger_count(message)
            
            # Set extracted information
            if len(cities) >= 2:
                session.set_data('source_city', cities[0])
                session.set_data('destination_city', cities[1])
            elif len(cities) == 1:
                # Determine if it's source or destination based on message context
                if any(word in message.lower() for word in ['from', 'starting', 'leaving']):
                    session.set_data('source_city', cities[0])
                else:
                    session.set_data('destination_city', cities[0])
            
            if date:
                session.set_data('departure_date', date)
            
            if passenger_counts:
                session.set_data('adults', passenger_counts.get('adults', 1))
                session.set_data('children', passenger_counts.get('children', 0))
                session.set_data('infants', passenger_counts.get('infants', 0))
            
            # Move to next required step
            return self._determine_next_step(session)
        else:
            # Not a flight booking request
            return """✈️ *Welcome to Flight Booking Assistant!*

I can help you book flights quickly and easily. To get started, just tell me:

*Examples:*
• "I want to book a flight"
• "Flight to Dubai"
• "Book flight from Delhi to Mumbai tomorrow"

*What can I help you with today?* 🛫"""
    
    def _handle_source_collection(self, session: ConversationSession, message: str) -> str:
        """Handle source city collection"""
        cities = self.intent_service.extract_cities(message)
        
        if cities:
            source_city = cities[0]
            session.set_data('source_city', source_city)
            session.reset_retry()
            return self._determine_next_step(session)
        else:
            session.increment_retry()
            if session.get_retry_count() >= self.max_retries:
                return self._offer_human_support(session)
            
            return f"""🏙️ I couldn't find that city. Please provide a valid departure city.

*Examples:* Delhi, Mumbai, Bangalore, Hyderabad, Chennai

*Which city are you flying from?*"""
    
    def _handle_destination_collection(self, session: ConversationSession, message: str) -> str:
        """Handle destination city collection"""
        cities = self.intent_service.extract_cities(message)
        
        if cities:
            destination_city = cities[0]
            source_city = session.get_data('source_city')
            
            # Check if source and destination are the same
            if source_city and destination_city['iata'] == source_city['iata']:
                session.increment_retry()
                return "🤔 Source and destination cannot be the same. Please choose a different destination city."
            
            # Check if route exists
            if source_city and not self.flight_service.validate_route(source_city['iata'], destination_city['iata']):
                available_destinations = self.flight_service.get_available_destinations_from(source_city['iata'])
                if available_destinations:
                    dest_names = [self._get_city_name_by_iata(iata) for iata in available_destinations]
                    session.increment_retry()
                    return f"""❌ No flights available from {source_city['name']} to {destination_city['name']}.

*Available destinations from {source_city['name']}:*
{', '.join(dest_names)}

*Please choose one of these destinations:*"""
            
            session.set_data('destination_city', destination_city)
            session.reset_retry()
            return self._determine_next_step(session)
        else:
            session.increment_retry()
            if session.get_retry_count() >= self.max_retries:
                return self._offer_human_support(session)
            
            return f"""🏙️ I couldn't find that city. Please provide a valid destination city.

*Examples:* Dubai, London, Singapore, Bangkok

*Where would you like to fly to?*"""
    
    def _handle_date_collection(self, session: ConversationSession, message: str) -> str:
        """Handle travel date collection"""
        date = self.intent_service.extract_date(message)
        
        if date:
            session.set_data('departure_date', date)
            session.reset_retry()
            return self._determine_next_step(session)
        else:
            session.increment_retry()
            if session.get_retry_count() >= self.max_retries:
                return self._offer_human_support(session)
            
            return f"""📅 I couldn't understand the date. Please provide your travel date.

*Examples:*
• "July 15"
• "15/07/2025"
• "Tomorrow"
• "Next week"

*When would you like to travel?*"""
    
    def _handle_passenger_collection(self, session: ConversationSession, message: str) -> str:
        """Handle passenger count collection"""
        passenger_counts = self.intent_service.extract_passenger_count(message)
        
        total_passengers = passenger_counts['adults'] + passenger_counts['children'] + passenger_counts['infants']
        
        if total_passengers > 9:
            session.increment_retry()
            return "👥 Maximum 9 passengers allowed per booking. Please reduce the number of passengers."
        
        if total_passengers > 0:
            session.set_data('adults', passenger_counts['adults'])
            session.set_data('children', passenger_counts['children'])
            session.set_data('infants', passenger_counts['infants'])
            session.reset_retry()
            return self._determine_next_step(session)
        else:
            session.increment_retry()
            if session.get_retry_count() >= self.max_retries:
                return self._offer_human_support(session)
            
            return f"""👥 Please tell me how many passengers will be traveling.

*Examples:*
• "1 adult"
• "2 adults"
• "2 adults and 1 child"
• "Just me"

*How many passengers?*"""
    
    def _handle_flight_display(self, session: ConversationSession, message: str) -> str:
        """Handle flight search and display"""
        source_city = session.get_data('source_city')
        destination_city = session.get_data('destination_city')
        departure_date = session.get_data('departure_date')
        adults = session.get_data('adults', 1)
        children = session.get_data('children', 0)
        infants = session.get_data('infants', 0)
        
        # Search for flights
        flights = self.flight_service.search_flights(
            origin=source_city['iata'],
            destination=destination_city['iata'],
            date=departure_date,
            adults=adults,
            children=children,
            infants=infants
        )
        
        if not flights:
            return self.whatsapp_service.send_error_message(session.phone_number, 'no_flights')
        
        # Store available flights in session
        session.set_context('available_flights', flights)
        
        # Format and send flights
        flight_message = self.flight_service.format_flights_for_whatsapp(flights)
        session.set_state(ConversationState.COLLECT_SELECTION)
        
        return flight_message
    
    def _handle_flight_selection(self, session: ConversationSession, message: str) -> str:
        """Handle flight selection"""
        selection = self.intent_service.extract_flight_selection(message)
        available_flights = session.get_context('available_flights', [])
        
        if selection and 1 <= selection <= len(available_flights):
            selected_flight = available_flights[selection - 1]
            session.set_data('selected_flight', selected_flight)
            session.reset_retry()
            
            # Move to passenger details collection
            session.set_state(ConversationState.COLLECT_PASSENGER_DETAILS)
            
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
    
    def _handle_passenger_details_collection(self, session: ConversationSession, message: str) -> str:
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
            return "❌ *Booking Cancelled*\n\nNo worries! Feel free to start a new search anytime. Just say 'book flight' when you're ready. ✈️"
        else:
            return """Please confirm your booking:

• Type "*yes*" or "*confirm*" to proceed with booking
• Type "*no*" or "*cancel*" to cancel

*Would you like to proceed?*"""
    
    def _handle_completed_state(self, session: ConversationSession, message: str) -> str:
        """Handle completed state - start new booking"""
        if self.intent_service.detect_flight_booking_intent(message):
            # Start new booking
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
            return self._handle_greeting(session, message)
        else:
            return """✈️ *How can I help you today?*

• Type "*book flight*" to start a new booking
• Type "*help*" for assistance

*What would you like to do?*"""
    
    def _handle_unknown_state(self, session: ConversationSession, message: str) -> str:
        """Handle unknown state"""
        logger.warning(f"Unknown state: {session.state}")
        session.set_state(ConversationState.GREETING)
        return "🤔 Something seems off. Let's start fresh. How can I help you book a flight?"
    
    def _determine_next_step(self, session: ConversationSession) -> str:
        """Determine the next step in the conversation flow"""
        # Check what information is missing and move to appropriate state
        
        if not session.get_data('source_city'):
            session.set_state(ConversationState.COLLECT_SOURCE)
            return "🛫 *Great! Let's book your flight.*\n\n*Which city are you flying from?*"
        
        if not session.get_data('destination_city'):
            session.set_state(ConversationState.COLLECT_DESTINATION)
            source_city = session.get_data('source_city')
            return f"🛬 *Flying from {source_city['name']}.*\n\n*Where would you like to go?*"
        
        if not session.get_data('departure_date'):
            session.set_state(ConversationState.COLLECT_DATE)
            destination_city = session.get_data('destination_city')
            return f"📅 *Flying to {destination_city['name']}.*\n\n*When would you like to travel?*"
        
        # Check passenger count
        adults = session.get_data('adults', 0)
        if adults <= 0:
            session.set_state(ConversationState.COLLECT_PASSENGERS)
            return "👥 *How many passengers will be traveling?*"
        
        # All required information collected, search for flights
        session.set_state(ConversationState.SHOW_FLIGHTS)
        return self._handle_flight_display(session, "")
    
    def _generate_booking_summary(self, session: ConversationSession) -> str:
        """Generate booking summary for confirmation"""
        source_city = session.get_data('source_city')
        destination_city = session.get_data('destination_city')
        departure_date = session.get_data('departure_date')
        selected_flight = session.get_data('selected_flight')
        passengers = session.get_data('passengers', [])
        ssr_requests = session.get_data('ssr', [])
        adults = session.get_data('adults', 1)
        
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
• Type "*book flight*" to start over

Our team will contact you shortly! 📞"""
    
    def _get_city_name_by_iata(self, iata_code: str) -> str:
        """Get city name by IATA code"""
        cities_data = self.intent_service.cities_data
        for city_key, city_data in cities_data['cities'].items():
            if city_data['iata'] == iata_code:
                return city_data['name']
        return iata_code 