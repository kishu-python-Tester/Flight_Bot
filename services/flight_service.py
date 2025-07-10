import json
import os
import time
from typing import List, Optional, Dict
from datetime import datetime
from models.flight_data import Flight, Passenger, SpecialServiceRequest, Booking, BookingManager, SSR_CODES
from config.settings import Config

class FlightService:
    def __init__(self):
        self.flights_data = self._load_flights_data()
        self.booking_manager = BookingManager()
    
    def _load_flights_data(self) -> Dict:
        """Load flights data from JSON file"""
        try:
            flights_file = os.path.join(os.path.dirname(__file__), '..', 'data', 'dummy_flights.json')
            with open(flights_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print("Flights data file not found")
            return {'flights': []}
    
    def search_flights(self, origin: str, destination: str, date: str, 
                      adults: int = 1, children: int = 0, infants: int = 0) -> List[Flight]:
        """Search for flights based on criteria"""
        
        # Simulate API delay
        time.sleep(Config.MOCK_API_DELAY)
        
        available_flights = []
        
        for flight_data in self.flights_data['flights']:
            if (flight_data['origin'] == origin.upper() and 
                flight_data['destination'] == destination.upper()):
                
                flight = Flight(
                    flight_id=flight_data['flight_id'],
                    airline=flight_data['airline'],
                    origin=flight_data['origin'],
                    destination=flight_data['destination'],
                    departure_time=flight_data['departure_time'],
                    arrival_time=flight_data['arrival_time'],
                    price=flight_data['price'],
                    currency=flight_data['currency'],
                    duration=flight_data['duration'],
                    aircraft=flight_data['aircraft']
                )
                available_flights.append(flight)
        
        # Calculate total price based on passenger count
        for flight in available_flights:
            total_price = flight.price * adults
            if children > 0:
                total_price += flight.price * 0.75 * children  # 25% discount for children
            if infants > 0:
                total_price += flight.price * 0.1 * infants   # 90% discount for infants
            flight.price = int(total_price)
        
        # Sort by price
        available_flights.sort(key=lambda x: x.price)
        
        return available_flights
    
    def get_flight_by_id(self, flight_id: str) -> Optional[Flight]:
        """Get flight details by flight ID"""
        for flight_data in self.flights_data['flights']:
            if flight_data['flight_id'] == flight_id:
                return Flight(
                    flight_id=flight_data['flight_id'],
                    airline=flight_data['airline'],
                    origin=flight_data['origin'],
                    destination=flight_data['destination'],
                    departure_time=flight_data['departure_time'],
                    arrival_time=flight_data['arrival_time'],
                    price=flight_data['price'],
                    currency=flight_data['currency'],
                    duration=flight_data['duration'],
                    aircraft=flight_data['aircraft']
                )
        return None
    
    def create_booking(self, flight: Flight, passengers_data: List[Dict], 
                      contact_email: str, contact_phone: str) -> Optional[Booking]:
        """Create a new flight booking"""
        try:
            # Simulate API delay
            time.sleep(Config.MOCK_API_DELAY)
            
            # Convert passenger data to Passenger objects
            passengers = []
            for passenger_data in passengers_data:
                passenger = Passenger(
                    first_name=passenger_data['first_name'],
                    last_name=passenger_data['last_name'],
                    dob=passenger_data['dob'],
                    passport_number=passenger_data['passport_number'],
                    nationality=passenger_data['nationality']
                )
                passengers.append(passenger)
            
            # Create booking
            booking = self.booking_manager.create_booking(
                flight=flight,
                passengers=passengers,
                contact_email=contact_email,
                contact_phone=contact_phone
            )
            
            return booking
            
        except Exception as e:
            print(f"Error creating booking: {e}")
            return None
    
    def add_special_requests(self, pnr: str, ssr_requests: List[Dict]) -> bool:
        """Add special service requests to booking"""
        try:
            # Simulate API delay
            time.sleep(Config.MOCK_API_DELAY * 0.5)
            
            ssr_objects = []
            for ssr_request in ssr_requests:
                ssr_type = ssr_request['type']
                preference = ssr_request['preference']
                
                # Get SSR code and description
                if ssr_type in SSR_CODES and preference in SSR_CODES[ssr_type]:
                    ssr_info = SSR_CODES[ssr_type][preference]
                    ssr = SpecialServiceRequest(
                        type=ssr_type.upper(),
                        code=ssr_info['code'],
                        description=ssr_info['description']
                    )
                    ssr_objects.append(ssr)
            
            return self.booking_manager.add_special_requests(pnr, ssr_objects)
            
        except Exception as e:
            print(f"Error adding special requests: {e}")
            return False
    
    def issue_ticket(self, pnr: str) -> bool:
        """Issue ticket for booking"""
        try:
            # Simulate API delay
            time.sleep(Config.MOCK_API_DELAY)
            
            return self.booking_manager.issue_ticket(pnr)
            
        except Exception as e:
            print(f"Error issuing ticket: {e}")
            return False
    
    def get_booking(self, pnr: str) -> Optional[Booking]:
        """Get booking details by PNR"""
        return self.booking_manager.get_booking(pnr)
    
    def format_flights_for_whatsapp(self, flights: List[Flight]) -> str:
        """Format flight list for WhatsApp display"""
        if not flights:
            return "❌ No flights found for your search criteria. Please try different dates or destinations."
        
        message = "✈️ *Available Flights:*\n\n"
        
        for i, flight in enumerate(flights, 1):
            message += flight.format_for_display(i)
            if i < len(flights):
                message += "\n\n" + "─" * 30 + "\n\n"
        
        message += f"\n\n📝 *How to select:*\nReply with the option number (e.g., type '*{1}*' or '*Option {1}*')"
        
        return message
    
    def validate_route(self, origin: str, destination: str) -> bool:
        """Check if route exists in our flight data"""
        for flight_data in self.flights_data['flights']:
            if (flight_data['origin'] == origin.upper() and 
                flight_data['destination'] == destination.upper()):
                return True
        return False
    
    def get_available_destinations_from(self, origin: str) -> List[str]:
        """Get list of available destinations from origin"""
        destinations = set()
        for flight_data in self.flights_data['flights']:
            if flight_data['origin'] == origin.upper():
                destinations.add(flight_data['destination'])
        return list(destinations)
    
    def get_available_origins_to(self, destination: str) -> List[str]:
        """Get list of available origins to destination"""
        origins = set()
        for flight_data in self.flights_data['flights']:
            if flight_data['destination'] == destination.upper():
                origins.add(flight_data['origin'])
        return list(origins)
    
    def get_price_range(self, origin: str, destination: str) -> Dict[str, int]:
        """Get price range for a route"""
        prices = []
        for flight_data in self.flights_data['flights']:
            if (flight_data['origin'] == origin.upper() and 
                flight_data['destination'] == destination.upper()):
                prices.append(flight_data['price'])
        
        if prices:
            return {
                'min_price': min(prices),
                'max_price': max(prices),
                'avg_price': sum(prices) // len(prices)
            }
        return {'min_price': 0, 'max_price': 0, 'avg_price': 0}

class MockAPIResponse:
    """Mock API response class for testing"""
    def __init__(self, success: bool, data: any = None, error: str = None):
        self.success = success
        self.data = data
        self.error = error
    
    def to_dict(self):
        return {
            'success': self.success,
            'data': self.data,
            'error': self.error
        } 