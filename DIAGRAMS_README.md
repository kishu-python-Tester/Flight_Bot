# 🛫 Flight Booking Chatbot - System Diagrams

This folder contains comprehensive architectural and flow diagrams for your Google Gemini AI-powered WhatsApp flight booking chatbot.

## 📋 Available Diagrams

### 1. System Architecture Diagram
**File:** Embedded in `flight_booking_diagrams.html`

**Shows:**
- External integrations (WhatsApp Business API, Google Gemini AI, Cloudflare Tunnel)
- Flask application layers (API, Core Services, Dialogue Management, Data Models)
- Data storage components (JSON files, in-memory sessions)
- Service interconnections and data flow

**Key Components:**
- **External Systems:** WhatsApp Business API, Google Gemini AI, Cloudflare Tunnel
- **API Layer:** Webhook endpoints, test endpoints, session management
- **Core Services:** WhatsApp service, LLM service, flight service, intent service
- **Dialogue Management:** LLM dialogue manager, session manager
- **Data Storage:** Flight database, city mappings, session storage

### 2. Conversation Flow Diagram
**File:** Embedded in `flight_booking_diagrams.html`

**Shows:**
- Complete user journey from initial message to booking completion
- 11-step booking workflow with state transitions
- Google Gemini AI integration points
- Smart reset logic and error handling
- Decision points and user interaction flows

**Conversation States:**
1. GREETING - Welcome and intent detection
2. COLLECT_SOURCE - Get departure city
3. COLLECT_DESTINATION - Get arrival city
4. COLLECT_DATE - Get travel date
5. COLLECT_PASSENGERS - Get passenger count
6. SHOW_FLIGHTS - Display available options
7. COLLECT_SELECTION - Get flight choice
8. COLLECT_PASSENGER_DETAILS - Get passenger info
9. COLLECT_SSR - Special service requests
10. CONFIRM_BOOKING - Final confirmation
11. COMPLETED - Booking finished

### 3. Data Flow Diagram
**File:** Embedded in `flight_booking_diagrams.html`

**Shows:**
- How data moves through the system from user input to response
- AI analysis pipeline with Google Gemini integration
- Business logic execution flow
- Data storage interactions
- Response generation and formatting

**Data Flow Stages:**
- User Input → Message Processing → AI Analysis → Business Logic → Response Generation

## 🔧 Technology Stack Highlighted

- **Backend:** Python Flask (Port 5001)
- **AI Engine:** Google Gemini 1.5-Flash
- **Communication:** WhatsApp Business API
- **Tunneling:** Cloudflare Tunnel
- **Data Storage:** JSON files + In-memory sessions
- **NLP:** Intent Service (fallback processing)
- **Session Management:** Custom session manager with state persistence

## 📄 Converting to PDF

### Method 1: Browser Print (Recommended)
```bash
python3 convert_to_pdf.py
```
This will:
1. Open the HTML file in your default browser
2. Provide step-by-step instructions for printing to PDF
3. Show alternative conversion methods

### Method 2: Automated Conversion
```bash
# Install dependencies first
python3 convert_to_pdf.py --install
brew install wkhtmltopdf  # macOS

# Then convert
python3 convert_to_pdf.py --pdfkit
```

### Method 3: Chrome Headless
```bash
google-chrome --headless --disable-gpu --print-to-pdf=flight_booking_diagrams.pdf flight_booking_diagrams.html
```

## 🎯 Key Features Documented

### AI-Powered Understanding
- **Google Gemini Integration:** Natural language processing with typo and slang support
- **Multi-language Support:** English, Hindi/Hinglish, Arabic phrases
- **WhatsApp Language:** Handles u, ur, r, 2moro, nxt, etc.
- **Intent Detection:** Smart recognition of booking intent in casual conversation

### Conversational Intelligence
- **Context Preservation:** Maintains conversation state across messages
- **Smart Reset Logic:** Detects when users want to start new bookings
- **Error Recovery:** Graceful handling of unclear inputs
- **Fallback Support:** Rule-based extraction as backup to AI

### Complete Booking System
- **End-to-End Workflow:** From intent detection to ticket issuance
- **Flight Search:** Integration with dummy flight database
- **Passenger Management:** Support for multiple passengers
- **Special Requests:** Meal preferences, seat selection, assistance
- **PNR Generation:** Booking confirmation and ticket issuance

### WhatsApp Integration
- **Webhook Handling:** Secure message receipt and verification
- **Response Formatting:** WhatsApp-optimized message formatting
- **Mock Service:** Development mode for testing without WhatsApp
- **Session Management:** Concurrent user support

## 📊 Diagram Usage

### For Documentation
- **System Overview:** Use architecture diagram for high-level system understanding
- **Process Documentation:** Use flow diagram for explaining booking workflow
- **Technical Specifications:** Use data flow diagram for implementation details

### For Development
- **Code Structure:** Architecture diagram shows how services interact
- **Debugging:** Flow diagram helps trace user journey issues
- **Data Tracking:** Data flow diagram shows information movement

### For Stakeholders
- **Business Process:** Conversation flow shows user experience
- **Technical Capabilities:** Architecture diagram demonstrates system sophistication
- **Integration Points:** Clear view of external dependencies

## 🔍 Understanding the Visual Elements

### Color Coding
- **Green (#25d366):** WhatsApp-related components
- **Blue (#4285f4):** Google Gemini AI components
- **Orange (#f38020):** Cloudflare infrastructure
- **Red (#ff6b6b):** Core dialogue management
- **Teal (#4ecdc4):** Flight service components
- **Yellow (#ffe66d):** Session management

### Connection Types
- **Solid Lines:** Direct service connections
- **Dashed Lines:** Optional or conditional flows
- **Bidirectional Arrows:** Two-way data exchange
- **Single Arrows:** One-way data flow

## 📁 Files Included

```
flight_book/
├── flight_booking_diagrams.html     # Complete diagram documentation
├── convert_to_pdf.py               # PDF conversion utility
├── DIAGRAMS_README.md              # This documentation
└── [rest of your project files]
```

## 🚀 Next Steps

1. **View Diagrams:** Open `flight_booking_diagrams.html` in your browser
2. **Generate PDF:** Run `python3 convert_to_pdf.py` for PDF version
3. **Share Documentation:** Use PDF for presentations and documentation
4. **Update Diagrams:** Modify HTML file as system evolves

## 💡 Tips for Presentation

- **Print Settings:** Use A4 paper, minimal margins, 80-90% scale
- **Background Graphics:** Enable to preserve colors and styling
- **Page Breaks:** Diagrams are designed to fit well on separate pages
- **High Quality:** Vector-based diagrams scale well for any size

---

*Generated for Flight Booking Chatbot v2.0 - Google Gemini Powered*
*Last Updated: December 2024* 