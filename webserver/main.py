from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from .routes import router, AuthMiddleware, get_current_user
from fastapi import Request
from fastapi.responses import HTMLResponse
import os
from . import db as _db


app = FastAPI()

# Static and template dirs (use relative paths inside project)
here = os.path.dirname(__file__)
static_dir = os.path.join(here, 'static')
templates_dir = os.path.join(here, 'templates')

app.mount('/static', StaticFiles(directory=static_dir), name='static')
templates = Jinja2Templates(directory=templates_dir)

# Register router with product/auth endpoints
app.include_router(router)

# Basic home page
@app.get('/', response_class=HTMLResponse)
def home(request: Request):
    # If user is logged in, redirect them to product creation form
    user = get_current_user(request)
    if user:
        from fastapi.responses import RedirectResponse
        return RedirectResponse('/product/new')
    return templates.TemplateResponse('index.html', {'request': request, 'username': ''})

# Add auth middleware
app.add_middleware(AuthMiddleware)


@app.on_event('startup')
def startup_event():
    try:
        _db.init_db()
    except Exception as e:
        print('DB init error:', e)