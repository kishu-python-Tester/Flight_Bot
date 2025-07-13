# ✈️ WhatsApp Flight Booking Chatbot - Google Gemini Powered

A complete AI-powered flight booking assistant that integrates with WhatsApp Business API and uses Google's advanced Gemini AI for natural conversation understanding. This chatbot can handle the entire flight booking workflow through intelligent natural language conversations.

## 🌟 Features

- **🧠 Google Gemini-Powered Natural Language Understanding**: Uses Google's latest Gemini AI models for superior conversation understanding
- **🗣️ Natural Conversation Flow**: Users can express their travel needs in their own words
- **✈️ Complete Booking Workflow**: Handles the full 11-step flight booking process
- **📱 WhatsApp Integration**: Works seamlessly with WhatsApp Business API
- **🎭 Mock API Support**: Uses dummy data for testing without external API dependencies
- **💾 Session Management**: Maintains conversation state across multiple messages
- **🛡️ Error Handling**: Graceful handling of unclear inputs and failures
- **👥 Multi-passenger Support**: Handles individual and group bookings
- **🍽️ Special Requests**: Supports meal preferences, seat selection, and assistance requests
- **🔄 Fallback Support**: Combines Gemini intelligence with rule-based extraction for reliability

## 📋 Requirements

- Python 3.8+
- Flask 2.3+
- Google AI API account (for Gemini features)
- WhatsApp Business API account (for production)
- ngrok or Cloudflare Tunnel (for local testing)

## 🚀 Quick Start

### 1. Clone and Setup

```bash
git clone <repository-url>
cd flight_book
pip install -r requirements.txt
```

### 2. Configure Environment

Copy the environment template:
```bash
cp env.example .env
```

Edit `.env` file with your credentials:
```env
# WhatsApp Business API Configuration
WHATSAPP_TOKEN=your_whatsapp_access_token_here
WHATSAPP_PHONE_NUMBER_ID=your_whatsapp_phone_number_id_here
WHATSAPP_VERIFY_TOKEN=flight_booking_verify_token_123

# Google AI Configuration (Required for Gemini features)
GOOGLE_API_KEY=your_google_api_key_here

# Application Configuration
FLASK_ENV=development
```

### 3. Run the Application

```bash
python app.py
```

The application will start on `http://localhost:5001`

## 🧪 Testing

### Option 1: Web Interface Testing

1. Visit `http://localhost:5001/test`
2. Use the web interface to send test messages
3. Try natural language messages like:
   - "I want to go to Dubai tomorrow"
   - "Book me a flight from Delhi to Mumbai"
   - "I need tickets for 2 people to London"

### Option 2: API Testing with curl

```bash
# Natural language booking request
curl -X POST http://localhost:5001/test \
     -H "Content-Type: application/json" \
     -d '{"phone_number": "+1234567890", "message": "I want to go to Dubai tomorrow"}'

# Incomplete request (Gemini will ask for missing info)
curl -X POST http://localhost:5001/test \
     -H "Content-Type: application/json" \
     -d '{"phone_number": "+1234567890", "message": "Book a flight"}'
```

### Natural Language Test Examples

Google Gemini can understand various ways of expressing travel intent:

1. **Complete requests**: `"I want to fly from Delhi to Dubai tomorrow for 2 people"`
2. **Partial requests**: `"Going to London next week"`
3. **Casual language**: `"Need tickets to Singapore"`
4. **Specific requests**: `"Book me a flight from Mumbai to Bangkok on July 15"`
5. **Conversational**: `"Hello, I'm planning a trip to Dubai"`

## 🏗️ Project Structure

