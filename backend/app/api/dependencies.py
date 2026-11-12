from fastapi import Depends
from sqlalchemy.orm import Session

from app.database import get_db

DbSession = Depends(get_db)
