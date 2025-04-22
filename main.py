
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict

import openai
import os

openai.api_key = os.getenv("OPENAI_API_KEY")

app = FastAPI()

# Allow frontend requests from any origin for now
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class PlanRequest(BaseModel):
    destination: str
    dates: str
    currency: str
    budget: int
    interests: List[str]

class PlanResponse(BaseModel):
    itinerary: List[Dict[str, str]]
    totalCost: str
    agentThoughts: List[str]

@app.post("/plan", response_model=PlanResponse)
async def plan_trip(req: PlanRequest):
    trace = []

    def log(thought):
        trace.append(thought)

    log("Received trip planning request.")
    log(f"Destination: {req.destination}, Dates: {req.dates}, Budget: {req.budget} {req.currency}, Interests: {', '.join(req.interests)}")

    prompt = f"""
You are an intelligent travel planning agent.

Plan a {req.dates}-length trip to {req.destination} with a budget of {req.budget} {req.currency}.
Interests: {', '.join(req.interests) or 'General'}.

Return valid JSON only in this format:
{{
  "itinerary": [
    {{ "day": "Day 1", "plan": "..." }},
    {{ "day": "Day 2", "plan": "..." }}
  ],
  "totalCost": "formatted like '£450 GBP'",
  "agentThoughts": ["short points about how you planned the trip"]
}}

ONLY return raw JSON. Do NOT include ```json or any code blocks.
"""

    response = openai.ChatCompletion.create(
        model="gpt-4",
        temperature=0.7,
        messages=[
            {"role": "system", "content": "You are a helpful travel planner."},
            {"role": "user", "content": prompt}
        ]
    )

    raw = response.choices[0].message["content"]
    
    import json
    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        return {"error": "OpenAI returned invalid JSON", "raw": raw}

    result["agentThoughts"].insert(0, "Started with user preferences.")
    result["agentThoughts"].extend(trace)

    return result