```
flight_book/
├── app.py                          # Main Flask application  
├── requirements.txt                # Python dependencies (includes google-generativeai)
├── config/
│   └── settings.py                # Configuration (includes Google API key)
├── models/
│   ├── conversation.py            # Session and state management
│   └── flight_data.py             # Flight and booking data models
├── services/
│   ├── llm_service.py             # 🧠 Google Gemini integration service
│   ├── llm_dialogue_manager.py    # 🤖 Gemini-powered conversation manager
│   ├── intent_service.py          # Fallback intent recognition and NLP
│   ├── dialogue_manager.py        # Legacy rule-based manager
│   ├── flight_service.py          # Flight search and booking logic
│   └── whatsapp_service.py        # WhatsApp API integration
├── data/
│   ├── dummy_flights.json         # Mock flight database
│   └── cities.json               # City and IATA code mapping
├── utils/
│   └── helpers.py                # Utility functions
├── env.example                   # Environment variables template
├── PRD.md                       # Product Requirements Document
└── README.md                    # This file
```

## 🧠 Google Gemini Integration

### How It Works

1. **Message Analysis**: Google Gemini analyzes user messages to understand intent and extract information
2. **Smart Extraction**: Combines Gemini intelligence with rule-based fallbacks
3. **Context Awareness**: Maintains conversation context for follow-up questions
4. **Flexible Understanding**: Handles various ways of expressing the same intent

### Gemini Capabilities

- **Intent Recognition**: Determines if message is flight-booking related
- **Information Extraction**: Pulls out cities, dates, passenger counts from natural language
- **Next Question Generation**: Intelligently asks for missing information
- **Error Recovery**: Handles unclear or incomplete requests gracefully
- **JSON Response Parsing**: Handles Gemini's markdown formatting automatically

### Fallback Strategy

- Primary: Google Gemini analysis for natural language understanding
- Secondary: Rule-based extraction for structured data (cities, dates, flight selection)
- Tertiary: Human handoff for complex cases

## 📱 WhatsApp Integration

### For Development (Mock Mode)

The application automatically uses Mock WhatsApp Service when:
- `FLASK_ENV=development` 
- `WHATSAPP_TOKEN` is not set or is the default value

In mock mode, messages are printed to console instead of being sent to WhatsApp.

### For Production (Real WhatsApp)

1. **Setup WhatsApp Business API**:
   - Create a Meta Developer account
   - Set up WhatsApp Business API
   - Get your access token and phone number ID

2. **Configure Webhook**:
   - Use ngrok to expose your local server: `ngrok http 5001`
   - Set webhook URL in Meta Developer Console to: `https://your-ngrok-url.ngrok.io/webhook`
   - Set verify token to match your `WHATSAPP_VERIFY_TOKEN`

3. **Update Environment**:
   ```env
   FLASK_ENV=production
   WHATSAPP_TOKEN=your_actual_token
   WHATSAPP_PHONE_NUMBER_ID=your_actual_phone_number_id
   ```

## 🛠️ API Endpoints

### Core Endpoints

- `GET /` - Health check
- `GET /webhook` - WhatsApp webhook verification
- `POST /webhook` - WhatsApp message handling

### Testing Endpoints

- `GET /test` - Web interface for testing
- `POST /test` - Send test messages
- `GET /sessions` - View active sessions
- `DELETE /sessions/<phone_number>` - Reset specific session

### Example API Usage

```bash
# Check application status
curl http://localhost:5001/

# View active sessions
curl http://localhost:5001/sessions

# Reset a session
curl -X DELETE http://localhost:5001/sessions/+1234567890
```

## 🎯 Conversation Flow

The chatbot follows this 11-step workflow:

1. **Intent Detection** - Recognizes flight booking intent
2. **Source Collection** - Asks for departure city
3. **Destination Collection** - Asks for arrival city
4. **Date Collection** - Asks for travel date
5. **Passenger Collection** - Asks for number of travelers
6. **Flight Search** - Searches and displays available flights
7. **Flight Selection** - User selects preferred flight
8. **Passenger Details** - Collects passenger information
9. **Special Requests** - Asks for meal/seat preferences
10. **Booking Confirmation** - Shows summary and confirms
11. **Ticket Issuance** - Creates booking and issues ticket

## 🏙️ Supported Cities

The system includes dummy data for flights between these cities:

**India**: Delhi (DEL), Mumbai (BOM), Bangalore (BLR), Hyderabad (HYD), Chennai (MAA), Kolkata (CCU)

