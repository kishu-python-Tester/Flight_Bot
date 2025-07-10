import re
import json
import os
from typing import Dict, List, Optional, Tuple
from dateutil.parser import parse as parse_date
from datetime import datetime, timedelta
from fuzzywuzzy import fuzz, process

class IntentService:
    def __init__(self):
        self.cities_data = self._load_cities_data()
        self.flight_booking_keywords = [
            'book flight', 'flight booking', 'book a flight', 'reserve flight',
            'travel', 'fly to', 'going to', 'trip to', 'want to fly',
            'need flight', 'flight ticket', 'air ticket', 'airline',
            'flight search', 'find flight', 'check flight'
        ]
        
        # Number patterns
        self.number_patterns = {
            'adults': r'(\d+)\s*adult',
            'children': r'(\d+)\s*child',
            'infants': r'(\d+)\s*infant',
            'passengers': r'(\d+)\s*passenger',
            'people': r'(\d+)\s*people',
            'pax': r'(\d+)\s*pax'
        }
    
    def _load_cities_data(self) -> Dict:
        """Load cities data from JSON file"""
        try:
            cities_file = os.path.join(os.path.dirname(__file__), '..', 'data', 'cities.json')
            with open(cities_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print("Cities data file not found")
            return {'cities': {}}
    
    def detect_flight_booking_intent(self, message: str) -> bool:
        """Detect if message indicates flight booking intent"""
        message_lower = message.lower()
        
        # Check for direct keywords
        for keyword in self.flight_booking_keywords:
            if keyword in message_lower:
                return True
        
        # Check for city names (might indicate travel intent)
        cities_mentioned = self.extract_cities(message)
        if len(cities_mentioned) >= 1:
            # Check if there are travel-related words
            travel_words = ['to', 'from', 'going', 'visiting', 'travel']
            for word in travel_words:
                if word in message_lower:
                    return True
        
        return False
    
    def extract_cities(self, message: str) -> List[Dict]:
        """Extract city names from message using fuzzy matching"""
        cities_found = []
        message_lower = message.lower()
        
        # Get all city names and aliases
        all_city_names = []
        city_mapping = {}
        
        for city_key, city_data in self.cities_data['cities'].items():
            # Add main city name
            city_name = city_data['name'].lower()
            all_city_names.append(city_name)
            city_mapping[city_name] = city_data
            
            # Add IATA code
            iata = city_data['iata'].lower()
            all_city_names.append(iata)
            city_mapping[iata] = city_data
            
            # Add aliases
            for alias in city_data.get('aliases', []):
                alias_lower = alias.lower()
                all_city_names.append(alias_lower)
                city_mapping[alias_lower] = city_data
        
        # Split message into words
        words = re.findall(r'\b\w+\b', message_lower)
        
        # Check each word and combination of words
        for i, word in enumerate(words):
            # Skip single letters and very short words to avoid false matches
            if len(word) < 3:
                continue
                
            # Check single word
            matches = process.extractBests(word, all_city_names, score_cutoff=85, limit=1)
            for match, score in matches:
                city_data = city_mapping[match]
                if city_data not in cities_found:
                    cities_found.append(city_data)
            
            # Check two-word combinations
            if i < len(words) - 1:
                two_word = f"{word} {words[i+1]}"
                # Only check two-word combinations if they're meaningful
                if len(two_word) >= 6:  # Minimum reasonable city name length
                    matches = process.extractBests(two_word, all_city_names, score_cutoff=85, limit=1)
                    for match, score in matches:
                        city_data = city_mapping[match]
                        if city_data not in cities_found:
                            cities_found.append(city_data)
        
        # Also check for exact IATA code matches (3 letters)
        iata_matches = re.findall(r'\b[A-Z]{3}\b', message.upper())
        for iata in iata_matches:
            iata_lower = iata.lower()
            if iata_lower in city_mapping:
                city_data = city_mapping[iata_lower]
                if city_data not in cities_found:
                    cities_found.append(city_data)
        
        return cities_found
    
    def extract_date(self, message: str) -> Optional[str]:
        """Extract date from message"""
        try:
            # Common date patterns
            date_patterns = [
                r'\b(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})\b',  # DD/MM/YYYY or MM/DD/YYYY
                r'\b(\d{1,2}\s+(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\w*\s*\d{2,4})\b',
                r'\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\w*\s+\d{1,2}\b',
                r'\b(today|tomorrow|next week|next month)\b',
                r'\b(\d{1,2})\s+(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\b'
            ]
            
            message_lower = message.lower()
            
            for pattern in date_patterns:
                matches = re.findall(pattern, message_lower, re.IGNORECASE)
                if matches:
                    date_str = matches[0] if isinstance(matches[0], str) else ' '.join(matches[0])
                    
                    # Handle special cases
                    if date_str == 'today':
                        return datetime.now().strftime('%Y-%m-%d')
                    elif date_str == 'tomorrow':
                        return (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
                    elif date_str == 'next week':
                        return (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
                    elif date_str == 'next month':
                        return (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
                    
                    # Try to parse the date
                    try:
                        parsed_date = parse_date(date_str, fuzzy=True)
                        # If year is not specified, assume current year
                        if parsed_date.year < datetime.now().year:
                            parsed_date = parsed_date.replace(year=datetime.now().year)
                        
                        # Don't allow past dates
                        if parsed_date.date() < datetime.now().date():
                            parsed_date = parsed_date.replace(year=datetime.now().year + 1)
                        
                        return parsed_date.strftime('%Y-%m-%d')
                    except:
                        continue
            
            return None
        except Exception as e:
            print(f"Error extracting date: {e}")
            return None
    
    def extract_passenger_count(self, message: str) -> Dict[str, int]:
        """Extract passenger counts from message"""
        passenger_counts = {'adults': 1, 'children': 0, 'infants': 0}
        message_lower = message.lower()
        
        # Look for specific passenger type mentions
        for passenger_type, pattern in self.number_patterns.items():
            matches = re.findall(pattern, message_lower)
            if matches:
                count = int(matches[0])
                if passenger_type == 'adults':
                    passenger_counts['adults'] = count
                elif passenger_type == 'children':
                    passenger_counts['children'] = count
                elif passenger_type == 'infants':
                    passenger_counts['infants'] = count
                elif passenger_type in ['passengers', 'people', 'pax']:
                    # Assume all are adults if not specified
                    passenger_counts['adults'] = count
        
        # Look for general numbers
        number_matches = re.findall(r'\b(\d+)\b', message_lower)
        if number_matches and not any(re.search(pattern, message_lower) for pattern in self.number_patterns.values()):
            # If we found a number but no specific passenger type, assume adults
            total_count = int(number_matches[0])
            if total_count <= 9:  # Reasonable passenger limit
                passenger_counts['adults'] = total_count
        
        # Special text patterns
        if 'just me' in message_lower or 'only me' in message_lower or 'myself' in message_lower:
            passenger_counts = {'adults': 1, 'children': 0, 'infants': 0}
        elif 'two' in message_lower or '2' in message:
            passenger_counts['adults'] = 2
        elif 'three' in message_lower or '3' in message:
            passenger_counts['adults'] = 3
        elif 'four' in message_lower or '4' in message:
            passenger_counts['adults'] = 4
        
        return passenger_counts
    
    def extract_flight_selection(self, message: str) -> Optional[int]:
        """Extract flight option selection from message"""
        message_lower = message.lower()
        
        # Look for "option 1", "option 2", etc.
        option_pattern = r'option\s*(\d+)'
        matches = re.findall(option_pattern, message_lower)
        if matches:
            return int(matches[0])
        
        # Look for just numbers
        number_pattern = r'^(\d+)$'
        matches = re.findall(number_pattern, message.strip())
        if matches:
            return int(matches[0])
        
        # Look for first, second, third, etc.
        ordinal_mapping = {
            'first': 1, '1st': 1,
            'second': 2, '2nd': 2,
            'third': 3, '3rd': 3,
            'fourth': 4, '4th': 4,
            'fifth': 5, '5th': 5
        }
        
        for ordinal, number in ordinal_mapping.items():
            if ordinal in message_lower:
                return number
        
        return None
    
    def extract_passenger_details(self, message: str) -> Optional[Dict]:
        """Extract passenger details from message"""
        try:
            # Expected format: "John Doe, 10-May-1990, A1234567, Indian"
            # or variations of this
            
            parts = [part.strip() for part in message.split(',')]
            if len(parts) >= 4:
                name_parts = parts[0].strip().split()
                if len(name_parts) >= 2:
                    first_name = name_parts[0]
                    last_name = ' '.join(name_parts[1:])
                    
                    dob_str = parts[1].strip()
                    try:
                        # Parse date of birth
                        dob = parse_date(dob_str, fuzzy=True)
                        dob_formatted = dob.strftime('%Y-%m-%d')
                    except:
                        return None
                    
                    passport = parts[2].strip()
                    nationality = parts[3].strip()
                    
                    return {
                        'first_name': first_name,
                        'last_name': last_name,
                        'dob': dob_formatted,
                        'passport_number': passport,
                        'nationality': nationality
                    }
            
            return None
        except Exception as e:
            print(f"Error extracting passenger details: {e}")
            return None
    
    def extract_ssr_requests(self, message: str) -> List[Dict]:
        """Extract special service requests from message"""
        ssr_requests = []
        message_lower = message.lower()
        
        # Meal preferences
        meal_keywords = {
            'vegetarian': 'vegetarian',
            'veg': 'vegetarian',
            'vegan': 'vegan',
            'halal': 'halal',
            'kosher': 'kosher',
            'diabetic': 'diabetic',
            'child meal': 'child'
        }
        
        for keyword, meal_type in meal_keywords.items():
            if keyword in message_lower:
                ssr_requests.append({
                    'type': 'meal',
                    'preference': meal_type
                })
        
        # Seat preferences
        if 'window' in message_lower:
            ssr_requests.append({
                'type': 'seat',
                'preference': 'window'
            })
        elif 'aisle' in message_lower:
            ssr_requests.append({
                'type': 'seat',
                'preference': 'aisle'
            })
        
        if 'extra legroom' in message_lower or 'legroom' in message_lower:
            ssr_requests.append({
                'type': 'seat',
                'preference': 'extra_legroom'
            })
        
        # Assistance requirements
        if 'wheelchair' in message_lower:
            ssr_requests.append({
                'type': 'assistance',
                'preference': 'wheelchair'
            })
        
        # Baggage
        if 'extra baggage' in message_lower or 'additional baggage' in message_lower:
            ssr_requests.append({
                'type': 'baggage',
                'preference': 'extra'
            })
        
        return ssr_requests
    
    def is_affirmative(self, message: str) -> bool:
        """Check if message is affirmative (yes, ok, etc.)"""
        affirmative_words = ['yes', 'ok', 'okay', 'sure', 'confirm', 'proceed', 'book it', 'go ahead']
        message_lower = message.lower().strip()
        
        return any(word in message_lower for word in affirmative_words)
    
    def is_negative(self, message: str) -> bool:
        """Check if message is negative (no, cancel, etc.)"""
        negative_words = ['no', 'cancel', 'stop', 'quit', 'exit', 'abort']
        message_lower = message.lower().strip()
        
        return any(word in message_lower for word in negative_words) 