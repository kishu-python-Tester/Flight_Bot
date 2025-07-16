import logging
from typing import Dict, Optional
from models.conversation import ConversationState, ConversationSession
from services.llm_service import LLMService
from services.flight_service import FlightService
from services.whatsapp_service import WhatsAppService
from services.intent_service import IntentService
from datetime import datetime
from models.ticket_storage import ticket_storage

logger = logging.getLogger(__name__)

class LLMDialogueManager:
    def __init__(self, whatsapp_service: WhatsAppService):
        self.llm_service = LLMService()
        self.flight_service = FlightService()
        self.whatsapp_service = whatsapp_service
        self.intent_service = IntentService()  # Keep for city/date extraction
        self.max_retries = 3
        
    def process_message(self, session: ConversationSession, message: str) -> str:
        """Process incoming message and return appropriate response"""
        
        try:
            session.set_context('last_message', message)
            
            # 🆕 CHECK FOR STORED TICKET DATA if session doesn't have it
            if not session.get_context('parsed_ticket'):
                stored_data = ticket_storage.get_ticket_data(session.phone_number)
                if stored_data:
                    # Restore ticket data to session
                    session.set_context('parsed_ticket', stored_data.get('ticket_info'))
                    session.set_context('price_comparison', stored_data.get('price_comparison'))
                    logger.info(f"✅ Restored ticket data for {session.phone_number}")
            
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
            elif session.state == ConversationState.COLLECT_OFFICE_ID:
                return self._handle_office_id_collection(session, message)
            elif session.state == ConversationState.COMPLETED:
                return self._handle_completed_state(session, message)
            
            # Check for ticket-related actions first
            if session.get_context('parsed_ticket'):
                ticket_action = self._detect_ticket_action(message)
                if ticket_action:
                    return self._handle_ticket_action(session, message, ticket_action)
            
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
        """Handle completed state - check for ticket actions before starting new booking"""
        
        # 🆕 ENHANCED: Check for ticket-related actions first before resetting session
        if session.get_context('parsed_ticket'):
            ticket_action = self._detect_ticket_action(message)
            if ticket_action:
                # User is asking about their ticket, handle the action
                return self._handle_ticket_action(session, message, ticket_action)
        
        # 🆕 ENHANCED: Check if user wants to start a new booking explicitly
        new_booking_phrases = [
            'book new flight', 'new booking', 'fresh booking', 'start over',
            'book flight', 'i need flight', 'i want flight', 'book me flight',
            'need to book', 'want to book'
        ]
        
        message_lower = message.lower().strip()
        is_new_booking_request = any(phrase in message_lower for phrase in new_booking_phrases)
        
        if is_new_booking_request:
            # User explicitly wants a new booking, reset session
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
        
        # 🆕 ENHANCED: Fallback for ticket-related queries that weren't detected
        has_ticket = session.get_context('parsed_ticket')
        has_comparison = session.get_context('price_comparison')
        
        # Keywords that suggest user is asking about their ticket
        ticket_related_keywords = [
            'price', 'cost', 'fare', 'ticket', 'flight', 'compare', 'show', 'tell', 'check',
            'what', 'how much', 'details', 'info', 'information', 'about'
        ]
        
        has_ticket_keywords = any(keyword in message_lower for keyword in ticket_related_keywords)
        
        if has_ticket and has_ticket_keywords:
            # User seems to be asking about their ticket but action wasn't detected
            # Provide helpful guidance instead of resetting to new booking
            flight_details = has_ticket.get('flight_details', {})
            
            return f"""📄 *Your Uploaded Ticket*

✈️ **Flight:** {flight_details.get('airline', 'Unknown')} {flight_details.get('flight_number', 'N/A')}
📍 **Route:** {flight_details.get('origin_city', 'Unknown')} → {flight_details.get('destination_city', 'Unknown')}
📅 **Date:** {flight_details.get('departure_date', 'N/A')}

💡 **You can ask me:**
• "*compare prices*" - Compare with our system prices
• "*search similar*" - Find similar flights to book
• "*book new flight*" - Start a fresh booking

*What would you like to know?* ✈️"""
        
        # 🆕 ENHANCED: For other messages, provide helpful guidance without resetting
        return """✅ *Booking Complete!*

Your previous booking is confirmed. What would you like to do next?

📄 *If you have a ticket uploaded:*
• Type '*compare prices*' for price comparison
• Type '*search similar*' to find similar flights

✈️ *For new bookings:*
• Type '*book new flight*' to start fresh booking
• Tell me your travel plans

*How can I help you?* 🛫"""
    
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
    
    def _detect_ticket_action(self, message: str) -> str:
        """Detect if user wants to perform actions related to their uploaded ticket"""
        message_lower = message.lower().strip()
        
        # 🆕 ENHANCED: Much more comprehensive price comparison detection
        price_comparison_phrases = [
            # Direct comparison
            'compare prices', 'price comparison', 'compare', 'comparison',
            
            # Show/tell variations
            'show prices', 'show price', 'tell me prices', 'tell me price', 
            'show me prices', 'show me price', 'display prices', 'display price',
            
            # Check variations  
            'check prices', 'check price', 'price check', 'check cost',
            'check fare', 'fare check',
            
            # What/how questions
            'what about prices', 'what about price', 'what about cost',
            'what about fare', 'how much', 'how much does it cost',
            'what is the price', 'what is price', 'what price',
            'what cost', 'what fare',
            
            # Details variations
            'price details', 'price detail', 'cost details', 'cost detail',
            'fare details', 'fare detail', 'pricing details', 'pricing',
            
            # System comparison
            'compare with system', 'compare with your system', 'system price',
            'your price', 'better price', 'cheaper price',
            
            # General price inquiries
            'prices', 'price', 'cost', 'costs', 'fare', 'fares',
            'pricing', 'rate', 'rates', 'amount', 'total',
            
            # Action-oriented
            'analyze price', 'analyze prices', 'review price', 'review prices'
        ]
        
        if any(phrase in message_lower for phrase in price_comparison_phrases):
            return 'compare_prices'
        
        # Other actions (existing logic)
        elif any(phrase in message_lower for phrase in ['search similar', 'find similar', 'similar flights']):
            return 'search_similar'
        elif any(phrase in message_lower for phrase in ['book new flight', 'new booking', 'book flight']):
            return 'book_new'
        elif any(phrase in message_lower for phrase in ['book this flight', 'book same flight', 'book exact']):
            return 'book_exact'
        elif any(phrase in message_lower for phrase in [
            'book with new price', 'book new price', 'go ahead', 'proceed', 
            'book cheaper', 'book better price', 'book with system', 'book now',
            'yes book', 'book it', 'book this'
        ]):
            return 'book_with_better_price'
        
        return ''
    
    def _handle_ticket_action(self, session: ConversationSession, message: str, action: str) -> str:
        """Handle actions related to uploaded ticket"""
        parsed_ticket = session.get_context('parsed_ticket')
        
        if not parsed_ticket:
            return "❌ No ticket information found. Please upload your ticket again."
        
        flight_details = parsed_ticket.get('flight_details', {})
        
        if action == 'search_similar':
            # Search for flights on the same route
            origin = flight_details.get('origin_airport')
            destination = flight_details.get('destination_airport')
            date = flight_details.get('departure_date')
            
            if not all([origin, destination, date]):
                return "❌ Missing flight details. Please upload a clearer ticket."
            
            # Set up booking search using airport codes
            from services.intent_service import IntentService
            intent_service = IntentService()
            
            # Try to find city data for origin and destination
            origin_cities = intent_service.extract_cities(origin)
            dest_cities = intent_service.extract_cities(destination)
            
            if origin_cities and dest_cities:
                session.set_data('source_city', origin_cities[0])
                session.set_data('destination_city', dest_cities[0])
                session.set_data('departure_date', date)
                session.set_data('adults', 1)
                session.set_data('children', 0)
                session.set_data('infants', 0)
                
                # Search and display flights
                return self._search_and_display_flights(session)
            else:
                return f"❌ Sorry, we don't have flights available for the route {origin} → {destination}."
        
        elif action == 'book_new':
            # Reset session for new booking
            session.reset_session()
            session.set_state(ConversationState.GREETING)
            return """✈️ *New Flight Booking*

Perfect! Let's start a fresh booking for you.

Tell me where you'd like to travel:
• "Flight from Delhi to Mumbai tomorrow"
• "Need to go to Dubai next week"
• "Traveling to London for business"

*Where would you like to go?* 🛫"""
        
        elif action == 'compare_prices':
            price_comparison = session.get_context('price_comparison')
            if not price_comparison or not price_comparison.get('comparison_available'):
                return "❌ Price comparison not available for this route."
            
            # Detailed price comparison with safe data access
            comp = price_comparison
            ticket_price = comp.get('ticket_price', 0)
            best_system_price = comp.get('best_system_price', 0)
            price_difference = comp.get('price_difference', 0)
            savings_percentage = comp.get('savings_percentage', 0)
            
            # Ensure all values are numeric and safe
            try:
                ticket_price = float(ticket_price) if ticket_price else 0
                best_system_price = float(best_system_price) if best_system_price else 0
                price_difference = float(price_difference) if price_difference else 0
                savings_percentage = float(savings_percentage) if savings_percentage else 0
            except (ValueError, TypeError):
                return "❌ Error in price comparison data. Please try uploading your ticket again."
            
            message = f"""💰 *Detailed Price Comparison*

📋 *Your Ticket Details:*
✈️ {flight_details.get('airline', 'Unknown')} {flight_details.get('flight_number', 'N/A')}
📍 {flight_details.get('origin_city', 'Unknown')} → {flight_details.get('destination_city', 'Unknown')}
📅 {flight_details.get('departure_date', 'N/A')}
💰 Price: ₹{int(ticket_price):,}

🏷️ *Our System Comparison:*
💰 Best Available Price: ₹{int(best_system_price):,}
📊 Price Difference: ₹{int(abs(price_difference)):,}"""
            
            if comp.get('recommendation') == 'cheaper' and price_difference > 0:
                message += f"\n\n💸 *Potential Savings: ₹{int(abs(price_difference)):,}*"
                message += f"\n✨ You could save {savings_percentage}% by booking with us!"
            elif comp.get('recommendation') == 'similar':
                message += f"\n\n✅ Your price is competitive! Only ±₹{abs(price_difference):,} difference."
            else:
                message += f"\n\n📈 Your ticket cost ₹{abs(price_difference):,} more than our best price."
            
            message += "\n\n🔍 *Want to see available flights?*\nType '*search similar*' to explore options!"
            
            return message
        
        elif action == 'book_exact':
            return f"""🎫 *Book Exact Flight*

Your ticket details:
✈️ {flight_details.get('airline')} {flight_details.get('flight_number')}
📍 {flight_details.get('origin_city')} → {flight_details.get('destination_city')}
📅 {flight_details.get('departure_date')}

❌ *Sorry, we cannot book the exact same flight* as it may be:
• Already departed
• From a different booking system
• Not available in our inventory

🔄 *Instead, try:*
• Type '*search similar*' for flights on the same route
• Type '*book new flight*' to start fresh booking

*How can I help you?* ✈️"""
        
        elif action == 'book_with_better_price':
            # Check if we have price comparison data and can offer better price
            price_comparison = session.get_context('price_comparison')
            if not price_comparison or not price_comparison.get('comparison_available'):
                return """❌ *Cannot proceed with booking*

Price comparison is not available for your ticket route. Please try:
• Type '*search similar*' to find available flights
• Type '*book new flight*' to start a new booking

*How can I help you?* ✈️"""
            
            # Check if we actually have a better price
            if price_comparison.get('recommendation') != 'cheaper':
                return f"""💰 *Price Check*

Based on our comparison, our system shows:
📋 *Your Ticket:* ₹{price_comparison.get('ticket_price', 0):,}
🏷️ *Our Best Price:* ₹{price_comparison.get('best_system_price', 0):,}

{price_comparison.get('recommendation', 'similar').title()} pricing detected. Would you still like to book with us?

• Type '*search similar*' to see available options
• Type '*book new flight*' to start fresh booking

*How can I help you?* ✈️"""
            
            # We have a better price, proceed to collect office ID
            savings_amount = abs(price_comparison.get('price_difference', 0))
            savings_percentage = price_comparison.get('savings_percentage', 0)
            
            session.set_state(ConversationState.COLLECT_OFFICE_ID)
            
            return f"""💸 *Great! Let's book with better pricing*

✅ *Savings Available:* ₹{savings_amount:,} ({savings_percentage}%)
🏷️ *New Price:* ₹{price_comparison.get('best_system_price', 0):,}

To proceed with the booking, I need your *Office ID* for the ticket:

📝 *Please provide your Office ID:*
Example: "OFF123456" or "CORP-001"

*Enter your Office ID:*"""

        return "❌ Unknown action. Try 'search similar', 'book new flight', or 'compare prices'."
    
    def _handle_office_id_collection(self, session: ConversationSession, message: str) -> str:
        """Handle office ID collection for ticket booking"""
        office_id = message.strip()
        
        # Validate office ID format (basic validation)
        if len(office_id) < 3:
            return """❌ *Invalid Office ID*

Please provide a valid Office ID (minimum 3 characters):
Examples: "OFF123456", "CORP-001", "HQ-MUMBAI"

*Enter your Office ID:*"""
        
        # Store office ID in session
        session.set_data('office_id', office_id)
        
        # Get ticket details and price comparison for booking
        ticket_info = session.get_context('parsed_ticket')
        price_comparison = session.get_context('price_comparison')
        
        if not ticket_info or not price_comparison:
            session.set_state(ConversationState.COMPLETED)
            return """❌ *Booking Error*

Sorry, ticket information is no longer available. Please:
• Upload your ticket again
• Type '*book new flight*' to start fresh

*How can I help you?* ✈️"""
        
        # Process the booking and generate new PDF
        return self._process_ticket_rebooking(session, ticket_info, price_comparison, office_id)
    
    def _process_ticket_rebooking(self, session: ConversationSession, ticket_info: dict, price_comparison: dict, office_id: str) -> str:
        """Process ticket rebooking with new office ID and generate PDF"""
        try:
            from services.pdf_generator_service import PDFGeneratorService
            
            # Get flight details from parsed ticket
            flight_details = ticket_info.get('flight_details', {})
            
            # Create new booking data with better price
            new_booking_data = {
                'pnr': self._generate_pnr(),
                'airline': flight_details.get('airline'),
                'flight_number': flight_details.get('flight_number'),
                'origin_city': flight_details.get('origin_city'),
                'origin_airport': flight_details.get('origin_airport'),
                'destination_city': flight_details.get('destination_city'),
                'destination_airport': flight_details.get('destination_airport'),
                'departure_date': flight_details.get('departure_date'),
                'departure_time': flight_details.get('departure_time'),
                'arrival_time': flight_details.get('arrival_time'),
                'class_of_service': flight_details.get('class_of_service', 'Economy'),
                'passenger_name': flight_details.get('passenger_name'),
                'ticket_price': price_comparison.get('best_system_price'),
                'currency': 'INR',
                'office_id': office_id,
                'booking_date': datetime.now().strftime('%Y-%m-%d'),
                'booking_time': datetime.now().strftime('%H:%M')
            }
            
            # Generate new PDF ticket
            pdf_generator = PDFGeneratorService()
            pdf_path = pdf_generator.generate_ticket_pdf(new_booking_data)
            
            if not pdf_path:
                raise Exception("Failed to generate PDF ticket")
            
            # Update session state
            session.set_state(ConversationState.COMPLETED)
            session.set_data('new_booking', new_booking_data)
            session.set_data('pdf_path', pdf_path)
            
            # Calculate savings
            savings_amount = abs(price_comparison.get('price_difference', 0))
            savings_percentage = price_comparison.get('savings_percentage', 0)
            
            # Send the PDF via WhatsApp
            pdf_caption = f"✈️ New Flight Ticket - PNR: {new_booking_data['pnr']}"
            pdf_sent = self.whatsapp_service.send_pdf_document(
                session.phone_number, 
                pdf_path, 
                pdf_caption
            )
            
            if not pdf_sent:
                logger.warning(f"Failed to send PDF to {session.phone_number}")
            
            # Clean up PDF file after sending
            try:
                pdf_generator.cleanup_ticket_file(pdf_path)
            except Exception as e:
                logger.warning(f"Failed to cleanup PDF file: {e}")
            
            return f"""🎫 *BOOKING CONFIRMED!*

📋 *New PNR:* {new_booking_data['pnr']}
✈️ *Flight:* {new_booking_data['airline']} {new_booking_data['flight_number']}
📍 *Route:* {new_booking_data['origin_city']} → {new_booking_data['destination_city']}
📅 *Date:* {new_booking_data['departure_date']}
🎫 *Class:* {new_booking_data['class_of_service']}
👤 *Passenger:* {new_booking_data['passenger_name']}
🏢 *Office ID:* {office_id}

💰 *Pricing:*
🔴 *Previous Price:* ₹{price_comparison.get('ticket_price', 0):,}
🟢 *New Price:* ₹{new_booking_data['ticket_price']:,}
💸 *You Saved:* ₹{savings_amount:,} ({savings_percentage}%)

📄 *New ticket PDF {"sent successfully!" if pdf_sent else "generation completed!"}*

✅ *Thank you for booking with us!*

*Need anything else? Type 'book flight' for a new booking* ✈️"""
            
        except Exception as e:
            logger.error(f"Error processing ticket rebooking: {e}")
            session.set_state(ConversationState.COMPLETED)
            return """❌ *Booking Failed*

Sorry, there was an issue processing your booking. Please try:
• Upload your ticket again
• Type '*book new flight*' to start fresh
• Contact support for assistance

*How can I help you?* ✈️"""
    
    def _generate_pnr(self) -> str:
        """Generate a random PNR for new booking"""
        import random
        import string
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    
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