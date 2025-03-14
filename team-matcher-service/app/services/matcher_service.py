# team-matcher-service/app/services/matcher_service.py
import os
import httpx
import numpy as np
from typing import List, Dict, Any
import google.generativeai as genai
from sklearn.metrics.pairwise import cosine_similarity

class MatcherService:
    """Service for matching leads to team members based on relevance"""
    
    def __init__(self):
        # Initialize Google Gemini API
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY environment variable is not set")
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-pro')
        self.database_url = os.getenv("DATABASE_SERVICE_URL", "http://localhost:8000")
    
    async def get_lead_data(self, lead_id: int) -> Dict[str, Any]:
        """Fetch lead data from the database service"""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.database_url}/leads/{lead_id}")
            if response.status_code != 200:
                raise ValueError(f"Failed to fetch lead data: {response.text}")
            return response.json()
    
    async def get_team_members(self) -> List[Dict[str, Any]]:
        """Fetch all team members from the database service"""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.database_url}/team-members")
            if response.status_code != 200:
                raise ValueError(f"Failed to fetch team members: {response.text}")
            return response.json()
    
    async def generate_embeddings(self, text: str) -> List[float]:
        """Generate embeddings for the given text using Gemini"""
        response = self.model.generate_content(
            f"""
            Create a numerical embedding vector representation of the following text.
            The embedding should capture the semantic meaning of the text.
            Return ONLY the vector as a Python list of 768 float values.
            
            Text: {text}
            """
        )
        
        # Extract the embedding from the response
        embedding_text = response.text.strip()
        try:
            # Clean and parse the embedding
            clean_text = embedding_text.replace('[', '').replace(']', '').replace('\n', '')
            embedding = [float(x) for x in clean_text.split(',')]
            
            # Normalize to unit length
            norm = np.linalg.norm(embedding)
            if norm > 0:
                embedding = [x / norm for x in embedding]
            
            return embedding
        except Exception as e:
            raise ValueError(f"Failed to parse embedding: {e}")
    
    async def find_matches(self, lead_id: int, analysis_context: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Find matching team members for the given lead"""
        # Get lead data
        lead_data = await self.get_lead_data(lead_id)
        
        # Get all team members
        team_members = await self.get_team_members()
        
        # Create a combined text representation of the lead's requirements
        lead_text = f"""
        Company: {lead_data.get('company_name', '')}
        Industry: {lead_data.get('industry', '')}
        Service Needed: {lead_data.get('service_type', '')}
        Description: {lead_data.get('message', '')}
        Revenue: {lead_data.get('revenue', '')}
        """
        
        # If we have analysis context, add it to the lead text
        if analysis_context:
            lead_text += f"\nAnalysis: {analysis_context.get('llm_analysis', '')}"
        
        # Generate embedding for the lead
        lead_embedding = await self.generate_embeddings(lead_text)
        
        # Calculate similarity scores for each team member
        results = []
        for member in team_members:
            # Create text representation of the team member
            member_text = f"""
            Name: {member.get('name', '')}
            Role: {member.get('role', '')}
            Skills: {', '.join(member.get('skills', []))}
            Expertise: {member.get('expertise_summary', '')}
            """
            
            # Generate embedding for the team member
            member_embedding = await self.generate_embeddings(member_text)
            
            # Calculate cosine similarity
            similarity = cosine_similarity([lead_embedding], [member_embedding])[0][0]
            
            # Generate matching reasons using the model
            matching_prompt = f"""
            Lead information:
            {lead_text}
            
            Team member information:
            {member_text}
            
            Provide exactly 3 specific reasons why this team member would be a good match for this lead.
            Each reason should be brief (1-2 sentences) and specific to this particular match.
            Return only a JSON list of strings, with each string being a reason.
            """
            
            matching_response = self.model.generate_content(matching_prompt)
            try:
                # Parse the matching reasons
                import json
                matching_reasons_text = matching_response.text.strip()
                # Remove code formatting if present
                if "```json" in matching_reasons_text:
                    matching_reasons_text = matching_reasons_text.split("```json")[1].split("```")[0].strip()
                matching_reasons = json.loads(matching_reasons_text)
            except Exception:
                # Fallback if parsing fails
                matching_reasons = ["Relevant expertise match", "Similar project experience", "Compatible skill set"]
            
            results.append({
                "team_member_id": member.get("id"),
                "name": member.get("name"),
                "email": member.get("email"),
                "role": member.get("role"),
                "relevance_score": float(similarity),
                "matching_reasons": matching_reasons
            })
        
        # Sort by relevance score in descending order
        results.sort(key=lambda x: x["relevance_score"], reverse=True)
        
        # Return top 3 matches
        return results[:3]
    
    async def match_team_to_lead(self, lead_id: int, analysis_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Match a team to a lead and return the result"""
        matches = await self.find_matches(lead_id, analysis_context)
        
        return {
            "lead_id": lead_id,
            "matches": matches
        }