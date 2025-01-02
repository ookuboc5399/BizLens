from typing import List
import openai
from ..company_service import CompanyService

class ChatService:
    def __init__(self):
        self.company_service = CompanyService()

    async def get_chat_response(self, message: str) -> str:
        """
        Get a response from the AI model for a user's financial question.
        """
        try:
            # Get relevant company data that might be needed for context
            # This can be expanded based on the specific needs
            
            response = await openai.ChatCompletion.acreate(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": """You are a financial advisor assistant specialized in Japanese and US markets. 
                        You help users understand company financials, stock indicators, and market analysis. 
                        Focus on providing accurate information about:
                        - Financial statements and metrics
                        - Stock price indicators
                        - Company valuations
                        - Balance sheet analysis
                        - Industry comparisons
                        Always explain financial terms clearly and provide context for your answers."""
                    },
                    {"role": "user", "content": message}
                ],
                temperature=0.7,
                max_tokens=500
            )
            
            return response.choices[0].message.content
        except Exception as e:
            raise Exception(f"Error getting chat response: {str(e)}")
