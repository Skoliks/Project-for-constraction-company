from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.stroilandia_import_services import stroylandiya_import_service

router = APIRouter(prefix="/parsers", tags=["Parsers"])


@router.post("/stroylandiya/run")
async def run_stroylandiya_parser(db: Session = Depends(get_db)):
    try:
        result = await stroylandiya_import_service.run_import(db=db)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Parser failed: {e}")