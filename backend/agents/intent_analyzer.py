import json
import logging
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from backend.config.settings import settings

logger = logging.getLogger(__name__)

class IntentAnalyzer:
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert Sales Intent Analyst.
            Analyze the following email reply from a prospect and classify their intent.
            
            Classification Categories:
            - POSITIVE: Interested in a meeting, asking for a demo, clear buying signal, or asking for a discovery call.
            - NEUTRAL: Asking a clarifying question, asking for more info, or not yet convinced but not a rejection.
            - NEGATIVE: Explicit rejection, "not interested", "remove me", or clearly stating they are not the right person / no budget.
            
            Provide the output in strict JSON format:
            {{
                "intent": "POSITIVE" | "NEUTRAL" | "NEGATIVE",
                "confidence": 0.0 to 1.0,
                "reasoning": "brief explanation"
            }}
            """),
            ("human", "Prospect Reply:\n\n{reply_text}")
        ])

    async def analyze(self, reply_text: str):
        try:
            chain = self.prompt | self.llm
            response = await chain.ainvoke({"reply_text": reply_text})
            
            content = response.content.strip()
            logger.info(f"Intent Analysis Raw Output: {content}")
            
            # Extract JSON
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            # Remove possible JSON prefix/suffix garbage
            content = content.strip()
            if not content.startswith("{"):
                start = content.find("{")
                end = content.rfind("}")
                if start != -1 and end != -1:
                    content = content[start:end+1]

            result = json.loads(content)
            logger.info(f"Classified Intent: {result.get('intent')} (Confidence: {result.get('confidence')})")
            return result
        except Exception as e:
            logger.error(f"Error analyzing intent: {e}")
            return {
                "intent": "NEUTRAL",
                "confidence": 0,
                "reasoning": f"Analyzer error: {str(e)}"
            }
