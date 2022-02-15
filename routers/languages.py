from typing import *
import fastapi
import schemas
from ignition.common.languages import Languages
router = fastapi.APIRouter()


@router.get("/languages")
async def supported_languages(
) -> List[schemas.snippet.supported_languages]:
    return list(Languages.languages.keys())
