import fastapi
import schemas
import routers
from starlette.responses import RedirectResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

# TODO
""" 
* implement logic for rate limit.
* add proper error messages to all HTTPExceptions.
* change token value function to query something else.
* implement password reset. (very low prio)
* implement email verification. (very low prio)
* implement mail change (very low prio)
"""

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


@app.get(f"/", include_in_schema=False)
async def docs_redirect():
    return RedirectResponse(f"{root_url}/docs")

