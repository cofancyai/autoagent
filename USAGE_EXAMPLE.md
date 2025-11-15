# ThinkingAgent - Complete Usage Example

This guide demonstrates the full AI thinking workflow with automatic approval generation.

## 🤖 How It Works

When a user sends a message, the ThinkingAgent:
1. **Analyzes** the request using Claude AI
2. **Generates** 2-3 strategic options with pros/cons
3. **Creates** an approval checkpoint automatically
4. **Returns** both the message confirmation and approval options

## 📝 Complete Workflow Example

### 1. Create a Session

```bash
curl -X POST http://localhost:8000/api/v1/sessions \
  -H "Content-Type: application/json" \
  -d '{
    "title": "YouTube Channel Planning"
  }'
```

**Response:**
```json
{
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "title": "YouTube Channel Planning",
    "status": "active",
    "created_at": "2025-11-15T10:00:00Z"
  }
}
```

### 2. Send a User Message (AI Automatically Triggers)

```bash
curl -X POST http://localhost:8000/api/v1/sessions/550e8400-e29b-41d4-a716-446655440000/messages \
  -H "Content-Type: application/json" \
  -d '{
    "role": "user",
    "content": "I want to create a cooking YouTube channel"
  }'
```

**Response:**
```json
{
  "data": {
    "message": {
      "id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
      "session_id": "550e8400-e29b-41d4-a716-446655440000",
      "role": "user",
      "content": "I want to create a cooking YouTube channel",
      "created_at": "2025-11-15T10:01:00Z"
    },
    "approval_checkpoint": {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "checkpoint_type": "strategic_decision",
      "decision_needed": "Choose your approach: I want to create a cooking YouTube channel",
      "options_count": 3,
      "recommended_option": 0
    }
  }
}
```

### 3. Get the Approval Details

```bash
curl http://localhost:8000/api/v1/approvals/123e4567-e89b-12d3-a456-426614174000
```

**Response:**
```json
{
  "data": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "checkpoint_type": "strategic_decision",
    "decision_needed": "Choose your approach: I want to create a cooking YouTube channel",
    "status": "pending",
    "recommended_option": 0,
    "options": [
      {
        "name": "Quick & Easy 15-Minute Recipes",
        "description": "Focus on fast, accessible recipes for busy people",
        "pros": [
          "High demand from working professionals",
          "Easy to produce consistently",
          "Great for building initial audience",
          "Lower production complexity"
        ],
        "cons": [
          "Highly competitive niche",
          "May limit culinary creativity",
          "Requires constant content output"
        ]
      },
      {
        "name": "Traditional Cultural Cooking",
        "description": "Showcase authentic recipes from specific cultural traditions",
        "pros": [
          "Unique positioning in market",
          "Passionate niche audience",
          "Educational and cultural value",
          "Less direct competition"
        ],
        "cons": [
          "Smaller target audience",
          "May need specialized ingredients",
          "Requires deep cultural knowledge"
        ]
      },
      {
        "name": "Healthy Meal Prep & Planning",
        "description": "Focus on nutritious batch cooking and weekly meal planning",
        "pros": [
          "Growing health-conscious audience",
          "Strong monetization potential",
          "Helps viewers save time and money",
          "Sustainable content model"
        ],
        "cons": [
          "Requires nutrition knowledge",
          "Equipment investment for batch cooking",
          "Longer video production time"
        ]
      }
    ],
    "created_at": "2025-11-15T10:01:00Z"
  }
}
```

### 4. Submit Your Decision

```bash
curl -X POST http://localhost:8000/api/v1/approvals/123e4567-e89b-12d3-a456-426614174000/decide \
  -H "Content-Type: application/json" \
  -d '{
    "selected_option": 0,
    "modifications": "Focus on Asian-inspired quick recipes",
    "reasoning": "Combines quick recipes with unique cultural angle"
  }'
```

**Response:**
```json
{
  "data": {
    "id": "dec-9876-5432-1098",
    "approval_checkpoint_id": "123e4567-e89b-12d3-a456-426614174000",
    "selected_option": 0,
    "modifications": "Focus on Asian-inspired quick recipes",
    "reasoning": "Combines quick recipes with unique cultural angle",
    "created_at": "2025-11-15T10:05:00Z"
  }
}
```

### 5. View Conversation History

```bash
curl http://localhost:8000/api/v1/sessions/550e8400-e29b-41d4-a716-446655440000/messages
```

**Response:**
```json
{
  "data": {
    "messages": [
      {
        "id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
        "role": "user",
        "content": "I want to create a cooking YouTube channel",
        "created_at": "2025-11-15T10:01:00Z"
      },
      {
        "id": "8d0f7780-8536-51ef-b158-f18gd2g01bf8",
        "role": "assistant",
        "content": "I've analyzed your request to create a cooking YouTube channel. This is an exciting venture with multiple strategic approaches you could take.\n\nI've generated 3 strategic options for you to consider.",
        "extra_data": {
          "approval_id": "123e4567-e89b-12d3-a456-426614174000",
          "type": "thinking_response"
        },
        "created_at": "2025-11-15T10:01:05Z"
      }
    ],
    "has_more": false
  }
}
```

## 🎯 Key Features Demonstrated

1. **Automatic AI Thinking**: User message triggers AI analysis automatically
2. **Strategic Options**: AI generates multiple approaches with detailed pros/cons
3. **Approval Workflow**: User reviews and approves their preferred option
4. **Complete Audit Trail**: All messages, thinking processes, and decisions logged
5. **Conversational Context**: AI maintains conversation history for better analysis

## 🔧 Configuration

The AI thinking is configured in `app/services/prompts.py`:
- System prompt defines AI's role
- Option generation template structures the analysis
- Conversation history provides context

## 📊 Behind the Scenes

When you send a user message, the system:

1. **Stores Message** → Database
2. **Triggers ThinkingAgentService** → AI Processing
3. **Calls Claude API** → Strategic Analysis
4. **Creates ThinkingProcess** → Audit Trail
5. **Generates ApprovalCheckpoint** → Options Storage
6. **Creates Assistant Message** → Response
7. **Returns Combined Response** → User

All of this happens automatically in a single API call!

## 🚀 Next Steps

After approval, you can:
- Continue the conversation with more refinements
- Create goals based on approved decisions
- Track execution of the chosen strategy
- Review the complete decision history

## 💡 Tips

- **Be Specific**: More detailed requests generate better options
- **Provide Context**: Mention your background, goals, constraints
- **Iterate**: You can refine options by sending follow-up messages
- **Review History**: Check conversation history to see AI's reasoning

## 🎨 Customization

You can customize the AI behavior by:
- Modifying prompts in `app/services/prompts.py`
- Adjusting model selection in `ThinkingAgentService`
- Adding domain-specific knowledge to system prompts
- Implementing custom approval checkpoint types
