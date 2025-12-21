import asyncio
import os

from dotenv import load_dotenv
from rich.console import Console
from rich.prompt import Prompt

from genkit.ai import Genkit
from genkit.plugins.compat_oai import OpenAI

# -------------------------------------------------
# Carga de variables de entorno
# -------------------------------------------------
load_dotenv()

if not os.getenv("OPENAI_API_KEY"):
    raise RuntimeError(
        "Falta la variable de entorno OPENAI_API_KEY. "
        "Crea un archivo .env a partir de .env.example."
    )

# -------------------------------------------------
# Inicialización de Genkit
# -------------------------------------------------
ai = Genkit(
    plugins=[
        OpenAI()
    ]
)

console = Console()


# -------------------------------------------------
# Función principal de chat
# -------------------------------------------------
async def chat_loop() -> None:
    console.print("[bold green]Chatbot Genkit (Python)[/bold green]")
    console.print("Escribe 'salir' para terminar.\n")

    while True:
        user_input = Prompt.ask("[bold cyan]Tú[/bold cyan]")

        if user_input.lower() in {"salir", "exit", "quit"}:
            console.print("\n[bold yellow]Hasta luego 👋[/bold yellow]")
            break

        try:
            response = await ai.generate(
                model="openai/gpt-4o",
                prompt=user_input,
            )

            console.print(
                "\n[bold magenta]Asistente[/bold magenta]: "
                f"{response.text}\n"
            )

        except Exception as e:
            console.print(
                f"[bold red]Error:[/bold red] {str(e)}"
            )


# -------------------------------------------------
# Entry point
# -------------------------------------------------
if __name__ == "__main__":
    asyncio.run(chat_loop())
