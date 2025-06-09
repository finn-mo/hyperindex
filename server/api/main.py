# server/main.py
from fastapi import FastAPI, Response
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from server.db.connection import init_db
from server.views.rolodex import router as rolodex_router
from server.views.yellowpages import router as yellowpages_router
from server.views.admin import router as admin_router
from server.views.auth import router as auth_view_router

app = FastAPI()
init_db()

app.mount("/static", StaticFiles(directory="server/static"), name="static")

# HTML view routers
app.include_router(rolodex_router)
app.include_router(yellowpages_router)
app.include_router(admin_router)
app.include_router(auth_view_router)

templates = Jinja2Templates(directory="server/templates")


@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    return Response(status_code=204)