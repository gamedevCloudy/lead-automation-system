# analyzer-service/app/models.py
from pydantic import BaseModel
from typing import Dict, Any, Optional, List

class AnalysisRequest(BaseModel):
    """Optional additional context that can be provided to the analyzer"""
    additional_context: Optional[Dict[str, Any]] = None

class AnalysisResult(BaseModel):
    """Result of the lead analysis"""
    lead_id: int
    company_details: Dict[str, Any]
    llm_analysis: str
    final_decision: str  # "Yes", "No", "Maybe"

class WebScrapingResult(BaseModel):
    """Results from web scraping"""
    company_name: str
    website_url: Optional[str] = None
    found_data: Dict[str, Any]
    raw_text: Optional[str] = None