import os
from typing import List

from fastapi import Depends, FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from ..agents.content_generator import ContentGenerator
from ..database.models import User
from .routers import users
from .security import get_current_active_user

app = FastAPI(title="Gerador de Posts - MVP")

# Configurar templates e arquivos estáticos
templates = Jinja2Templates(directory="templates")

# Montar diretório static apenas se ele existir
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")


# Middleware para interceptar erros de autenticação
class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Se for erro de autenticação e a requisição espera HTML
        if response.status_code == 401 and "text/html" in request.headers.get(
            "accept", ""
        ):
            return RedirectResponse(url="/login", status_code=302)

        return response


app.add_middleware(AuthMiddleware)

# Incluir routers
app.include_router(users.router)

# Instanciar gerador de conteúdo
content_generator = ContentGenerator()


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Página inicial."""
    return templates.TemplateResponse("home.html", {"request": request})


@app.get("/generator", response_class=HTMLResponse)
async def generator_page(
    request: Request, current_user: User = Depends(get_current_active_user)
):
    """Página do gerador de posts."""
    return templates.TemplateResponse("generator.html", {"request": request})


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Página de login."""
    return templates.TemplateResponse("login.html", {"request": request})


@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    """Página de registro."""
    return templates.TemplateResponse("register.html", {"request": request})


@app.post("/generate")
async def generate_post(
    topic: str = Form(...),
    tone: str = Form(...),
    content_type: str = Form(...),
    personas: List[str] = Form(["adultos"]),  # Valor padrão para compatibilidade
    current_user: User = Depends(get_current_active_user),
):
    """Gera conteúdo baseado nos inputs do usuário."""
    try:
        print(f"Gerando conteúdo para usuário: {current_user.email}")
        if len(personas) == 1 and personas[0] == "adultos":
            # Modo compatibilidade - retorna único post
            content = await content_generator.generate_content(
                topic, tone, content_type
            )
            return content
        else:
            # Novo modo - retorna múltiplos posts por persona
            contents = await content_generator.generate_content_for_personas(
                topic=topic, tone=tone, content_type=content_type, personas=personas
            )
            return {"posts": contents, "count": len(contents)}
    except Exception as e:
        print(f"Erro na geração do post: {str(e)}")
        error_message = str(e)

        # Verificar se é um erro de violação de política
        if "content_policy_violation" in error_message:
            error_detail = "content_policy_violation: O conteúdo solicitado viola as políticas de uso da IA."
        else:
            error_detail = error_message

        raise HTTPException(status_code=500, detail=error_detail)
