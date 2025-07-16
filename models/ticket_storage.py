"""
Persistent Ticket Storage System
Stores parsed ticket data that survives session timeouts
"""

import json
import os
import tempfile
from datetime import datetime, timedelta
from typing import Dict, Optional, Any
import logging

logger = logging.getLogger(__name__)

class TicketStorage:
    """Persistent storage for parsed ticket data"""
    
    def __init__(self):
        # Use temp directory for storage (in production, use database)
        self.storage_dir = os.path.join(tempfile.gettempdir(), 'flight_tickets')
        os.makedirs(self.storage_dir, exist_ok=True)
        
        # Ticket data expires after 24 hours
        self.expiry_hours = 24
    
    def _get_ticket_file_path(self, phone_number: str) -> str:
        """Get file path for user's ticket data"""
        # Clean phone number for filename
        clean_phone = phone_number.replace('+', '').replace('-', '').replace(' ', '')
        return os.path.join(self.storage_dir, f"ticket_{clean_phone}.json")
    
    def store_ticket_data(self, phone_number: str, ticket_info: Dict, price_comparison: Optional[Dict] = None) -> bool:
        """Store ticket and price comparison data persistently"""
        try:
            data = {
                'phone_number': phone_number,
                'stored_at': datetime.now().isoformat(),
                'expires_at': (datetime.now() + timedelta(hours=self.expiry_hours)).isoformat(),
                'ticket_info': ticket_info,
                'price_comparison': price_comparison
            }
            
            file_path = self._get_ticket_file_path(phone_number)
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.info(f"✅ Ticket data stored for {phone_number}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to store ticket data for {phone_number}: {e}")
            return False
    
    def get_ticket_data(self, phone_number: str) -> Optional[Dict]:
        """Retrieve stored ticket data if not expired"""
        try:
            file_path = self._get_ticket_file_path(phone_number)
            
            if not os.path.exists(file_path):
                return None
            
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            # Check if data has expired
            expires_at = datetime.fromisoformat(data['expires_at'])
            if datetime.now() > expires_at:
                # Clean up expired data
                os.remove(file_path)
                logger.info(f"🗑️ Expired ticket data removed for {phone_number}")
                return None
            
            logger.info(f"✅ Retrieved ticket data for {phone_number}")
            return data
            
        except Exception as e:
            logger.error(f"❌ Failed to retrieve ticket data for {phone_number}: {e}")
            return None
    
    def has_ticket_data(self, phone_number: str) -> bool:
        """Check if user has stored ticket data"""
        return self.get_ticket_data(phone_number) is not None
    
    def clear_ticket_data(self, phone_number: str) -> bool:
        """Clear stored ticket data for user"""
        try:
            file_path = self._get_ticket_file_path(phone_number)
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"🗑️ Ticket data cleared for {phone_number}")
                return True
            return False
        except Exception as e:
            logger.error(f"❌ Failed to clear ticket data for {phone_number}: {e}")
            return False
    
    def cleanup_expired_tickets(self) -> int:
        """Clean up all expired ticket files"""
        cleaned_count = 0
        try:
            if not os.path.exists(self.storage_dir):
                return 0
            
            for filename in os.listdir(self.storage_dir):
                if filename.startswith('ticket_') and filename.endswith('.json'):
                    file_path = os.path.join(self.storage_dir, filename)
                    
                    try:
                        with open(file_path, 'r') as f:
                            data = json.load(f)
                        
                        expires_at = datetime.fromisoformat(data['expires_at'])
                        if datetime.now() > expires_at:
                            os.remove(file_path)
                            cleaned_count += 1
                            
                    except Exception:
                        # Remove corrupted files
                        os.remove(file_path)
                        cleaned_count += 1
            
            if cleaned_count > 0:
                logger.info(f"🧹 Cleaned up {cleaned_count} expired ticket files")
                
        except Exception as e:
            logger.error(f"❌ Error during cleanup: {e}")
        
        return cleaned_count
    
    def get_storage_info(self) -> Dict:
        """Get information about ticket storage"""
        info = {
            'storage_dir': self.storage_dir,
            'total_tickets': 0,
            'expired_tickets': 0,
            'active_tickets': 0
        }
        
        try:
            if os.path.exists(self.storage_dir):
                for filename in os.listdir(self.storage_dir):
                    if filename.startswith('ticket_') and filename.endswith('.json'):
                        info['total_tickets'] += 1
                        
                        try:
                            file_path = os.path.join(self.storage_dir, filename)
                            with open(file_path, 'r') as f:
                                data = json.load(f)
                            
                            expires_at = datetime.fromisoformat(data['expires_at'])
                            if datetime.now() > expires_at:
                                info['expired_tickets'] += 1
                            else:
                                info['active_tickets'] += 1
                                
                        except Exception:
                            info['expired_tickets'] += 1
                            
        except Exception as e:
            logger.error(f"Error getting storage info: {e}")
        
        return info

# Global ticket storage instance
ticket_storage = TicketStorage() 