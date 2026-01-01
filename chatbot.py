import os
import re
import requests
from openai import OpenAI

# Cliente OpenAI
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# Info del negocio
with open("info_negocio.txt", "r", encoding="utf-8") as f:
    info_negocio = f.read()

# URL de Google Sheets (Apps Script)
GOOGLE_SHEETS_URL = "https://script.google.com/macros/s/AKfycbwfuqsNl2fghl05PLkCRmHyP8w37ab6WMwfFTXI_Ra_2SaRNXZlRPlw2w44U2tzaYk/exec"

# Palabras clave para detectar intención de contacto
PALABRAS_CONTACTO = [
    "cita", "reservar", "contactar", "llamar", "información", "telefono", "teléfono", "email"
]

def quiere_contacto(mensaje: str) -> bool:
    mensaje = mensaje.lower()
    return any(p in mensaje for p in PALABRAS_CONTACTO)

def extraer_nombre(mensaje: str):
    patrones = [
        r"me llamo\s+([a-záéíóúñ]+)",
        r"soy\s+([a-záéíóúñ]+)",
        r"mi nombre es\s+([a-záéíóúñ]+)"
    ]
    mensaje = mensaje.lower()
    for patron in patrones:
        match = re.search(patron, mensaje)
        if match:
            return match.group(1).capitalize()
    return None

def extraer_telefono(mensaje: str):
    match = re.search(r"\b\d{9}\b", mensaje)
    return match.group(0) if match else None

def guardar_lead(nombre: str, telefono: str):
    payload = {
        "nombre": nombre,
        "telefono": telefono
    }
    headers = {"Content-Type": "application/json"}  # IMPORTANTE
    try:
        r = requests.post(GOOGLE_SHEETS_URL, json=payload, headers=headers, timeout=5)
        print("Lead enviado, status:", r.status_code, r.text)
    except Exception as e:
        print("Error enviando lead a Google Sheets:", e)

def responder(mensaje: str):
    mensaje = mensaje.strip()

    # Mensaje vacío o saludo inicial
    if not mensaje:
        return {
            "tipo": "respuesta",
            "mensaje": "Hola, ¿en qué puedo ayudarte?"
        }

    # Intentar extraer datos de contacto
    nombre = extraer_nombre(mensaje)
    telefono = extraer_telefono(mensaje)

    if nombre and telefono:
        guardar_lead(nombre, telefono)
        return {
            "tipo": "lead",
            "mensaje": f"Gracias {nombre}, te contactaremos pronto."
        }

    # Si quiere contacto pero no ha dado datos aún
    if quiere_contacto(mensaje):
        return {
            "tipo": "lead",
            "mensaje": "Perfecto, ¿me dices tu nombre y teléfono?"
        }

    # Respuesta normal con OpenAI
    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "Responde como asistente de una clínica dental. "
                    "Usa solo la información del negocio. "
                    "Si algo no está en la información, di que no lo sabes.\n\n"
                    f"{info_negocio}"
                )
            },
            {"role": "user", "content": mensaje}
        ]
    )

    return {
        "tipo": "respuesta",
        "mensaje": response.choices[0].message.content
    }
