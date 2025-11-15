# ThinkingAgent Web UI

A professional, modern web interface for the ThinkingAgent AI decision-making platform.

## 🎨 Features

### Design
- **Modern Glassmorphism UI** with backdrop blur effects
- **Dark Theme** with purple/gold gradient background (#2E1A47 to #1a1a4e)
- **Responsive Design** that works on desktop, tablet, and mobile
- **Smooth Animations** and transitions throughout
- **Professional Business-Ready** appearance

### Functionality
- **Real-time Chat Interface** for conversing with the AI
- **Strategic Options Display** with pros/cons analysis
- **Session Management** to organize conversations
- **Interactive Approval Workflow** for decision-making
- **Loading States** and error handling
- **Notifications** for user feedback

## 🚀 Getting Started

### Prerequisites

1. **Backend Running**: Ensure the ThinkingAgent backend is running on `localhost:8000`
   ```bash
   cd /path/to/autoagent
   python run.py
   ```

2. **Database Setup**: PostgreSQL and Redis must be running
   ```bash
   # Check if PostgreSQL is running
   psql -U kumaresh -d thinkingagent -c "SELECT 1"

   # Check if Redis is running
   redis-cli ping
   ```

### Access the UI

Once the backend is running, simply open your browser and navigate to:

```
http://localhost:8000/
```

The UI will be served automatically!

## 📖 How to Use

### 1. Start a New Session

Click the **"✨ New Session"** button in the header to create a new conversation session.

### 2. Send a Message

Type your goal or challenge in the message input at the bottom of the chat panel and click **"Send"**.

**Example:**
```
I want to create a cooking YouTube channel
```

### 3. Review Strategic Options

The AI will analyze your request and generate 2-3 strategic options displayed in the right panel. Each option includes:
- **Name**: Clear description of the approach
- **Pros**: Advantages of this option
- **Cons**: Challenges or disadvantages
- **Recommended Badge**: AI's recommended choice (if applicable)

### 4. Select an Option

Click on one of the option cards to select it. The selected card will be highlighted with a gold border.

### 5. Add Modifications (Optional)

Use the text area in the "Modifications or Notes" section to add:
- Specific requirements
- Customizations
- Additional context
- Constraints

### 6. Submit Your Decision

Click **"✅ Submit Decision"** to confirm your choice. The AI will record your decision and proceed with the workflow.

## 🎯 Example Workflow

### Scenario: Starting a YouTube Channel

**Step 1**: User sends message
```
I want to create a cooking YouTube channel
```

**Step 2**: AI generates 3 strategic options:
- **Option 1**: Quick 15-Minute Recipes
  - Pros: High engagement, busy audience appeal, easy production
  - Cons: Limited depth, competitive niche

- **Option 2**: Traditional Cultural Cooking
  - Pros: Unique content, passionate audience, educational value
  - Cons: Smaller audience, requires expertise

- **Option 3**: Healthy Meal Prep & Planning
  - Pros: Growing trend, subscription potential, helpful content
  - Cons: Requires nutritional knowledge, time-intensive prep

**Step 3**: User selects Option 1 and adds modification:
```
Focus on Asian cuisine with vegetarian options
```

**Step 4**: AI confirms decision and continues the workflow

## 🎨 UI Components

### Chat Panel (Left Side)
- **Message History**: Shows all user and AI messages
- **Message Input**: Text field for typing messages
- **Send Button**: Submits messages to the AI

### Approval Panel (Right Side)
- **Strategic Options**: Cards displaying AI-generated options
- **Pros/Cons Lists**: Detailed analysis for each option
- **Decision Area**: Text area for modifications and submit button

### Header
- **Logo and Branding**: ThinkingAgent identity
- **New Session Button**: Creates fresh conversation sessions

## 🔧 Technical Details

### API Integration

The UI connects to the following backend endpoints:

- `POST /api/v1/sessions` - Create new session
- `POST /api/v1/sessions/{id}/messages` - Send message
- `GET /api/v1/sessions/{id}/messages` - Fetch messages
- `GET /api/v1/approvals/{id}` - Get approval details
- `POST /api/v1/approvals/{id}/decide` - Submit decision

### Error Handling

The UI includes comprehensive error handling:
- **Network Errors**: Displays error notifications
- **API Failures**: Shows user-friendly error messages
- **Loading States**: Indicates when operations are in progress
- **Empty States**: Guides users when no data is available

### Notifications

Three types of notifications:
- **Success** (Green): Operation completed successfully
- **Error** (Red): Something went wrong
- **Info** (Blue): Informational messages

## 🎨 Customization

### Changing Colors

The UI uses CSS variables that can be easily customized:

```css
/* Primary gradient */
background: linear-gradient(135deg, #2E1A47 0%, #1a1a4e 100%);

/* Gold accent */
color: #FFD700;

/* Edit these in the <style> section of index.html */
```

### Modifying Layout

The layout uses CSS Grid for responsiveness:
```css
.main-content {
    display: grid;
    grid-template-columns: 1fr 1fr; /* Two equal columns */
    gap: 20px;
}
```

## 🐛 Troubleshooting

### UI Not Loading
- Ensure backend is running: `python run.py`
- Check browser console for errors (F12)
- Verify static files are in the correct directory

### API Errors
- Check backend logs for detailed error messages
- Verify `LOG_LEVEL=DEBUG` in `.env` for detailed logging
- Ensure database and Redis are running

### CORS Issues
- Backend CORS is configured for `localhost:8000`
- Check `CORS_ORIGINS` in `.env` if accessing from different origin

### Messages Not Appearing
- Check browser console for JavaScript errors
- Verify session was created successfully
- Ensure API endpoints are accessible

## 🔒 Security Notes

- The UI runs on the same origin as the API (no CORS issues)
- API keys are never exposed in the frontend
- All communication uses HTTP (use HTTPS in production)
- Sessions are managed server-side

## 📱 Responsive Design

The UI automatically adapts to different screen sizes:
- **Desktop**: Side-by-side panels (1400px max width)
- **Tablet**: Stacked panels below 968px
- **Mobile**: Optimized for small screens with touch-friendly buttons

## 🚀 Production Deployment

For production deployment:

1. **Use HTTPS**: Configure SSL/TLS certificates
2. **Update API URL**: Change `API_BASE_URL` if backend is on different domain
3. **Optimize Assets**: Minify CSS and JavaScript
4. **Enable Caching**: Add cache headers for static assets
5. **CDN**: Consider using a CDN for static files

## 📚 Additional Resources

- **Backend API Docs**: http://localhost:8000/api/v1/docs
- **Backend Source**: See `app/` directory
- **OpenRouter Integration**: See `OPENROUTER_INTEGRATION.md`

## 💡 Tips

- Use descriptive messages for better AI analysis
- Review all pros/cons before selecting an option
- Add modifications to customize options to your needs
- Create new sessions for different topics/projects
- The recommended option is AI-suggested but not required

---

**Enjoy using ThinkingAgent!** 🧠✨
