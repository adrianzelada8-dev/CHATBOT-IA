from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from chatbot import responder

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # luego se limita en producción
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Mensaje(BaseModel):
    texto: str

@app.post("/chat")
def chat(mensaje: Mensaje):
    return responder(mensaje.texto)
