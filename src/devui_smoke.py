import time
from dotenv import load_dotenv

from genkit.ai import Genkit
from genkit.plugins.compat_oai import OpenAI

load_dotenv()  # <-- añade esto

ai = Genkit(plugins=[OpenAI()])

print("Runtime up. Sleeping to keep process alive...")
time.sleep(10**9)
