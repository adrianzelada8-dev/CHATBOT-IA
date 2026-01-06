import os
import json
import requests
from openai import OpenAI

# ===============================
# CONFIG
# ===============================
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

PALABRAS_CONTACTO = [
    "cita", "reservar", "contactar", "llamar",
    "información", "telefono", "teléfono", "email"
]

WEB_APP_URL = "https://script.google.com/macros/s/AKfycbwn4ijef_IF4FdZxJG8r0I6itKufNU-YztCgbu5GBjV9LgQ3GNfjQuZqytWLULIVxQ/exec"

# ===============================
# CARGAR INFO DEL NEGOCIO
# ===============================
with open("info_negocio.txt", "r", encoding="utf-8") as f:
    info_negocio = f.read()

# ===============================
# MEMORIA DE CONVERSACIÓN
# ===============================
estado_usuarios = {}  # Diccionario por usuario_id

# ===============================
# UTILIDADES
# ===============================
def quiere_contacto(mensaje: str) -> bool:
    mensaje = mensaje.lower()
    return any(p in mensaje for p in PALABRAS_CONTACTO)


def extraer_datos_contacto(mensaje: str):
    try:
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Extrae nombre y teléfono del mensaje del usuario.\n"
                        "Responde SOLO en JSON válido, sin texto adicional.\n"
                        "Formato:\n"
                        "{ \"nombre\": string | null, \"telefono\": string | null }\n"
                        "Normaliza el teléfono quitando espacios y símbolos."
                    )
                },
                {"role": "user", "content": mensaje}
            ]
        )

        contenido = response.choices[0].message.content.strip()
        datos = json.loads(contenido)
        return datos.get("nombre"), datos.get("telefono")

    except Exception as e:
        print("Error extrayendo datos de contacto:", e)
        return None, None


def enviar_a_google_sheet(nombre: str, telefono: str):
    payload = {"nombre": nombre, "telefono": telefono}
    try:
        res = requests.post(WEB_APP_URL, json=payload, timeout=5)
        if res.status_code != 200:
            print("Error Google Sheet:", res.text)
    except Exception as e:
        print("Error enviando a Google Sheet:", e)


def generar_respuesta_conversacional(mensaje_usuario: str):
    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "Eres una recepcionista profesional y amable de una clínica dental.\n"
                    "Responde de forma natural y cercana.\n"
                    "Usa la información del negocio si es relevante.\n"
                    "Si no tienes un dato exacto, responde de forma educada y ofrece ayuda.\n"
                    f"Información clínica:\n{info_negocio}"
                )
            },
            {"role": "user", "content": mensaje_usuario}
        ]
    )
    return response.choices[0].message.content

# ===============================
# FUNCIÓN PRINCIPAL
# ===============================
def responder(mensaje: str, usuario_id: str = "default"):
    mensaje = mensaje.strip()
    if usuario_id not in estado_usuarios:
        estado_usuarios[usuario_id] = {"contacto_preguntado": False}

    # 1️⃣ Mensaje vacío
    if not mensaje:
        return {"tipo": "respuesta", "mensaje": "Hola 😊 ¿En qué puedo ayudarte?"}

    # 2️⃣ Extraer datos de contacto
    nombre, telefono = extraer_datos_contacto(mensaje)

    # 3️⃣ Lead completo → guardar
    if nombre and telefono:
        enviar_a_google_sheet(nombre, telefono)
        estado_usuarios[usuario_id]["contacto_preguntado"] = True
        return {
            "tipo": "lead",
            "mensaje": f"Gracias {nombre}, hemos recibido tus datos y te contactaremos muy pronto."
        }

    # 4️⃣ Quiere contacto pero aún faltan datos
    if quiere_contacto(mensaje) and not estado_usuarios[usuario_id]["contacto_preguntado"]:
        estado_usuarios[usuario_id]["contacto_preguntado"] = True
        return {
            "tipo": "lead",
            "mensaje": "Perfecto 😊 ¿Me indicas tu nombre y teléfono para contactarte?"
        }

    # 5️⃣ Respuesta normal conversacional
    respuesta = generar_respuesta_conversacional(mensaje)

    return {"tipo": "respuesta", "mensaje": respuesta}
