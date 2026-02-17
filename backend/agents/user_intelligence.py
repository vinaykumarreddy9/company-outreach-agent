from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_tavily import TavilySearch
from backend.config.settings import settings
from backend.schemas.campaign import Campaign, CompanyProfile
from backend.graphs.state import AgentState
from backend.services.neon_db import update_campaign_profile
import trafilatura
from playwright.async_api import async_playwright
import logging
from typing import List, Set
import asyncio
import httpx

logger = logging.getLogger(__name__)

class UserIntelligenceAgent:
    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            api_key=settings.OPENAI_API_KEY,
            temperature=0
        )
        self.search = TavilySearch(
            max_results=5,
            tavily_api_key=settings.TAVILY_API_KEY
        )
        self.structured_llm = self.llm.with_structured_output(CompanyProfile)
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an expert business analyst. Your goal is to research a company and create a comprehensive profile. "
                       "You will be provided with text extracted from multiple pages of the company website (Homepage, About, Products/Offerings). "
                       "Your primary task is to extract a detailed list of products/services and the company's core value proposition. "
                       "Focus on factual data found in the text. "
                       "If specific information is missing, infer reasonable values but prioritize direct extraction."),
            ("user", "Company Name: {company_name}\nProduct Description: {product_description}\n\nWebsite Content from multiple pages:\n{website_content}")
        ])

    async def scrape_url(self, url: str) -> str:
        """Tiered scraping: Trafilatura -> HTTPX (Verify=False) -> Playwright."""
        try:
            print(f"  --> Attempting Trafilatura for: {url}")
            downloaded = await asyncio.to_thread(trafilatura.fetch_url, url)
            text = await asyncio.to_thread(trafilatura.extract, downloaded) if downloaded else None
            
            # If trafilatura fails (e.g. SSL error), try HTTPX without verification
            if not text:
                print(f"  --> Trafilatura failed or returned empty. Trying HTTPX (verify=False) for: {url}")
                async with httpx.AsyncClient(verify=False, timeout=10.0) as client:
                    try:
                        resp = await client.get(url, follow_redirects=True)
                        if resp.status_code == 200:
                            text = await asyncio.to_thread(trafilatura.extract, resp.text)
                    except Exception as he:
                        print(f"      HTTPX also failed: {he}")

            # If still fails or returns very little content, use Playwright
            if not text or len(text.split()) < 100:
                print(f"  --> Content too low. Falling back to Playwright for: {url}")
                
                # Check for Windows Proactor loop to avoid NotImplementedError
                if asyncio.get_event_loop_policy().__class__.__name__ != 'WindowsProactorEventLoopPolicy' and asyncio.get_event_loop().__class__.__name__ != 'ProactorEventLoop':
                    logger.warning("Event loop may not support subprocesses (Playwright). Skipping Playwright to avoid crash.")
                    return text or ""

                async with async_playwright() as p:
                    try:
                        browser = await p.chromium.launch(headless=True)
                        context = await browser.new_context(ignore_https_errors=True)
                        page = await context.new_page()
                        await page.route("**/*.{png,jpg,jpeg,svg,gif,webp,css,woff,woff2}", lambda route: route.abort())
                        await page.goto(url, wait_until="domcontentloaded", timeout=20000)
                        html = await page.content()
                        await browser.close()
                        
                        if html:
                            playwright_text = await asyncio.to_thread(trafilatura.extract, html)
                            # Only replace if playwright got significantly more content
                            if playwright_text and len(playwright_text) > len(text or ""):
                                text = playwright_text
                    except Exception as e:
                        logger.warning(f"Playwright navigation failed for {url}: {e}")
            
            return text or ""
        except Exception as e:
            logger.error(f"Failed to scrape {url} asynchronously: {e}")
            return f"Error scraping {url}: {str(e)}"

    async def find_key_urls(self, company_name: str, base_url: str) -> List[str]:
        """Find About, Products, and Offerings URLs via Tavily search."""
        try:
            print(f"Searching for deep links for {company_name} (async)...")
            search_query = f"{company_name} {base_url} about us products services offerings"
            search_response = await self.search.ainvoke({"query": search_query})
            results = search_response.get('results', [])
            
            urls = [base_url]
            
            # Simple heuristic
            keywords = ['about', 'product', 'service', 'offering', 'solution']
            for res in results:
                url = res['url']
                if any(kw in url.lower() for kw in keywords):
                    if url not in urls:
                        urls.append(url)
            
            return urls[:4]
        except Exception as e:
            logger.error(f"Error finding key URLs asynchronously: {e}")
            return [base_url]

    async def run(self, state: AgentState) -> AgentState:
        try:
            campaign = state.get("campaign_data")
            if not campaign:
                state["errors"].append("No campaign data found in state.")
                return state

            print(f"Running UserIntelligenceAgent Deep Scan (async) for: {campaign.user_company_name}")
            
            # 1. Find the main domain first
            try:
                home_search = await self.search.ainvoke({"query": f"{campaign.user_company_name} official website"})
                results = home_search.get('results', [])
                base_url = results[0]['url'] if results else ""
            except Exception as e:
                print(f"Initial async search failed: {e}")
                base_url = ""

            if not base_url:
                state["errors"].append(f"Could not find a website for {campaign.user_company_name}")
                return state

            # 2. Find deep links (About, Products, etc.)
            key_urls = await self.find_key_urls(campaign.user_company_name, base_url)
            print(f"Found {len(key_urls)} URLs to scan (async): {key_urls}")

            # 3. Scrape all relevant URLs
            consolidated_content = ""
            for url in key_urls:
                print(f"Scanning (async): {url}...")
                page_text = await self.scrape_url(url)
                if page_text and "Error scraping" not in page_text:
                    consolidated_content += f"\n--- CONTENT FROM {url} ---\n{page_text}\n"

            # 4. Synthesize Profile with LLM
            if not consolidated_content.strip():
                state["errors"].append(f"Failed to extract any text from {base_url}")
                return state

            print(f"Synthesizing profile (async) from {len(consolidated_content)} chars of text...")
            chain = self.prompt | self.structured_llm
            try:
                profile = await chain.ainvoke({
                    "company_name": campaign.user_company_name,
                    "product_description": campaign.product_description,
                    "website_content": consolidated_content[:12000]
                })
                
                campaign.user_company_profile = profile
                state["campaign_data"] = campaign
                state["current_agent"] = "UserIntelligenceAgent"
                
                # Persist Profile
                campaign_id = state.get("campaign_id")
                if campaign_id:
                    await update_campaign_profile(campaign_id, profile.dict())
                    print(f"User company profile persisted for campaign: {campaign_id}")

                print(f"UserIntelligenceAgent Deep Scan completed (async). Products: {len(profile.key_offerings)}")
            except Exception as e:
                error_msg = f"Error synthesizing profile asynchronously: {str(e)}"
                logger.error(error_msg)
                state["errors"].append(error_msg)
                
        except Exception as e:
            error_msg = f"Panic in UserIntelligenceAgent (async): {str(e)}"
            logger.error(error_msg)
            state["errors"].append(error_msg)
            
        return state
