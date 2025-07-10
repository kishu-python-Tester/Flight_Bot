#!/usr/bin/env python3
"""
Debug fuzzy matching in city detection
"""

from services.intent_service import IntentService
from fuzzywuzzy import fuzz, process
import json

def debug_fuzzy_matching():
    """Debug the fuzzy matching issue"""
    print("🔍 Debugging Fuzzy Matching")
    print("=" * 50)
    
    intent_service = IntentService()
    
    # Get all city names and aliases
    all_city_names = []
    city_mapping = {}
    
    for city_key, city_data in intent_service.cities_data['cities'].items():
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
    
    print(f"Total city names/aliases: {len(all_city_names)}")
    print(f"Cities: {all_city_names}")
    
    # Test problematic phrase
    message = "I want to book a flight"
    print(f"\n🔍 Testing message: '{message}'")
    
    import re
    words = re.findall(r'\b\w+\b', message.lower())
    print(f"Words in message: {words}")
    
    for word in words:
        print(f"\n  Testing word: '{word}'")
        matches = process.extractBests(word, all_city_names, score_cutoff=80, limit=5)
        for match, score in matches:
            city_data = city_mapping[match]
            print(f"    Match: '{match}' -> {city_data['name']} ({city_data['iata']}) - Score: {score}")

if __name__ == "__main__":
    debug_fuzzy_matching() 