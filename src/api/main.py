import os
from typing import List

from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from ..agents.content_generator import ContentGenerator

app = FastAPI(title="Gerador de Posts - MVP")

# Configurar templates e arquivos estáticos
templates = Jinja2Templates(directory="templates")

# Montar diretório static apenas se ele existir
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

# Instanciar gerador de conteúdo
content_generator = ContentGenerator()


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Página inicial com formulário."""
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/generate")
async def generate_post(
    topic: str = Form(...),
    tone: str = Form(...),
    content_type: str = Form(...),
    personas: List[str] = Form(["adultos"]),  # Valor padrão para compatibilidade
):
    """Gera conteúdo baseado nos inputs do usuário."""
    try:
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
        raise HTTPException(status_code=500, detail=str(e))
