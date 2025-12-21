# run_api.py
import uvicorn
from api import app
from flows import register_flows

def main():
    register_flows()  # <-- asegura que Dev UI vea el flow
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")

if __name__ == "__main__":
    main()
