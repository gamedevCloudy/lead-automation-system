# chatbot-service/app/models.py
from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional, Dict, Any

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[Message]

class ChatResponse(BaseModel):
    response: str
    extracted_data: Optional[Dict[str, Any]] = None

class LeadData(BaseModel):
    company_name: str = Field(..., description="Name of the company")
    contact_name: str = Field(..., description="Name of the contact person")
    position: Optional[str] = Field(None, description="Position of the contact person in the company")
    email: EmailStr = Field(..., description="Email address of the contact")
    phone: Optional[str] = Field(None, description="Phone number of the contact")
    revenue: Optional[float] = Field(None, description="Approximate annual revenue of the company")
    service_type: Optional[str] = Field(None, description="Type of service the lead is looking for")
    message: Optional[str] = Field(None, description="Additional information or requirements")