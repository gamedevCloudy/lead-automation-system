# analyzer-service/app/routes.py
import os
import httpx
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any

from .models import AnalysisRequest, AnalysisResult
from .services.analyzer_service import AnalyzerService
from .services.web_scraper import WebScraper

router = APIRouter()

DATABASE_SERVICE_URL = os.getenv("DATABASE_SERVICE_URL", "http://localhost:8000")
TEAM_MATCHER_URL = os.getenv("TEAM_MATCHER_URL", "http://localhost:8003")

async def get_analyzer_service():
    return AnalyzerService()

async def get_web_scraper():
    return WebScraper()

@router.post("/analyze/{lead_id}", response_model=AnalysisResult)
async def analyze_lead(
    lead_id: int,
    request: AnalysisRequest = AnalysisRequest(),
    analyzer_service: AnalyzerService = Depends(get_analyzer_service),
    web_scraper: WebScraper = Depends(get_web_scraper)
):
    # Get lead data from database service
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{DATABASE_SERVICE_URL}/leads/{lead_id}")
        
        if response.status_code != 200:
            raise HTTPException(status_code=404, detail="Lead not found")
        
        lead_data = response.json()
    
    # Perform web scraping to get company information
    company_info = None
    if lead_data.get("company_name"):
        try:
            company_info = await web_scraper.scrape_company_info(lead_data["company_name"])
        except Exception as e:
            print(f"Error during web scraping: {str(e)}")
            company_info = {"error": str(e)}
    
    # Analyze the lead
    analysis_result = await analyzer_service.analyze_lead(lead_data, company_info)
    
    # Save the analysis to the database
    async with httpx.AsyncClient() as client:
        analysis_data = {
            "lead_id": lead_id,
            "company_details": analysis_result.company_details,
            "llm_analysis": analysis_result.llm_analysis,
            "final_decision": analysis_result.final_decision
        }
        
        response = await client.post(f"{DATABASE_SERVICE_URL}/analyses/", json=analysis_data)
        
        if response.status_code != 200:
            print(f"Error saving analysis: {response.text}")
            raise HTTPException(status_code=500, detail="Failed to save analysis")
    
    # If the decision is "Yes" or "Maybe", trigger team matching
    if analysis_result.final_decision in ["Yes", "Maybe"]:
        try:
            async with httpx.AsyncClient() as client:
                await client.post(
                    f"{TEAM_MATCHER_URL}/match/{lead_id}",
                    json={"analysis_context": analysis_result.dict()}
                )
        except Exception as e:
            print(f"Error triggering team matching: {str(e)}")
    
    return analysis_result