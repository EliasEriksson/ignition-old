import asyncio
import logging
import ignition
import fastapi
import schemas
import routers
from starlette.responses import RedirectResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

# TODO
""" 
* integrate with fastapi auth.
* implement logic for rate limit.
* add proper error messages to all HTTPExceptions.
* change token value function to query something else.
* implement password reset. (very low prio)
* implement email verification. (very low prio)
* implement mail change (very low prio)
"""

loop = asyncio.get_event_loop()

server = ignition.Server(10, ignition.get_logger(__name__, logging.INFO), loop=loop)
root_url = "/ignition/api"
app = fastapi.FastAPI(
    docs_url=f"{root_url}/docs",
    openapi_url=f"{root_url}/openapi.json"
)

app.include_router(
    routers.auth.router,
    prefix=root_url
)

app.include_router(
    routers.snippet.router,
    prefix=root_url
)

app.include_router(
    routers.languages.router,
    prefix=root_url
)

auth_scheme = OAuth2PasswordBearer(tokenUrl=f"{root_url}/token/")


@app.get(f"/", include_in_schema=False)
async def docs_redirect():
    return RedirectResponse(f"{root_url}/docs")


@app.post(f"{root_url}/process/")
async def process(
        request: schemas.snippet.SnippetData
):
    status, response = await server.process(request.dict())
    return {"status": status, "response": response}
