from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
import os
from ..services.mock_chat_service import MockChatService
from ..services.company_service import CompanyService

router = APIRouter(prefix="/chat", tags=["chat"])

class ChatMessage(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str

# Initialize mock service for testing
chat_service = MockChatService()

@router.post("", response_model=ChatResponse)
async def chat(message: ChatMessage):
    try:
        response = await chat_service.get_chat_response(message.message)
        return ChatResponse(response=response)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
