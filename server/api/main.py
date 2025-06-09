# server/main.py
from fastapi import FastAPI, Response, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.exceptions import HTTPException as StarletteHTTPException

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

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    status = exc.status_code
    template_name = "error.html"
    context = {"request": request, "status_code": status, "detail": exc.detail}
    return templates.TemplateResponse(template_name, context, status_code=status)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    return templates.TemplateResponse(
        "error.html",
        {"request": request, "status_code": 500, "detail": "Internal server error"},
        status_code=500
    )


@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    return Response(status_code=204)