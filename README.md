# AI Travel Planner

A real-time travel planning application that uses AI to create personalized trip itineraries. The application leverages LangChain and GPT to generate dynamic travel plans with streaming updates.

## Features

- 🌍 Personalized trip planning based on destination
- 💰 Budget assessment and validation
- 🎯 Interest-based attraction recommendations
- ⚡ Real-time streaming responses
- 📅 Day-by-day itinerary generation

## API Endpoints

### GET `/stream-plan`

Creates a travel plan with real-time updates.

Parameters:

- `destination`: String - Where you want to go
- `dates`: String - Duration of the trip
- `currency`: String - Currency for budget calculation
- `budget`: Integer - Available budget
- `interests`: Array[String] - Optional list of interests/themes

Response Stream Events:

- `thought`: Agent's thinking process and tool usage
- `narration`: Streaming narrative from the AI
- `final`: Structured itinerary
- `status`: Process completion status
- `done`: Stream end marker

## Technical Stack

- FastAPI for the backend API
- LangChain for AI agent orchestration
- GPT-3.5-turbo for natural language processing
- Server-Sent Events (SSE) for real-time updates

## Response Format

The itinerary is returned in a structured format:

```json
{
  "title": string,
  "days": [
    {
      "day": number,
      "activities": string[]
    }
  ]
}
```

## Setup

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Set up your environment variables:

```bash
OPENAI_API_KEY=your_api_key_here
```

3. Run the server:

```bash
uvicorn main:app --reload
```
