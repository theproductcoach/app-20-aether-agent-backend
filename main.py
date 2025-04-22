from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict
import os
import json

from openai import OpenAI
openai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

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

@app.post("/plan")
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

Return valid JSON ONLY in this format:

{{
  "itinerary": [
    {{ "day": "Day 1", "plan": "..." }},
    {{ "day": "Day 2", "plan": "..." }}
  ],
  "totalCost": "formatted like '£450 GBP'",
  "agentThoughts": ["short points about how you planned the trip"]
}}

Do not return anything else. No markdown. No text before or after.
"""

    try:
        response = openai.chat.completions.create(
            model="gpt-4",
            temperature=0.7,
            messages=[
                {"role": "system", "content": "You are a helpful travel planner."},
                {"role": "user", "content": prompt}
            ]
        )

        raw = response.choices[0].message.content
        result = json.loads(raw)

        result["agentThoughts"].insert(0, "Started with user preferences.")
        result["agentThoughts"].extend(trace)

        return result

    except json.JSONDecodeError as json_err:
        return {
            "error": "OpenAI returned invalid JSON",
            "raw": raw if 'raw' in locals() else "No response to parse",
            "exception": str(json_err)
        }

    except Exception as e:
        return {
            "error": "Unhandled exception",
            "exception": str(e)
        }
from fastapi import Request
from stream_plan import stream_plan, StreamPlanRequest

@app.post("/stream-plan")
async def stream_plan_route(request: Request):
    body = await request.json()
    req_data = StreamPlanRequest(**body)
    return stream_plan(req_data)