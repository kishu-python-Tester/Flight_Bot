from dataclasses import dataclass
from typing import List, Optional, Dict
from datetime import datetime
import json
import random
import string

@dataclass
class Flight:
    flight_id: str
    airline: str
    origin: str
    destination: str
    departure_time: str
    arrival_time: str
    price: int
    currency: str
    duration: str
    aircraft: str
    
    def to_dict(self) -> Dict:
        return {
            'flight_id': self.flight_id,
            'airline': self.airline,
            'origin': self.origin,
            'destination': self.destination,
            'departure_time': self.departure_time,
            'arrival_time': self.arrival_time,
            'price': self.price,
            'currency': self.currency,
            'duration': self.duration,
            'aircraft': self.aircraft
        }
    
    def format_for_display(self, index: int) -> str:
        """Format flight for WhatsApp display"""
        return f"""✈️ *Option {index}*
🛫 {self.airline} - {self.flight_id}
🕐 {self.departure_time} → {self.arrival_time}
💰 ₹{self.price:,}
⏱️ Duration: {self.duration}
✈️ Aircraft: {self.aircraft}"""

@dataclass
class Passenger:
    first_name: str
    last_name: str
    dob: str  # YYYY-MM-DD format
    passport_number: str
    nationality: str
    
    def to_dict(self) -> Dict:
        return {
            'first_name': self.first_name,
            'last_name': self.last_name,
            'dob': self.dob,
            'passport_number': self.passport_number,
            'nationality': self.nationality
        }

@dataclass
class SpecialServiceRequest:
    type: str  # MEAL, SEAT, ASSISTANCE, etc.
    code: str  # VGML, 12A, WCHR, etc.
    description: str
    
    def to_dict(self) -> Dict:
        return {
            'type': self.type,
            'code': self.code,
            'description': self.description
        }

@dataclass
class Booking:
    pnr: str
    flight: Flight
    passengers: List[Passenger]
    contact_email: str
    contact_phone: str
    special_requests: List[SpecialServiceRequest]
    booking_date: datetime
    status: str  # CONFIRMED, PENDING, CANCELLED
    ticket_issued: bool = False
    
    def to_dict(self) -> Dict:
        return {
            'pnr': self.pnr,
            'flight': self.flight.to_dict(),
            'passengers': [p.to_dict() for p in self.passengers],
            'contact_email': self.contact_email,
            'contact_phone': self.contact_phone,
            'special_requests': [ssr.to_dict() for ssr in self.special_requests],
            'booking_date': self.booking_date.isoformat(),
            'status': self.status,
            'ticket_issued': self.ticket_issued
        }
    
    def generate_confirmation_message(self) -> str:
        """Generate booking confirmation message for WhatsApp"""
        ssr_text = ""
        if self.special_requests:
            ssr_list = [f"• {ssr.description}" for ssr in self.special_requests]
            ssr_text = f"\n\n🍽️ *Special Requests:*\n" + "\n".join(ssr_list)
        
        passenger_text = ""
        if len(self.passengers) == 1:
            passenger_text = f"👤 *Passenger:* {self.passengers[0].first_name} {self.passengers[0].last_name}"
        else:
            passenger_names = [f"• {p.first_name} {p.last_name}" for p in self.passengers]
            passenger_text = f"👥 *Passengers:*\n" + "\n".join(passenger_names)
        
        return f"""🎫 *BOOKING CONFIRMED!*

📋 *PNR:* {self.pnr}
✈️ *Flight:* {self.flight.airline} {self.flight.flight_id}
🛫 *Route:* {self.flight.origin} → {self.flight.destination}
🕐 *Time:* {self.flight.departure_time} - {self.flight.arrival_time}
💰 *Price:* ₹{self.flight.price:,}

{passenger_text}{ssr_text}

📧 Confirmation sent to: {self.contact_email}
📱 SMS sent to: {self.contact_phone}

✅ *Status:* {self.status}
🎟️ *Ticket:* {'Issued' if self.ticket_issued else 'Will be issued shortly'}

Thank you for booking with us! 🙏"""

class BookingManager:
    def __init__(self):
        self.bookings: Dict[str, Booking] = {}
    
    def generate_pnr(self) -> str:
        """Generate a random PNR"""
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    
    def create_booking(self, flight: Flight, passengers: List[Passenger], 
                      contact_email: str, contact_phone: str) -> Booking:
        """Create a new booking"""
        pnr = self.generate_pnr()
        while pnr in self.bookings:  # Ensure unique PNR
            pnr = self.generate_pnr()
        
        booking = Booking(
            pnr=pnr,
            flight=flight,
            passengers=passengers,
            contact_email=contact_email,
            contact_phone=contact_phone,
            special_requests=[],
            booking_date=datetime.now(),
            status="CONFIRMED",
            ticket_issued=False
        )
        
        self.bookings[pnr] = booking
        return booking
    
    def add_special_requests(self, pnr: str, ssr_list: List[SpecialServiceRequest]) -> bool:
        """Add special service requests to booking"""
        if pnr in self.bookings:
            self.bookings[pnr].special_requests.extend(ssr_list)
            return True
        return False
    
    def issue_ticket(self, pnr: str) -> bool:
        """Issue ticket for booking"""
        if pnr in self.bookings:
            self.bookings[pnr].ticket_issued = True
            return True
        return False
    
    def get_booking(self, pnr: str) -> Optional[Booking]:
        """Get booking by PNR"""
        return self.bookings.get(pnr)

# SSR Code mappings
SSR_CODES = {
    'meal': {
        'vegetarian': {'code': 'VGML', 'description': 'Vegetarian Meal'},
        'vegan': {'code': 'VLML', 'description': 'Vegan Meal'},
        'halal': {'code': 'MOML', 'description': 'Halal Meal'},
        'kosher': {'code': 'KSML', 'description': 'Kosher Meal'},
        'diabetic': {'code': 'DBML', 'description': 'Diabetic Meal'},
        'child': {'code': 'CHML', 'description': 'Child Meal'}
    },
    'seat': {
        'window': {'code': 'WINDOW', 'description': 'Window Seat Preference'},
        'aisle': {'code': 'AISLE', 'description': 'Aisle Seat Preference'},
        'extra_legroom': {'code': 'LEGROOM', 'description': 'Extra Legroom Seat'}
    },
    'assistance': {
        'wheelchair': {'code': 'WCHR', 'description': 'Wheelchair Assistance'},
        'blind': {'code': 'BLND', 'description': 'Assistance for Blind Passenger'},
        'deaf': {'code': 'DEAF', 'description': 'Assistance for Deaf Passenger'}
    },
    'baggage': {
        'extra': {'code': 'XBAG', 'description': 'Extra Baggage (15kg)'},
        'sports': {'code': 'SPBG', 'description': 'Sports Equipment'}
    }
} 