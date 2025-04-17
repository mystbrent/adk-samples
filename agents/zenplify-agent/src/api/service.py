from uuid import UUID, uuid4
from typing import Dict, Optional, List, Any
from .schemas import UserCreate, QAPairCreate

class AutofillService:
    def __init__(self):
        # In-memory storage
        self.users: Dict[UUID, Dict] = {}
        self.qa_pairs: Dict[UUID, Dict] = {}
    
    def create_user(self, user_data: UserCreate) -> Dict[str, Any]:
        """Create a new user."""
        user_id = uuid4()
        
        user_dict = {
            "id": user_id,
            "first_name": user_data.first_name,
            "last_name": user_data.last_name,
            "email": user_data.email,
            "github_username": user_data.github_username,
            "linkedin_url": user_data.linkedin_url
        }
        
        self.users[user_id] = user_dict
        return user_dict

    def create_qa_pair(self, qa_data: QAPairCreate) -> Dict[str, Any]:
        """Create a new QA pair for a user."""
        if qa_data.user_id not in self.users:
            raise ValueError(f"User with ID {qa_data.user_id} not found")
        
        qa_id = uuid4()
        qa_dict = {
            "id": qa_id,
            "user_id": qa_data.user_id,
            "question": qa_data.question,
            "answer": qa_data.answer,
            "context": qa_data.context,
        }
        
        self.qa_pairs[qa_id] = qa_dict
        return qa_dict 