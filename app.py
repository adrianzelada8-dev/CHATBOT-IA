import os
import re
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from chatbot import responder

app = FastAPI()

# Orígenes permitidos separados por comas (por defecto, todos)
origenes = [o.strip() for o in os.environ.get("ALLOWED_ORIGINS", "*").split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origenes,
    allow_credentials=origenes != ["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class Mensaje(BaseModel):
    texto: str = Field(default="", max_length=2000)
    session_id: str = Field(default="default", max_length=64)


@app.post("/chat")
def chat(mensaje: Mensaje):
    session_id = re.sub(r"[^\w-]", "", mensaje.session_id) or "default"
    return responder(mensaje.texto, session_id)


@app.get("/")
def root():
    return {"mensaje": "Chatbot activo"}


@app.get("/health")
def health():
    return {"status": "ok"}
