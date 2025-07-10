from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, Optional, Any
import time

class ConversationState(Enum):
    GREETING = "greeting"
    COLLECT_SOURCE = "collect_source"
    COLLECT_DESTINATION = "collect_destination"
    COLLECT_DATE = "collect_date"
    COLLECT_PASSENGERS = "collect_passengers"
    SHOW_FLIGHTS = "show_flights"
    COLLECT_SELECTION = "collect_selection"
    COLLECT_PASSENGER_DETAILS = "collect_passenger_details"
    COLLECT_SSR = "collect_ssr"
    CONFIRM_BOOKING = "confirm_booking"
    COMPLETED = "completed"

class ConversationSession:
    def __init__(self, phone_number: str):
        self.phone_number = phone_number
        self.state = ConversationState.GREETING
        self.created_at = datetime.now()
        self.last_activity = datetime.now()
        self.data = {
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
        self.context = {
            'last_message': None,
            'retry_count': 0,
            'error_message': None,
            'available_flights': []
        }
    
    def update_activity(self):
        """Update last activity timestamp"""
        self.last_activity = datetime.now()
    
    def is_expired(self, timeout_minutes: int = 30) -> bool:
        """Check if session has expired"""
        expiry_time = self.last_activity + timedelta(minutes=timeout_minutes)
        return datetime.now() > expiry_time
    
    def set_state(self, new_state: ConversationState):
        """Update conversation state"""
        self.state = new_state
        self.update_activity()
        # Reset retry count when moving to new state
        self.context['retry_count'] = 0
    
    def set_data(self, key: str, value: Any):
        """Set data in conversation context"""
        self.data[key] = value
        self.update_activity()
    
    def get_data(self, key: str, default=None):
        """Get data from conversation context"""
        return self.data.get(key, default)
    
    def set_context(self, key: str, value: Any):
        """Set context information"""
        self.context[key] = value
        self.update_activity()
    
    def get_context(self, key: str, default=None):
        """Get context information"""
        return self.context.get(key, default)
    
    def increment_retry(self):
        """Increment retry count for current state"""
        self.context['retry_count'] = self.context.get('retry_count', 0) + 1
    
    def reset_retry(self):
        """Reset retry count"""
        self.context['retry_count'] = 0
    
    def get_retry_count(self) -> int:
        """Get current retry count"""
        return self.context.get('retry_count', 0)
    
    def to_dict(self) -> Dict:
        """Convert session to dictionary for storage/logging"""
        return {
            'phone_number': self.phone_number,
            'state': self.state.value,
            'created_at': self.created_at.isoformat(),
            'last_activity': self.last_activity.isoformat(),
            'data': self.data,
            'context': self.context
        }

class SessionManager:
    def __init__(self):
        self.sessions: Dict[str, ConversationSession] = {}
    
    def get_session(self, phone_number: str) -> ConversationSession:
        """Get or create session for phone number"""
        if phone_number not in self.sessions:
            self.sessions[phone_number] = ConversationSession(phone_number)
        else:
            # Check if session is expired
            session = self.sessions[phone_number]
            if session.is_expired():
                # Create new session
                self.sessions[phone_number] = ConversationSession(phone_number)
        
        return self.sessions[phone_number]
    
    def cleanup_expired_sessions(self, timeout_minutes: int = 30):
        """Remove expired sessions"""
        expired_sessions = []
        for phone_number, session in self.sessions.items():
            if session.is_expired(timeout_minutes):
                expired_sessions.append(phone_number)
        
        for phone_number in expired_sessions:
            del self.sessions[phone_number]
    
    def get_active_sessions_count(self) -> int:
        """Get count of active sessions"""
        return len(self.sessions)
    
    def reset_session(self, phone_number: str):
        """Reset session for phone number"""
        if phone_number in self.sessions:
            del self.sessions[phone_number] 