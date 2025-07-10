import re
import json
from datetime import datetime, date
from typing import Dict, Any, List, Optional

def format_phone_number(phone_number: str) -> str:
    """Format phone number to standard international format"""
    # Remove all non-digit characters
    digits_only = re.sub(r'[^\d]', '', phone_number)
    
    # Add + if not present
    if not digits_only.startswith('+'):
        digits_only = '+' + digits_only
    
    return digits_only

def validate_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_passport_number(passport: str) -> bool:
    """Validate passport number format"""
    # Basic validation - alphanumeric, 6-12 characters
    pattern = r'^[A-Z0-9]{6,12}$'
    return re.match(pattern, passport.upper()) is not None

def format_currency(amount: int, currency: str = 'INR') -> str:
    """Format currency amount with proper formatting"""
    if currency == 'INR':
        # Indian formatting with commas
        return f"₹{amount:,}"
    elif currency == 'USD':
        return f"${amount:,}"
    elif currency == 'EUR':
        return f"€{amount:,}"
    else:
        return f"{amount:,} {currency}"

def format_date_for_display(date_str: str) -> str:
    """Format date string for user-friendly display"""
    try:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        return date_obj.strftime('%B %d, %Y')  # e.g., "July 15, 2025"
    except:
        return date_str

def format_time_for_display(time_str: str) -> str:
    """Format time string for user-friendly display"""
    try:
        # Handle both HH:MM and HH:MM:SS formats
        if len(time_str.split(':')) == 2:
            time_obj = datetime.strptime(time_str, '%H:%M')
        else:
            time_obj = datetime.strptime(time_str, '%H:%M:%S')
        
        return time_obj.strftime('%I:%M %p')  # e.g., "02:30 PM"
    except:
        return time_str

def sanitize_input(text: str) -> str:
    """Sanitize user input"""
    # Remove potentially harmful characters
    sanitized = re.sub(r'[<>\"\'&]', '', text)
    # Limit length
    sanitized = sanitized[:500]
    return sanitized.strip()

def extract_numbers_from_text(text: str) -> List[int]:
    """Extract all numbers from text"""
    numbers = re.findall(r'\b\d+\b', text)
    return [int(num) for num in numbers]

def is_future_date(date_str: str) -> bool:
    """Check if date is in the future"""
    try:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
        return date_obj > date.today()
    except:
        return False

def calculate_age(birth_date: str) -> Optional[int]:
    """Calculate age from birth date"""
    try:
        birth_date_obj = datetime.strptime(birth_date, '%Y-%m-%d').date()
        today = date.today()
        age = today.year - birth_date_obj.year
        
        # Adjust if birthday hasn't occurred this year
        if today < birth_date_obj.replace(year=today.year):
            age -= 1
            
        return age
    except:
        return None

def format_duration(duration_str: str) -> str:
    """Format flight duration for display"""
    # Convert "5h 30m" to "5 hours 30 minutes"
    duration_str = duration_str.lower()
    
    # Extract hours and minutes
    hours_match = re.search(r'(\d+)h', duration_str)
    minutes_match = re.search(r'(\d+)m', duration_str)
    
    parts = []
    
    if hours_match:
        hours = int(hours_match.group(1))
        if hours == 1:
            parts.append("1 hour")
        else:
            parts.append(f"{hours} hours")
    
    if minutes_match:
        minutes = int(minutes_match.group(1))
        if minutes == 1:
            parts.append("1 minute")
        else:
            parts.append(f"{minutes} minutes")
    
    return " ".join(parts) if parts else duration_str

def create_error_response(error_type: str, details: str = '') -> Dict[str, Any]:
    """Create standardized error response"""
    error_messages = {
        'validation_error': 'Invalid input provided',
        'not_found': 'Requested resource not found',
        'server_error': 'Internal server error',
        'rate_limit': 'Too many requests',
        'unauthorized': 'Unauthorized access'
    }
    
    return {
        'error': True,
        'error_type': error_type,
        'message': error_messages.get(error_type, 'Unknown error'),
        'details': details,
        'timestamp': datetime.now().isoformat()
    }

def create_success_response(data: Any, message: str = 'Success') -> Dict[str, Any]:
    """Create standardized success response"""
    return {
        'success': True,
        'message': message,
        'data': data,
        'timestamp': datetime.now().isoformat()
    }

def log_conversation_event(phone_number: str, event_type: str, data: Dict = None):
    """Log conversation events for analytics"""
    log_entry = {
        'phone_number': phone_number,
        'event_type': event_type,
        'data': data or {},
        'timestamp': datetime.now().isoformat()
    }
    
    # In a real implementation, this would write to a logging service
    print(f"CONVERSATION_LOG: {json.dumps(log_entry)}")

def generate_reference_id(prefix: str = 'REF') -> str:
    """Generate a unique reference ID"""
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    return f"{prefix}{timestamp}"

def mask_sensitive_data(text: str) -> str:
    """Mask sensitive information in text for logging"""
    # Mask phone numbers
    text = re.sub(r'\+?\d{10,15}', lambda m: m.group(0)[:3] + '*' * (len(m.group(0)) - 6) + m.group(0)[-3:], text)
    
    # Mask email addresses
    text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', 
                  lambda m: m.group(0)[:3] + '*' * (len(m.group(0)) - 6) + m.group(0)[-3:], text)
    
    # Mask passport numbers (alphanumeric 6-12 chars)
    text = re.sub(r'\b[A-Z0-9]{6,12}\b', 
                  lambda m: m.group(0)[:2] + '*' * (len(m.group(0)) - 4) + m.group(0)[-2:], text)
    
    return text

def truncate_text(text: str, max_length: int = 100, suffix: str = '...') -> str:
    """Truncate text to specified length"""
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix

def parse_name(full_name: str) -> Dict[str, str]:
    """Parse full name into first and last names"""
    name_parts = full_name.strip().split()
    
    if len(name_parts) == 1:
        return {'first_name': name_parts[0], 'last_name': ''}
    elif len(name_parts) == 2:
        return {'first_name': name_parts[0], 'last_name': name_parts[1]}
    else:
        return {'first_name': name_parts[0], 'last_name': ' '.join(name_parts[1:])}

def validate_date_format(date_str: str, format_str: str = '%Y-%m-%d') -> bool:
    """Validate date format"""
    try:
        datetime.strptime(date_str, format_str)
        return True
    except ValueError:
        return False

def get_weekday_name(date_str: str) -> str:
    """Get weekday name from date string"""
    try:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        return date_obj.strftime('%A')  # e.g., "Monday"
    except:
        return ''

def format_whatsapp_message(text: str) -> str:
    """Format text for WhatsApp with proper emoji and formatting"""
    # Ensure proper spacing around emojis
    text = re.sub(r'([😀-🙿])', r' \1 ', text)
    
    # Clean up multiple spaces
    text = re.sub(r'\s+', ' ', text)
    
    # Ensure proper line breaks
    text = text.replace('\n\n\n', '\n\n')
    
    return text.strip() 