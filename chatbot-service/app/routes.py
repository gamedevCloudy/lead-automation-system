# chatbot-service/app/routes.py
import os
from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import httpx
from typing import List, Dict, Any

from .models import ChatRequest, ChatResponse, LeadData
from .services.chatbot_service import ChatbotService

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

DATABASE_SERVICE_URL = os.getenv("DATABASE_SERVICE_URL", "http://localhost:8000")
ANALYZER_SERVICE_URL = os.getenv("ANALYZER_SERVICE_URL", "http://localhost:8002")

async def get_chatbot_service():
    return ChatbotService()

@router.get("/", response_class=HTMLResponse)
async def get_chat_page(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@router.get("/chat", response_class=HTMLResponse)
async def get_chat_interface(request: Request):
    return templates.TemplateResponse("chat.html", {"request": request})

@router.post("/api/chat", response_model=ChatResponse)
async def chat(
    chat_request: ChatRequest,
    chatbot_service: ChatbotService = Depends(get_chatbot_service)
):
    # Process the chat with Gemini
    response_text, extracted_data = await chatbot_service.process_chat(chat_request.messages)
    
    # If we have enough data, save it to the database
    if extracted_data and all(key in extracted_data for key in ["company_name", "contact_name", "email"]):
        try:
            # Create a LeadData object for validation
            lead_data = LeadData(**extracted_data)
            
            # Save to database service
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{DATABASE_SERVICE_URL}/leads/",
                    json=lead_data.dict(exclude_none=True)
                )
                
                if response.status_code == 200:
                    # Trigger analyzer service to process the lead
                    lead_id = response.json()["id"]
                    await client.post(
                        f"{ANALYZER_SERVICE_URL}/analyze/{lead_id}",
                        json={}
                    )
                else:
                    print(f"Failed to save lead: {response.text}")
        except Exception as e:
            print(f"Error processing lead data: {str(e)}")
    
    return ChatResponse(
        response=response_text,
        extracted_data=extracted_data
    )