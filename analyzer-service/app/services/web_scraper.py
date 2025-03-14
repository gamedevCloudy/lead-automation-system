# analyzer-service/app/services/web_scraper.py
import aiohttp
from bs4 import BeautifulSoup
import re
import json
import google.generativeai as genai
import os
from typing import Dict, Any, List, Optional

class WebScraper:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable is not set")
        
        genai.configure(api_key=api_key)
        
        self.model = genai.GenerativeModel(
            model_name="gemini-1.5-pro",
            generation_config={
                "temperature": 0.2,
                "max_output_tokens": 1024,
            }
        )
        
        self.extraction_prompt = """
        Extract key business information from the following webpage content.
        Focus on:
        
        1. Company size (employees if mentioned)
        2. Company age/founding date
        3. Key products or services
        4. Client testimonials or major clients
        5. Any mentioned revenue figures
        6. Social media presence
        7. Company location(s)
        8. Industry or market segment
        
        Return ONLY a JSON object with these fields. If information is not found, use null.
        
        Webpage content: {content}
        
        Company being researched: {company_name}
        """

    async def _search_company(self, company_name: str) -> List[Dict[str, str]]:
        """Perform a simple search for company information"""
        # In a real implementation, this would use a search API
        # Here we'll simulate a simple search result
        search_query = f"{company_name} company website"
        
        # Encode the query for URL
        encoded_query = search_query.replace(" ", "+")
        
        async with aiohttp.ClientSession() as session:
            # Using DuckDuckGo as it's more scraper-friendly
            url = f"https://html.duckduckgo.com/html/?q={encoded_query}"
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            
            try:
                async with session.get(url, headers=headers) as response:
                    if response.status != 200:
                        return []
                    
                    html = await response.text()
                    soup = BeautifulSoup(html, "html.parser")
                    
                    results = []
                    for result in soup.select(".result"):
                        link_elem = result.select_one(".result__a")
                        if not link_elem:
                            continue
                            
                        link = link_elem.get("href", "")
                        # Extract URL from DuckDuckGo's redirect URL
                        match = re.search(r"uddg=([^&]+)", link)
                        if match:
                            url = match.group(1)
                        else:
                            continue
                            
                        # Get title
                        title = link_elem.get_text(strip=True)
                        
                        # Get snippet
                        snippet_elem = result.select_one(".result__snippet")
                        snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""
                        
                        results.append({
                            "title": title,
                            "url": url,
                            "snippet": snippet
                        })
                        
                        if len(results) >= 3:  # Limit to top 3 results
                            break
                            
                    return results
            except Exception as e:
                print(f"Error searching for company: {str(e)}")
                return []

    async def _scrape_webpage(self, url: str) -> Optional[str]:
        """Scrape content from a webpage"""
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status != 200:
                        return None
                        
                    html = await response.text()
                    soup = BeautifulSoup(html, "html.parser")
                    
                    # Remove script and style elements
                    for script in soup(["script", "style", "nav", "footer", "header"]):
                        script.decompose()
                        
                    # Get text
                    text = soup.get_text()
                    
                    # Break into lines and remove leading and trailing space
                    lines = (line.strip() for line in text.splitlines())
                    # Break multi-headlines into a line each
                    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                    # Remove blank lines
                    text = '\n'.join(chunk for chunk in chunks if chunk)
                    
                    return text[:15000]  # Limit text length
        except Exception as e:
            print(f"Error scraping webpage {url}: {str(e)}")
            return None

    async def _extract_company_info(self, text: str, company_name: str) -> Dict[str, Any]:
        """Extract structured information from webpage text using LLM"""
        if not text or len(text.strip()) < 100:
            return {"error": "Insufficient text content"}
            
        prompt = self.extraction_prompt.format(
            content=text[:10000],  # Limit content length
            company_name=company_name
        )
        
        try:
            response = await self.model.generate_content_async(prompt)
            
            # Parse JSON response
            response_text = response.text
            
            # Clean the response if it contains markdown code blocks
            if "```json" in response_text:
                json_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                json_text = response_text.split("```")[1].split("```")[0].strip()
            else:
                json_text = response_text
                
            return json.loads(json_text)
        except Exception as e:
            print(f"Error extracting company info: {str(e)}")
            return {"error": f"Failed to extract info: {str(e)}"}

    async def scrape_company_info(self, company_name: str) -> Dict[str, Any]:
        """Main method to search for and scrape company information"""
        # Search for company
        search_results = await self._search_company(company_name)
        
        if not search_results:
            return {
                "company_name": company_name,
                "error": "No search results found"
            }
        
        # Get the most relevant URL (first result)
        main_url = search_results[0]["url"]
        
        # Scrape the webpage
        webpage_text = await self._scrape_webpage(main_url)
        
        if not webpage_text:
            return {
                "company_name": company_name,
                "website_url": main_url,
                "error": "Failed to scrape webpage"
            }
        
        # Extract company information
        company_info = await self._extract_company_info(webpage_text, company_name)
        
        # Add metadata
        result = {
            "company_name": company_name,
            "website_url": main_url,
            "search_results": search_results,
            "found_data": company_info
        }
        
        # Optionally include raw text for debugging
        # result["raw_text"] = webpage_text
        
        return result