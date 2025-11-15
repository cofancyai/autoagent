"""Prompt templates for AI thinking"""

SYSTEM_PROMPT = """You are a strategic thinking assistant that helps users make better decisions.

When a user shares a goal or problem, your role is to:
1. Analyze their request thoughtfully
2. Generate 2-3 strategic options/approaches they could take
3. For each option, provide:
   - A clear name/title
   - Key advantages (pros)
   - Important considerations/drawbacks (cons)
   - Any additional context that helps decision-making

Be concise but insightful. Focus on actionable, practical options."""


OPTION_GENERATION_TEMPLATE = """The user wants to: {user_request}

Please analyze this request and generate 2-3 strategic options for how they could approach this.

For each option, provide:
- name: A clear, descriptive title (max 60 characters)
- description: A brief 1-2 sentence description
- pros: List of 2-4 key advantages
- cons: List of 2-4 important considerations or challenges

Return your response in JSON format:
{{
  "analysis": "Brief analysis of the user's request (2-3 sentences)",
  "options": [
    {{
      "name": "Option title",
      "description": "Brief description",
      "pros": ["Advantage 1", "Advantage 2", "Advantage 3"],
      "cons": ["Challenge 1", "Challenge 2"]
    }}
  ],
  "recommended_option": 0
}}

Focus on being strategic, practical, and balanced in your analysis."""


def build_thinking_prompt(user_message: str, conversation_history: list = None) -> str:
    """Build a prompt for generating strategic options"""

    context = ""
    if conversation_history:
        context = "\n\nConversation history:\n"
        for msg in conversation_history[-5:]:  # Last 5 messages for context
            context += f"{msg.role}: {msg.content}\n"

    return OPTION_GENERATION_TEMPLATE.format(user_request=user_message) + context
