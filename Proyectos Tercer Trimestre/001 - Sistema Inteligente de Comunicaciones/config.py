import os
from dotenv import load_dotenv

load_dotenv()

class Config:

    EMAIL_USUARIO = os.getenv("EMAIL_USUARIO")
    EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
    EMAIL_IMAP = os.getenv("EMAIL_IMAP")

    OLLAMA_URL = os.getenv(
        "OLLAMA_URL",
        "http://localhost:11434/api/generate"
    )

    OLLAMA_MODEL = os.getenv(
        "OLLAMA_MODEL",
        "qwen2.5:3b-instruct"
    )

    CANTIDAD_CORREOS = int(
        os.getenv("CANTIDAD_CORREOS", 10)
    )

    MAX_CARACTERES = int(
        os.getenv("MAX_CARACTERES", 5000)
    )
