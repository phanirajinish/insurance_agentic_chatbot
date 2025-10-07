# Apollo 24|7 Insurance Chatbot 🛡️

An intelligent, conversational AI chatbot for health insurance recommendations powered by RAG (Retrieval-Augmented Generation) and OpenAI.

## 🌟 Key Features

- **RAG-Powered Knowledge Base**: Accurate answers grounded in actual policy documents using FAISS vector search
- **Matrix-Based Recommendations**: Interpretable recommendation engine using matrix multiplication 🎯 NEW!
  - Maps user attributes → insurance needs → policy scores
  - Fully explainable: shows WHY each policy is recommended
  - Fast, scalable, and tunable
- **Real-Time Premium Quotes**: Live premium data from Apollo 24|7 API based on user profile 💰
- **Conversational AI**: Engaging dialogue that keeps users exploring and finding the perfect plan
- **Interactive Profile Collection**: Smart extraction from natural language + interactive forms
- **Plan Comparison**: Side-by-side comparison of top insurance plans
- **Comprehensive Coverage**: Answers questions about policies, riders, claims, eligibility, and more

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Set Up OpenAI API Key
Create `.streamlit/secrets.toml`:
```toml
[openai]
api_key = "your-api-key-here"
```

### 3. Verify Setup
```bash
python test_rag_integration.py
```

### 4. Run the Chatbot
```bash
streamlit run app.py
```

Visit `http://localhost:8501` in your browser!

## 📚 Documentation

- **[QUICKSTART.md](QUICKSTART.md)** - 5-minute quick start guide
- **[SETUP_GUIDE.md](SETUP_GUIDE.md)** - Detailed installation and configuration
- **[MATRIX_RECOMMENDATION_GUIDE.md](MATRIX_RECOMMENDATION_GUIDE.md)** - Matrix recommendation engine guide 🎯 NEW!
- **[PREMIUM_API_GUIDE.md](PREMIUM_API_GUIDE.md)** - Real-time premium API integration guide 💰
- **[AUTH_TOKEN_SETUP.md](AUTH_TOKEN_SETUP.md)** - Premium API authentication explained
- **[IMPROVEMENTS.md](IMPROVEMENTS.md)** - Technical improvements and architecture
- **[test_rag_integration.py](test_rag_integration.py)** - RAG integration tests
- **[test_premium_api.py](test_premium_api.py)** - Premium API tests
- **[test_matrix_recommendation.py](test_matrix_recommendation.py)** - Matrix engine tests 🎯 NEW!

## 🏗️ Architecture

```
User Input → Intent Classification → Dialogue Manager → RAG Retrieval → GPT Response
                                          ↓
                                   Profile Extraction
                                          ↓
                                   Plan Recommendation
```

### Core Components

- **`app.py`**: Streamlit UI and session management
- **`controller/chat_controller.py`**: Main conversation orchestration
- **`core/retrieval.py`**: RAG system with FAISS vector search
- **`core/dialogue_manager.py`**: Conversation flow logic
- **`core/intent_handler.py`**: Intent classification
- **`core/scoring.py`**: Plan recommendation engine

## 💬 Example Conversations

### Knowledge Query
```
User: What is copay?
Bot: Copay (co-payment) is the fixed percentage you pay...
     Would you like to know which plans have lower copay?
```

### Recommendation
```
User: I'm 35, male, need coverage for family
Bot: Based on your profile, I recommend the Apollo Munich 
     Optima Restore plan...
     Would you like to see premium details?
```

### Premium Quotes (NEW!) 💰
```
User: What's the premium?
Bot: 💰 Live Premium Quotes for Your Profile:
     
     1. Apollo Optima Restore - ₹8,500/year
     2. HDFC Health Suraksha - ₹9,200/year
     3. Star Comprehensive - ₹7,800/year
```

### Comparison
```
User: Compare top 3 plans
Bot: [Detailed comparison table]
     Which plan interests you most?
```

## 🔧 Configuration

### Adjust GPT Model
In `gpt_handler.py`:
```python
call_gpt(messages, model="gpt-4o-mini")  # or "gpt-4o"
```

### Adjust Retrieval Settings
In `chat_controller.py`:
```python
retrieve_answer(query, top_k=3, summarize=True, conversational=True)
```

## 📊 Data Files

Required in `data/` directory:
- `kb.index` - FAISS vector index
- `kb.json` - Knowledge base metadata
- `knowledge_base_merged.json` - Structured policy data
- `df_variations.csv` - Plan variations
- `dfv_variations.parquet` - Recommendation data

## 🧪 Testing

Run integration tests:
```bash
python test_rag_integration.py
```

Test conversation flows:
1. Knowledge queries (uses RAG)
2. Profile collection
3. Plan recommendations
4. Comparisons
5. General exploration

## 🔐 Security

