from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import sys
from google import genai
from google.genai import types 
from google.genai.types import Part
import os
from dotenv import load_dotenv
from prompt.prompt import instruction_str

load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

#Initializing Google GenAI Agent
client = genai.Client(api_key=api_key)
# Get the absolute path to the directory relative to this script
current_dir = os.path.dirname(os.path.abspath(__file__))
target_dir = os.path.join(current_dir, "data")

files = [f for f in os.listdir(target_dir) if os.path.isfile(os.path.join(target_dir, f))]
print(files)

#Load PDF Files
def load_pdf_parts():
    pdf_parts = []
    
    for file_path in files:
        with open(f"data/{file_path}", "rb") as f:
            data = f.read()
            part = Part.from_bytes(data=data, mime_type="application/pdf")
            pdf_parts.append(part)
    return pdf_parts

pdf_parts = load_pdf_parts()

#Load Fast API
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins =["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],

)

#Creating the aibot
@app.post("/analyse-image/")
async def analyse_image(file: UploadFile = File(...)):
    image_bytes = await file.read()

    response = client.models.generate_content(
    model="gemini-2.5-flash",
    config=types.GenerateContentConfig(
        system_instruction=instruction_str),
    contents=[
    types.Part.from_bytes(
    data=image_bytes,
    mime_type='image/jpeg',
    ),
    'Analyze this image and provide relevant insight.'])

    return {"response": response.text}









