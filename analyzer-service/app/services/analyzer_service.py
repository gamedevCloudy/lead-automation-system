# analyzer-service/app/services/analyzer_service.py
import os
import json
import google.generativeai as genai
from typing import Dict, Any, Optional

from ..models import AnalysisResult

class AnalyzerService:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable is not set")
        
        genai.configure(api_key=api_key)
        
        # Create a model
        generation_config = {
            "temperature": 0.2,  # Low temperature for more deterministic results
            "top_p": 0.8,
            "top_k": 40,
            "max_output_tokens": 2048,
        }
        
        self.model = genai.GenerativeModel(
            model_name="gemini-1.5-pro",
            generation_config=generation_config
        )
        
        self.analysis_prompt = """
        You are an expert business development consultant analyzing potential client leads.
        You need to determine if a lead is a good fit for our digital marketing and web development agency.
        
        Our ideal clients:
        - Have annual revenue of at least $500,000
        - Have some existing online presence
        - Have a clear understanding of what they need
        - Have a reasonable budget for marketing/development work
        
        Based on the lead information and company details provided, analyze the prospect using these criteria:
        1. Company size and revenue
        2. Online presence and current marketing
        3. Clarity of their requirements
        4. Potential budget based on company size
        5. Overall fit with our agency
        
        Lead information: {lead_data}
        
        Web research on company: {company_info}
        
        Provide a thorough analysis and conclude with one of three decisions:
        - "Yes" (High-value lead, pursue immediately)
        - "Maybe" (Potential value, needs more information)
        - "No" (Not a good fit, do not pursue)
        
        Format your response as a JSON object with the following structure:
        {{
          "analysis": "Your detailed analysis here...",
          "decision": "Yes/Maybe/No",
          "company_details": {{
            "estimated_revenue": "Your estimate or the provided revenue",
            "online_presence": "Strong/Medium/Weak",
            "requirement_clarity": "Clear/Somewhat Clear/Unclear",
            "estimated_budget": "Your estimate",
            "key_findings": ["finding 1", "finding 2", ...]
          }}
        }}
        """

    async def analyze_lead(
        self, 
        lead_data: Dict[str, Any], 
        company_info: Optional[Dict[str, Any]] = None
    ) -> AnalysisResult:
        # Prepare the prompt with the lead and company data
        prompt = self.analysis_prompt.format(
            lead_data=json.dumps(lead_data),
            company_info=json.dumps(company_info if company_info else {})
        )
        
        # Generate analysis using Gemini
        response = await self.model.generate_content_async(prompt)
        
        # Parse the response text to extract JSON
        try:
            response_text = response.text
            
            # Clean the response if it contains markdown code blocks
            if "```json" in response_text:
                json_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                json_text = response_text.split("```")[1].split("```")[0].strip()
            else:
                json_text = response_text
                
            analysis_data = json.loads(json_text)
            
            # Create the analysis result
            return AnalysisResult(
                lead_id=lead_data["id"],
                company_details=analysis_data["company_details"],
                llm_analysis=analysis_data["analysis"],
                final_decision=analysis_data["decision"]
            )
        except Exception as e:
            print(f"Error parsing analysis response: {str(e)}")
            # Fallback with partial data
            return AnalysisResult(
                lead_id=lead_data["id"],
                company_details={"error": "Failed to parse company details"},
                llm_analysis=f"Error analyzing lead: {str(e)}",
                final_decision="Maybe"  # Default to "Maybe" on error
            )