- Store API keys in `.streamlit/secrets.toml` (never commit!)
- Add to `.gitignore`:
  ```
  .streamlit/secrets.toml
  __pycache__/
  *.pyc
  ```

## 📈 Recent Improvements

### ✅ Matrix-Based Recommendation Engine (NEWEST!) 🎯
- Interpretable recommendation system using matrix multiplication
- User Attributes (21) × Insurance Needs (21) → Policy Scores
- Fully explainable: shows why policies are recommended
- Fast (<50ms), scalable, and production-ready
- Replaces black-box scoring with transparent approach

### ✅ Real-Time Premium API Integration 💰
- Live premium quotes from Apollo 24|7 API
- Automatic profile-to-API conversion
- Graceful error handling with KB fallback
- Conversational premium presentation

### ✅ Fixed RAG Integration
- Knowledge queries now properly use the knowledge base
- FAISS vector search working correctly
- Accurate, fact-based responses

### ✅ Enhanced Conversational Flow
- Engaging responses with follow-up questions
- Keeps users exploring plans
- Guides through discovery process

### ✅ Better Error Handling
- Graceful fallbacks when info not found
- Helpful error messages
- Improved user experience

See [IMPROVEMENTS.md](IMPROVEMENTS.md) for detailed technical changes.

## 🚢 Deployment

### Streamlit Cloud
1. Push to GitHub
2. Connect to Streamlit Cloud
3. Add secrets in dashboard
4. Deploy!

### Docker
```bash
docker build -t insurance-chatbot .
docker run -p 8501:8501 insurance-chatbot
```

## 📝 Requirements

- Python 3.8+
- OpenAI API key
- 2GB+ RAM (for FAISS index)
- All packages in requirements.txt

## 🤝 Contributing

1. Test changes with `test_rag_integration.py`
2. Ensure RAG integration works correctly
3. Keep responses conversational
4. Maintain knowledge base accuracy

## 📞 Support

For issues:
1. Check [SETUP_GUIDE.md](SETUP_GUIDE.md)
2. Run diagnostics: `python test_rag_integration.py`
3. Review logs: `logs/conversations.log`

## 📄 Project Structure

```
insurance_chatbot/
│
├── app.py                      # Streamlit UI entry point
│
├── controller/
│   └── chat_controller.py      # Main conversation orchestration
│
├── core/
│   ├── dialogue_manager.py     # Conversation flow & state management
│   ├── intent_handler.py       # Intent classification (26 intents)
│   ├── profile_extractor.py    # Extract user profile from natural language
│   ├── retrieval.py            # RAG system (FAISS + knowledge base)
│   ├── scoring.py              # Plan recommendation scoring engine
│   ├── gpt_handler.py          # OpenAI API wrapper with cost tracking
│   └── utils.py                # Utility functions (logging, formatting)
│
├── data/
│   ├── kb.index                # FAISS vector index
│   ├── kb.json                 # Knowledge base metadata
│   ├── knowledge_base_merged.json  # Structured policy data
│   ├── df_variations.csv       # Plan variations
│   ├── dfv_variations.parquet  # Recommendation data
│   └── premium_table.csv       # Premium calculations
│
├── tests/
│   ├── test_intents.py         # Intent classification tests
│   ├── test_retrieval.py       # RAG system tests
│   ├── test_scoring.py         # Scoring engine tests
│   └── golden_conversations.json  # Test scenarios
│
├── logs/
│   └── conversations.log       # Conversation logs
│
├── requirements.txt            # Python dependencies
├── test_rag_integration.py     # Integration test script
├── SETUP_GUIDE.md             # Detailed setup instructions
├── IMPROVEMENTS.md            # Technical improvements summary
└── README.md                  # This file
```

## 🎯 How It Works

1. **User Input** → Received via Streamlit interface
2. **Intent Classification** → Identifies user's intent (recommend, compare, ask question, etc.)
3. **Profile Extraction** → Extracts demographic info from natural language
4. **Dialogue Management** → Determines next action based on intent and profile completeness
5. **RAG Retrieval** → For knowledge queries, retrieves relevant info from knowledge base using FAISS
6. **Plan Scoring** → For recommendations, scores plans based on user profile
7. **Response Generation** → GPT generates conversational response using retrieved context
8. **Follow-up** → Every response includes engaging follow-up questions

## 🔥 What Makes This Special

- **True RAG Implementation**: Not just GPT - actually retrieves from knowledge base
- **Conversational Design**: Keeps users engaged and exploring
- **Production-Ready**: Proper error handling, logging, and cost tracking
- **Modular Architecture**: Easy to extend and customize
- **Well-Tested**: Integration tests and golden conversation scenarios

---

Built with ❤️ for Apollo 24|7

**Status**: ✅ Production Ready  
**RAG**: ✅ Fully Functional  
**Conversational**: ✅ Highly Engaging
