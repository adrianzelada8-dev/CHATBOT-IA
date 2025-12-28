import os
from openai import OpenAI

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))


with open("info_negocio.txt", "r", encoding="utf-8") as f:
    info_negocio = f.read()

PALABRAS_CONTACTO = [
    "cita", "reservar", "contactar", "llamar", "información", "telefono", "email"
]

def quiere_contacto(mensaje):
    mensaje = mensaje.lower()
    return any(p in mensaje for p in PALABRAS_CONTACTO)

def responder(mensaje):
    if quiere_contacto(mensaje):
        return {
            "tipo": "lead",
            "mensaje": "Perfecto, ¿me dices tu nombre y contacto?"
        }

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
