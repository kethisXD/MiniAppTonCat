from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import RPi.GPIO as GPIO
import uvicorn

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# CHANGED TO: Physical Pin 37 = BCM GPIO 26
LIGHT_PIN = 26
GPIO.setmode(GPIO.BCM)
GPIO.setup(LIGHT_PIN, GPIO.OUT)

@app.get("/")
def read_root():
    return {"status": "Hardware API Ready"}

@app.post("/light/{state}")
def toggle_light(state: str):
    if state.lower() == "on":
        GPIO.output(LIGHT_PIN, GPIO.HIGH)
        return {"status": "success", "light": "ON"}
    elif state.lower() == "off":
        GPIO.output(LIGHT_PIN, GPIO.LOW)
        return {"status": "success", "light": "OFF"}
    return {"error": "Invalid state"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
