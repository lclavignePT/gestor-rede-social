from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from ...database.database import get_db
from ...database.models import User as UserModel
from ..schemas.user import Token, User, UserCreate
from ..security import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    authenticate_user,
    create_access_token,
    get_password_hash,
)

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/register", response_model=User, status_code=status.HTTP_201_CREATED)
async def register_user(user: UserCreate, db: Session = Depends(get_db)):
    """Registra um novo usuário."""
    try:
        print(f"Tentando registrar usuário: {user.email}")

        # Verificar se o email já existe
        db_user = db.query(UserModel).filter(UserModel.email == user.email).first()
        if db_user:
            print(f"Email já registrado: {user.email}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Email já registrado"
            )

        # Verificar se o username já existe
        db_user = (
            db.query(UserModel).filter(UserModel.username == user.username).first()
        )
        if db_user:
            print(f"Username já em uso: {user.username}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username já está em uso",
            )

        # Criar novo usuário
        hashed_password = get_password_hash(user.password)
        db_user = UserModel(
            email=user.email,
            username=user.username,
            hashed_password=hashed_password,
            full_name=user.full_name,
        )

        try:
            db.add(db_user)
            db.commit()
            db.refresh(db_user)
            print(f"Usuário registrado com sucesso: {user.email}")
            return db_user
        except Exception as e:
            db.rollback()
            print(f"Erro ao salvar usuário no banco: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Erro ao criar usuário: {str(e)}",
            )
    except HTTPException:
        raise
    except Exception as e:
        print(f"Erro inesperado: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro inesperado: {str(e)}",
        )


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    """Autentica um usuário e retorna o token de acesso."""
    try:
        print(f"Tentando autenticar usuário: {form_data.username}")

        # Autenticar usuário
        user = authenticate_user(db, form_data.username, form_data.password)
        if not user:
            print(f"Falha na autenticação: {form_data.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email ou senha incorretos",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Criar token de acesso
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.email}, expires_delta=access_token_expires
        )

        print(f"Usuário autenticado com sucesso: {form_data.username}")
        return {"access_token": access_token, "token_type": "bearer"}

    except HTTPException:
        raise
    except Exception as e:
        print(f"Erro inesperado no login: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro inesperado: {str(e)}",
        )
