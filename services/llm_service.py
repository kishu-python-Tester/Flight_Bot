import json
import logging
from typing import Dict, Optional, List
import google.generativeai as genai
from config.settings import Config

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self):
        # Configure Google AI
        genai.configure(api_key=Config.GOOGLE_API_KEY)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        
    def analyze_flight_booking_message(self, message: str, current_data: Dict) -> Dict:
        """
        Use Google Gemini to analyze user message and extract flight booking information
        """
        
        system_prompt = """You are an intelligent multilingual flight booking assistant that understands casual WhatsApp language, typos, abbreviations, and multiple languages.

LANGUAGE UNDERSTANDING:
- English: book flight, need ticket, want to travel, going to, trip to, fly to
- Hindi/Hinglish: flight book karna hai, ticket chahiye, jaana hai, travel karna
- Arabic: أريد حجز رحلة, تذكرة طيران, سفر, الى
- Common typos: flght, tiket, travle, goin, tomorow, nxt week
- WhatsApp language: u, ur, r, 2moro, nxt, pls, thnx, asap, btw
- Casual: wanna, gonna, lemme, can u help

TRAVEL INTENT DETECTION (ANY of these indicate flight booking):
- Direct: "book flight", "need flight", "flight ticket", "air ticket"
- Travel words: "travel", "trip", "vacation", "visit", "go to", "going to"
- Destination focus: "I want to go to Mumbai", "need to reach Delhi"
- Time expressions: "traveling tomorrow", "next week trip", "weekend getaway"
- Planning: "planning a trip", "thinking of visiting", "want to see"
- Business: "meeting in Dubai", "conference in London", "work travel"
- Family: "visiting family", "wedding in India", "taking kids to"

CITY NAME VARIATIONS:
- Delhi: del, dli, new delhi, ndls, दिल्ली
- Mumbai: bom, bombay, मुंबई
- Bangalore: blr, bengaluru, bang, बेंगलुरु  
- Dubai: dxb, دبي
- London: lhr, heathrow, लंदन
- Be flexible with spellings: mumabi→Mumbai, deli→Delhi, bangalor→Bangalore

DATE UNDERSTANDING:
- Relative: today, tomorrow (tom/tmrw/2moro), next week, this weekend
- Casual: Monday, Tuesday, next Monday, coming Sunday
- Numeric: 25th, 25 aug, aug 25, 25/8, 8/25
- Convert to YYYY-MM-DD format (assume current year 2024)

PASSENGER DETECTION:
- "me and my wife" = 2 adults
- "family of 4" = 4 people (assume adults unless specified)
- "with 2 kids" = current adults + 2 children
- "myself" = 1 adult
- Numbers: "for 3 people", "3 pax", "3 tickets"

Current booking data: {current_data}

Respond ONLY with valid JSON:
{
    "intent": "flight_booking" | "other",
    "extracted_data": {
        "source_city": "exact_city_name" | null,
        "destination_city": "exact_city_name" | null, 
        "departure_date": "YYYY-MM-DD" | null,
        "adults": number,
        "children": number,
        "infants": number
    },
    "confidence": 0.0-1.0,
    "next_question": "Next question in friendly WhatsApp style",
    "reasoning": "What was understood from the message"
}"""

        user_prompt = f"""
Current booking data: {json.dumps(current_data)}
User message: "{message}"

Analyze this message and determine what flight booking information can be extracted and what should be asked next.

{system_prompt}
"""

        try:
            response = self.model.generate_content(user_prompt)
            
            # Extract JSON from response
            response_text = response.text.strip()
            
            # Sometimes Gemini wraps JSON in markdown code blocks
            if response_text.startswith('```json'):
                response_text = response_text[7:-3].strip()
            elif response_text.startswith('```'):
                response_text = response_text[3:-3].strip()
                
            result = json.loads(response_text)
            logger.info(f"Gemini Analysis: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Gemini analysis error: {e}")
            return {
                "intent": "flight_booking",
                "extracted_data": {},
                "confidence": 0.5,
                "next_question": "I'd like to help you book a flight. Which city would you like to fly from?",
                "reasoning": "Error in Gemini processing, using fallback"
            }
    
    def generate_response(self, analysis: Dict, session_data: Dict) -> str:
        """Generate appropriate response based on Gemini analysis"""
        
        if analysis["intent"] != "flight_booking":
            # Generate contextual non-booking response
            return self._generate_non_booking_response(analysis, session_data)
        
        # Build response with extracted understanding
        reasoning = analysis.get("reasoning", "")
        next_question = analysis.get("next_question", "Where would you like to fly? 😊")
        confidence = analysis.get("confidence", 0.5)
        
        # More natural, WhatsApp-style responses
        if reasoning and confidence > 0.7:
            return f"""✈️ *Got it!* {reasoning}

{next_question}"""
        else:
            return f"""🛫 *Perfect! Let's get your flight booked.*

{next_question}"""
    
    def _generate_non_booking_response(self, analysis: Dict, session_data: Dict) -> str:
        """Generate response for non-booking messages"""
        
        non_booking_prompt = f"""The user sent a message that doesn't seem to be about flight booking.

User message: "{analysis.get('reasoning', 'Unknown message')}"

Generate a helpful, friendly WhatsApp-style response that:
1. Acknowledges their message politely
2. Gently redirects to flight booking 
3. Shows examples of how they can book flights in natural language
4. Uses emojis and casual tone
5. Keep it short and friendly

Respond with just the message text, no JSON."""

        try:
            response = self.model.generate_content(non_booking_prompt)
            return response.text.strip()
        except Exception as e:
            logger.error(f"Non-booking response error: {e}")
            return """✈️ *Hi there!*

I'm here to help you book flights easily! Just tell me where you want to go in your own words 😊

*Examples:*
• "wanna go to mumbai tomorrow"
• "need flight delhi to dubai" 
• "traveling to london next week"
• "मुझे दुबई जाना है" (Hindi)

*What's your travel plan?* 🛫"""
    
    def smart_city_extraction(self, message: str) -> List[str]:
        """Use Gemini to extract city names from message with multilingual support"""
        
        prompt = f"""Extract city names from this message. Handle typos, multiple languages, and variations.

AVAILABLE CITIES & VARIATIONS:
- Delhi (दिल्ली): del, dli, new delhi, ndls, dilli
- Mumbai (मुंबई): bom, bombay, mumabi, mumbai
- Bangalore (बेंगलुरु): blr, bengaluru, bang, bangalor, banguluru
- Hyderabad: hyd, hydrabad, حيدرآباد
- Chennai: maa, madras, चेन्नई
- Kolkata: ccu, calcutta, कोलकाता
- Dubai (دبي): dxb, dubay, دبى
- Abu Dhabi: auh, abudhabi, أبو ظبي
- London (लंदन): lhr, heathrow, lndn
- Singapore: sin, singapur, सिंगापुर
- Bangkok: bkk, bangkk, बैंकॉक
- New York: jfk, nyc, newyork

RULES:
1. Match variations, typos, and different languages
2. Return exact city names from the main list above (Delhi, Mumbai, etc.)
3. Consider word order: "mumbai to delhi" vs "delhi mumbai"
4. Handle "from X to Y" patterns
5. If only one city mentioned, include it

Message: "{message}"

Return JSON array of exact city names: ["City1", "City2"]"""

        try:
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            
            # Clean up markdown formatting if present
            if response_text.startswith('```json'):
                response_text = response_text[7:-3].strip()
            elif response_text.startswith('```'):
                response_text = response_text[3:-3].strip()
            
            cities = json.loads(response_text)
            return cities if isinstance(cities, list) else []
            
        except Exception as e:
            logger.error(f"Enhanced city extraction error: {e}")
            return []
    
    def test_natural_language_understanding(self, test_messages: List[str]) -> None:
        """Test function to validate natural language understanding"""
        print("🧪 Testing Natural Language Understanding:\n")
        
        for i, message in enumerate(test_messages, 1):
            print(f"{i}. Testing: '{message}'")
            try:
                analysis = self.analyze_flight_booking_message(message, {
                    "source_city": None, "destination_city": None, 
                    "departure_date": None, "adults": 1, "children": 0, "infants": 0
                })
                
                print(f"   Intent: {analysis['intent']} (confidence: {analysis.get('confidence', 0):.2f})")
                print(f"   Extracted: {analysis.get('extracted_data', {})}")
                print(f"   Next Q: {analysis.get('next_question', 'N/A')}")
                print()
                
            except Exception as e:
                print(f"   ❌ Error: {e}\n")
        
        print("✅ Testing complete!") 