**International**: Dubai (DXB), Abu Dhabi (AUH), London (LHR), New York (JFK), Singapore (SIN), Bangkok (BKK)

## ✈️ Available Routes

Sample routes with dummy flights:
- Delhi ↔ Dubai (Air India, Emirates, IndiGo)
- Mumbai ↔ Dubai (Air India, Emirates)
- Delhi ↔ London (Air India, British Airways)
- Delhi ↔ Bangalore (IndiGo, Air India, SpiceJet)
- Mumbai ↔ Singapore (Air India, Singapore Airlines)
- Delhi ↔ Bangkok (Thai Airways, Air India)

## 🍽️ Special Services

Supported special service requests:

**Meals**: Vegetarian, Vegan, Halal, Kosher, Diabetic, Child meal

**Seats**: Window, Aisle, Extra legroom

**Assistance**: Wheelchair, Blind passenger, Deaf passenger

**Baggage**: Extra baggage, Sports equipment

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GOOGLE_API_KEY` | Google AI API key for Gemini features | Required for AI features |
| `WHATSAPP_TOKEN` | WhatsApp Business API access token | Required for production |
| `WHATSAPP_PHONE_NUMBER_ID` | Your WhatsApp phone number ID | Required for production |
| `WHATSAPP_VERIFY_TOKEN` | Webhook verification token | `flight_booking_verify_token` |
| `FLASK_ENV` | Application environment | `development` |
| `DEBUG` | Enable debug mode | `True` |
| `PORT` | Application port | `5001` |
| `LOG_LEVEL` | Logging level | `INFO` |

### AI vs Rule-based Mode

**Gemini Mode** (Default):
- Uses Google Gemini for natural language understanding
- Handles conversational and partial requests
- More flexible and user-friendly

**Rule-based Fallback**:
- Uses pattern matching for specific extractions
- Faster but less flexible
- Always available as backup

## 📊 Monitoring and Logging

### Available Logs

- Conversation events and state changes
- API request/response logs
- Error tracking and debugging
- Session management events

### Session Management

- Automatic session cleanup after 30 minutes of inactivity
- Session state persistence across messages
- Support for concurrent users

## 🚨 Error Handling

The system handles various error scenarios:

- **Invalid city names**: Suggests alternatives
- **Invalid dates**: Provides format examples
- **No flights found**: Suggests different dates/destinations
- **Booking failures**: Offers human support
- **Retry limit exceeded**: Transfers to human agent

## 📈 Scalability

### Current Architecture
- In-memory session storage
- Single Flask instance
- Suitable for development and small-scale testing

### Production Recommendations
- Redis for session storage
- Horizontal scaling with load balancer
- Database for persistent booking storage
- Message queue for async processing

## 🔒 Security

- Input sanitization and validation
- Webhook signature verification
- Sensitive data masking in logs
- Rate limiting support
- HTTPS enforcement in production

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 🐛 Troubleshooting

### Common Issues

**Issue**: Mock service not working
**Solution**: Ensure `FLASK_ENV=development` in your environment

**Issue**: WhatsApp webhook verification fails
**Solution**: Check that your `WHATSAPP_VERIFY_TOKEN` matches the one configured in Meta Developer Console

**Issue**: No flights found
**Solution**: Verify that you're using supported city names from the cities.json file

**Issue**: Session state lost
**Solution**: Sessions expire after 30 minutes of inactivity; start a new conversation

**Issue**: Gemini API errors
**Solution**: Verify your `GOOGLE_API_KEY` is valid and has quota available

### Debug Mode

Run with debug logging:
```bash
LOG_LEVEL=DEBUG python app.py
```

## 📞 Support

For issues and questions:
1. Check the troubleshooting section
2. Review the logs for error details
3. Test with the mock interface first
4. Create an issue with detailed information

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Built according to the PRD specifications
- Uses WhatsApp Business API
- Powered by Google's advanced Gemini AI
- Implements industry-standard conversation flow patterns
- Follows best practices for chatbot development

---

**Note**: This is a demonstration project using dummy flight data. In a production environment, integrate with real flight booking APIs and payment systems. 