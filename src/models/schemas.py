from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field


class DateRange(BaseModel):
    start_date: datetime = Field(...,
                                 description="Start date in ISO format (YYYY-MM-DD)")
    end_date: datetime = Field(...,
                               description="End date in ISO format (YYYY-MM-DD)")


class EmailMessageModel(BaseModel):
    subject: Optional[str]
    from_email: Optional[str]
    to_emails: List[EmailStr] = []
    date: Optional[datetime]
    body: Optional[str]
