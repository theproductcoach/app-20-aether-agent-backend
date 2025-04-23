from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from langchain.agents import initialize_agent, AgentType
from langchain.tools import tool
from langchain_openai import ChatOpenAI
from langchain_core.callbacks.base import AsyncCallbackHandler
from typing import List, Optional, TypedDict
import asyncio
import json
import re

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@tool
def search_attractions(city: str, theme: str) -> str:
    """Finds themed attractions in a city"""
    prompt = f"List 3-4 real or plausible {theme}-related attractions in {city}. Include a mix of museums, landmarks, and cultural spots. Format as a simple comma-separated list."
    response = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.7).invoke(prompt)
    return response.content

@tool
def check_budget(amount: int, currency: str) -> str:
    """Checks if the budget is sufficient for a 3-day trip"""
    prompt = f"As a travel expert, evaluate if {amount} {currency} is sufficient for a 3-day trip, considering average hotel, food, and activity costs. Provide a brief 1-2 sentence assessment."
    response = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.3).invoke(prompt)
    return response.content

tools = [search_attractions, check_budget]
llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0, streaming=True)
agent_executor = initialize_agent(tools, llm, agent=AgentType.OPENAI_FUNCTIONS, verbose=True)

class DayActivity(TypedDict):
    day: int
    activities: List[str]

class Itinerary(TypedDict):
    title: str
    days: List[DayActivity]

def parse_itinerary(text: str, destination: str) -> Itinerary:
    """Parse the agent's response into a structured itinerary"""
    day_sections = re.split(r'Day \d+:|DAY \d+:', text)
    if len(day_sections) <= 1:
        return {
            "title": f"Trip to {destination}",
            "days": [{
                "day": 1,
                "activities": [text.strip()]
            }]
        }
    
    days = []
    for i, section in enumerate(day_sections[1:], 1):
        activities = [
            activity.strip()
            for activity in section.split('\n')
            if activity.strip() and not activity.lower().startswith(('day', 'morning', 'afternoon', 'evening'))
        ]
        days.append({
            "day": i,
            "activities": activities
        })
    
    return {
        "title": f"Trip to {destination}",
        "days": days
    }

@app.get("/stream-plan")
async def stream_plan(
    destination: str = Query(...),
    dates: str = Query(...),
    currency: str = Query(...),
    budget: int = Query(...),
    interests: List[str] = Query(default=[])
):
    theme = ", ".join(interests) if interests else "general"
    prompt = (
        f"Plan a {dates}-long trip to {destination} focused on {theme}. "
        f"Use tools to search attractions and validate the budget of {budget} {currency}. "
        "Structure your response by days, with a clear 'Day X:' format for each day."
    )

    async def event_stream():
        try:
            async for event in agent_executor.astream_events({"input": prompt}, version="v1"):
                kind = event.get("event")

                if kind == "on_chain_start":
                    agent_input = event.get("data", {}).get("input", "")
                    message = f"🤔 Agent thinking: {agent_input}"
                    yield f"data: {json.dumps({'type': 'thought', 'content': message})}\n\n"

                elif kind == "on_tool_start":
                    tool_name = event.get("name", "unknown_tool")
                    tool_input = event.get("data", {}).get("input", {})
                    message = f"🔧 Starting tool `{tool_name}` with inputs: {tool_input}"
                    yield f"data: {json.dumps({'type': 'thought', 'content': message})}\n\n"

                elif kind == "on_tool_end":
                    tool_name = event.get("name", "unknown_tool")
                    tool_output = event.get("data", {}).get("output", "")
                    message = f"✅ Done with tool `{tool_name}`. Output: {tool_output}"
                    yield f"data: {json.dumps({'type': 'thought', 'content': message})}\n\n"

                elif kind == "on_chat_model_stream":
                    chunk = event.get("data", {}).get("chunk")
                    if chunk and hasattr(chunk, "content"):
                        content = chunk.content
                        yield f"data: {json.dumps({'type': 'thought', 'content': content})}\n\n"

                elif kind == "on_chain_end":
                    output = event.get("data", {}).get("output", {}).get("output")
                    if output:
                        match = re.search(r"trip to ([^.]+)", prompt)
                        dest = match.group(1) if match else "your destination"
                        itinerary = parse_itinerary(output, dest)
                        yield f"data: {json.dumps({'type': 'final', 'payload': itinerary})}\n\n"
                        yield f"data: {json.dumps({'type': 'status', 'content': '✅ Trip planning complete!'})}\n\n"
                        yield f"data: {json.dumps({'type': 'done'})}\n\n"
        finally:
            # Ensure connection is flushed and closed
            yield "event: done\ndata: \n\n"
            print("🛑 Stream closed by finally block")

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
    )