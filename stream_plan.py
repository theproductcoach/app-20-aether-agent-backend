from fastapi import Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List
import time

class StreamPlanRequest(BaseModel):
    destination: str
    dates: str
    currency: str
    budget: int
    interests: List[str]

def stream_plan(req_data: StreamPlanRequest):
    def event_stream():
        yield f"data: ✈️ Planning a trip to {req_data.destination}...\n\n"
        time.sleep(1)
        yield f"data: 🔍 Analyzing interests: {', '.join(req_data.interests) or 'General'}\n\n"
        time.sleep(1)
        yield "data: 📅 Building itinerary across dates...\n\n"
        time.sleep(1)
        yield f"data: 💰 Checking budget: {req_data.budget} {req_data.currency}\n\n"
        time.sleep(1)
        yield "data: 🧠 Finalising and optimising..."
        time.sleep(1)
        yield "data: ✅ Done planning!"
        yield "data: [DONE]"
    return StreamingResponse(event_stream(), media_type="text/event-stream")
