from typing import List

class MockChatService:
    def __init__(self):
        self.responses = {
            "balance sheet": "A balance sheet shows a company's assets, liabilities, and shareholders' equity at a specific point in time. It provides a snapshot of a company's financial position.",
            "per": "Price-to-Earnings Ratio (PER) is a valuation metric that compares a company's stock price to its earnings per share. A lower PER might indicate a more attractive investment.",
            "roe": "Return on Equity (ROE) measures a company's profitability relative to shareholders' equity. An ROE of 12% or higher is generally considered good.",
            "revenue": "Revenue, or sales, represents the total amount of money a company generates from its business activities before any expenses are deducted.",
            "default": "I can help you understand company financials, stock indicators, and market analysis. What specific aspect would you like to learn about?"
        }

    async def get_chat_response(self, message: str) -> str:
        """
        Get a mock response based on keywords in the user's message.
        """
        message = message.lower()

        for keyword, response in self.responses.items():
            if keyword in message:
                return response

        return self.responses["default"]
