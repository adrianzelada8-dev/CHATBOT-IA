import os
import re
import requests  # Nuevo: para enviar POST al Apps Script
from openai import OpenAI

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# Leer info del negocio
with open("info_negocio.txt", "r", encoding="utf-8") as f:
    info_negocio = f.read()

# Palabras que indican contacto
PALABRAS_CONTACTO = [
    "cita", "reservar", "contactar", "llamar", "información", "telefono", "email"
]

# URL de tu Apps Script (reemplaza con la tuya)
WEB_APP_URL = "https://script.google.com/macros/s/AKfycbwn4ijef_IF4FdZxJG8r0I6itKufNU-YztCgbu5GBjV9LgQ3GNfjQuZqytWLULIVxQ/exec"  # ej: https://script.google.com/macros/s/XXXX/exec

# Función para detectar si el usuario quiere contacto
def quiere_contacto(mensaje):
    mensaje = mensaje.lower()
    return any(p in mensaje for p in PALABRAS_CONTACTO)

# Función para extraer nombre y teléfono
def extraer_contacto(texto):
    # Detecta un número de teléfono de 9 dígitos
    telefono_match = re.search(r"\b\d{9}\b", texto)
    telefono = telefono_match.group(0) if telefono_match else None

    # Detecta un nombre simple: primera palabra con mayúscula
    nombre_match = re.search(r"\b[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+", texto)
    nombre = nombre_match.group(0) if nombre_match else None

    return nombre, telefono

# Función para guardar lead localmente
def guardar_lead(nombre, telefono):
    with open("leads.txt", "a", encoding="utf-8") as f:
        f.write(f"{nombre},{telefono}\n")

# Nueva función: enviar lead a Google Sheets vía Apps Script
def enviar_a_google_sheet(nombre, telefono):
    payload = {"nombre": nombre, "telefono": telefono}
    try:
        res = requests.post(WEB_APP_URL, json=payload, timeout=5)
        if res.status_code != 200:
            print("Error enviando lead a Google Sheet:", res.text)
    except Exception as e:
        print("Error enviando lead a Google Sheet:", e)

# Función principal de respuesta
def responder(mensaje):
    # Si el usuario quiere contacto pero aún no da nombre/teléfono
    if quiere_contacto(mensaje):
        return {
            "tipo": "lead",
            "mensaje": "Perfecto, ¿me dices tu nombre y contacto?"
        }

    # Intentamos extraer contacto
    nombre, telefono = extraer_contacto(mensaje)
    if nombre or telefono:
        guardar_lead(nombre or "Desconocido", telefono or "Desconocido")

        # Enviar al Google Sheet + correo
        enviar_a_google_sheet(nombre or "Desconocido", telefono or "Desconocido")

        return {
            "tipo": "lead_guardado",
            "mensaje": f"Gracias {nombre or 'Usuario'}, te contactaremos pronto."
        }

    # Respuesta normal con OpenAI
    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "Responde solo con la información del negocio. "
                    "Si no está, di que no lo sabes.\n\n"
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
