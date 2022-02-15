from typing import *
import fastapi
import schemas
from ignition.common.languages import Languages
router = fastapi.APIRouter()


@router.get(
    "/languages",
    response_model=List[schemas.snippet.supported_languages])
async def supported_languages(
) -> List[schemas.snippet.supported_languages]:
    """
    lists all the languages supported by ignition.
    """
    return list(Languages.languages.keys())
