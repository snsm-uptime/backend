
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, EmailStr


class EmailMessageModel(BaseModel):
    subject: Optional[str]
    from_email: Optional[str]
    to_emails: List[EmailStr] = []
    date: Optional[datetime]
    body: Optional[str]
