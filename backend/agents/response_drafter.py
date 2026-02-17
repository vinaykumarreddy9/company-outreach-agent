import json
import logging
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from backend.config.settings import settings

logger = logging.getLogger(__name__)

class ResponseDrafter:
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a Principal Sales Correspondent.
            Your task is to draft a personalized reply to a prospect based on their intent.
            
            Context Provided:
            - Intent: {intent} (Reason: {reasoning})
            - Original Pitch: {original_pitch}
            - Prospect's Reply: {prospect_reply}
            
            Guidelines:
            - If intent is POSITIVE: Focus on scheduling a 15-min discovery call. Suggest 2-3 specific times or ask for their calendar.
            - If intent is NEUTRAL: Address their specific question/concerns from the reply. Pivot back to the value prop of the original pitch.
            - Tone: High-end, professional, yet empathetic and human.
            
            Provide the output in JSON format:
            {{
                "subject": "Re: {original_subject}",
                "body": "The email body text here."
            }}
            """),
            ("human", "Draft the response now.")
        ])

    async def draft_response(self, intent_data: dict, original_email: dict, prospect_reply: str):
        try:
            chain = self.prompt | self.llm
            response = await chain.ainvoke({
                "intent": intent_data.get("intent"),
                "reasoning": intent_data.get("reasoning"),
                "original_pitch": original_email.get("body"),
                "original_subject": original_email.get("subject"),
                "prospect_reply": prospect_reply
            })
            
            content = response.content
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            
            return json.loads(content)
        except Exception as e:
            logger.error(f"Error drafting response: {e}")
            return None
    async def draft_reminder(self, timer_type: str, original_email: dict):
        try:
            reminder_prompt = ChatPromptTemplate.from_messages([
                ("system", """You are a Principal Sales Correspondent.
                no reply was received to the previous email. Draft a polite, professional follow-up.
                
                Context:
                - Original Email Body: {original_body}
                - Original Subject: {original_subject}
                - Stage: {timer_type} (REMINDER_1 = 3 days later, REMINDER_2 = 7 days later)
                
                Guidelines:
                - REMINDER_1: "Just floating this to the top of your inbox..." very brief.
                - REMINDER_2: "One last check-in before I assume this isn't a priority..." strictly professional.
                - Do not be nagging. Be helpful.
                
                Output JSON:
                {{
                    "subject": "Re: {original_subject}",
                    "body": "Your draft here."
                }}
                """),
                ("human", "Draft the reminder.")
            ])
            
            chain = reminder_prompt | self.llm
            response = await chain.ainvoke({
                "original_body": original_email.get("body"),
                "original_subject": original_email.get("subject"),
                "timer_type": timer_type
            })
            
            content = response.content
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            
            return json.loads(content)
        except Exception as e:
            logger.error(f"Error drafting reminder: {e}")
            return None
