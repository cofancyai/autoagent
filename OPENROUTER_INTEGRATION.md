# OpenRouter Integration Guide

The ThinkingAgent backend now supports **both Anthropic Claude and OpenRouter** APIs seamlessly. The client automatically detects which provider to use based on your API key format.

## 🎯 Key Features

- **Automatic Provider Detection**: The client detects the provider from your API key format
- **Unified Interface**: Same code works with both providers - no changes needed
- **Cost Tracking**: Separate cost estimation for both providers
- **Same Response Format**: Consistent response structure regardless of provider
- **Full Retry Logic**: Same error handling and retry mechanisms for both

## 🔑 Configuration

### Using OpenRouter (Recommended for Free Models)

1. **Get an OpenRouter API Key**:
   - Sign up at https://openrouter.ai/
   - Get your API key (format: `sk-or-v1-...`)

2. **Configure Environment Variables**:
   ```bash
   # In your .env file
   ANTHROPIC_API_KEY=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
   OPENROUTER_MODEL=qwen/qwen3-coder:free
   ```

3. **That's it!** The client will automatically use OpenRouter.

### Using Anthropic Claude

1. **Get an Anthropic API Key**:
   - Sign up at https://console.anthropic.com/
   - Get your API key (format: `sk-ant-...`)

2. **Configure Environment Variables**:
   ```bash
   # In your .env file
   ANTHROPIC_API_KEY=sk-ant-your-anthropic-key-here
   # OPENROUTER_MODEL is ignored when using Anthropic
   ```

3. **Done!** The client will use Anthropic's API.

## 🔍 How It Works

### Provider Detection

The client detects the provider based on API key prefix:

```python
if api_key.startswith("sk-or-v1-"):
    # Use OpenRouter API
    provider = Provider.OPENROUTER
else:
    # Use Anthropic API
    provider = Provider.ANTHROPIC
```

### API Format Differences

**OpenRouter** uses OpenAI-compatible format:
- Endpoint: `https://openrouter.ai/api/v1/chat/completions`
- Format: OpenAI Chat Completions API
- System message: Included in messages array

**Anthropic** uses native Claude format:
- Endpoint: `https://api.anthropic.com/v1/messages`
- Format: Anthropic Messages API
- System context: Separate parameter with caching support

### Response Normalization

Both providers return the same response format:

```json
{
  "content": "AI response text...",
  "model": "model-id",
  "usage": {
    "prompt_tokens": 100,
    "completion_tokens": 200,
    "total_tokens": 300
  },
  "latency_ms": 1234,
  "stop_reason": "stop"
}
```

## 💰 Cost Tracking

### OpenRouter (Free Models)
- Free models like `qwen/qwen3-coder:free` have **zero cost**
- `estimate_cost()` returns `0.0`

### Anthropic Claude
- Opus: $15/$75 per million tokens (prompt/completion)
- Sonnet: $3/$15 per million tokens
- Haiku: $0.25/$1.25 per million tokens

## 🔧 Technical Details

### Model Selection

When using **OpenRouter**, the client uses the model specified in `OPENROUTER_MODEL`:
- Default: `qwen/qwen3-coder:free`
- You can use any OpenRouter model (see https://openrouter.ai/models)

When using **Anthropic**, the client uses model type routing:
- `ModelType.OPUS` → `claude-opus-4-20250514`
- `ModelType.SONNET` → `claude-sonnet-4-5-20250929`
- `ModelType.HAIKU` → `claude-haiku-4-20250514`

### Prompt Caching

- **Anthropic**: Full support for prompt caching (50-90% cost savings)
- **OpenRouter**: Not supported (use_cache parameter is ignored)

### Streaming

- **Anthropic**: Fully supported
- **OpenRouter**: Coming soon (not yet implemented)

## 📝 Code Examples

### Basic Usage (Works with Both Providers)

```python
from app.integrations.anthropic_client import anthropic_client, ModelType

# The same code works with both Anthropic and OpenRouter
response = await anthropic_client.generate(
    model=ModelType.SONNET,
    messages=[{"role": "user", "content": "Hello, how are you?"}],
    system_context="You are a helpful assistant.",
)

print(response["content"])  # AI response
print(response["usage"])    # Token usage
print(response["latency_ms"])  # Request latency
```

### Task-Based Model Selection

```python
# Automatically selects best model for the task
model = await anthropic_client.select_model_for_task("code_generation")

response = await anthropic_client.generate(
    model=model,
    messages=[{"role": "user", "content": "Write a Python function to sort a list"}],
)
```

### Cost Estimation

```python
# Works with both providers (returns 0.0 for OpenRouter free models)
cost = await anthropic_client.estimate_cost(
    model=ModelType.SONNET,
    prompt_tokens=1000,
    completion_tokens=500,
)
print(f"Estimated cost: ${cost:.4f}")
```

## 🚀 Switching Between Providers

To switch providers, simply change your API key:

```bash
# Switch to OpenRouter
ANTHROPIC_API_KEY=sk-or-v1-your-openrouter-key

# Switch to Anthropic
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key
```

**No code changes needed!** The client handles everything automatically.

## ⚠️ Important Notes

1. **API Key Format**: The provider is detected from the key prefix
   - OpenRouter: `sk-or-v1-...`
   - Anthropic: Any other format (typically `sk-ant-...`)

2. **Model Availability**:
   - OpenRouter: Only uses `OPENROUTER_MODEL` setting
   - Anthropic: Uses ModelType to select from Opus/Sonnet/Haiku

3. **Prompt Caching**: Only available with Anthropic keys

4. **Rate Limits**: Different for each provider (check provider docs)

## 🐛 Troubleshooting

### Error: "Authentication failed"
- Check your API key is correct
- Verify the key format matches the provider

### Error: "Model not found"
- For OpenRouter: Check `OPENROUTER_MODEL` is a valid model ID
- For Anthropic: Model IDs are hardcoded and should work

### Cost showing as $0 when using Anthropic
- Verify your API key starts with `sk-ant-` or similar (not `sk-or-v1-`)

## 📚 Additional Resources

- OpenRouter Docs: https://openrouter.ai/docs
- OpenRouter Models: https://openrouter.ai/models
- Anthropic Docs: https://docs.anthropic.com/
- Anthropic Pricing: https://www.anthropic.com/pricing
