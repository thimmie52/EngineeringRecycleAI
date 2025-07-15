from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from google import genai
from google.genai import types
from google.genai.types import Part
import os
from dotenv import load_dotenv
from prompt.prompt import instruction_str

# Load environment variables
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
client = genai.Client(api_key=api_key)

# Initialize FastAPI
app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://eco-analyser.vercel.app/", "http://localhost:3000"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

def load_pdf_parts():
    pdf_parts = []
    data_dir = "data"

    all_items = os.listdir(data_dir)
    pdf_files = [f for f in all_items if f.lower().endswith(".pdf")]

    for file_name in pdf_files:
        file_path = os.path.join(data_dir, file_name)
        try:
            with open(file_path, "rb") as f:
                data = f.read()

                # Skip empty files
                if len(data) == 0:
                    print(f"⚠️ Skipped empty PDF: {file_name}")
                    continue

                part = Part.from_bytes(data=data, mime_type="application/pdf")
                pdf_parts.append(part)

        except Exception as e:
            print(f"Failed to load {file_name}: {e}")

    return pdf_parts


pdf_parts = load_pdf_parts()
pdf_parts = pdf_parts[:8]

#  Image-only endpoint
@app.post(
    "/analyse-image/",
    summary="Analyse an uploaded image",
    description="Upload a JPEG image of an item. The AI will analyze it and suggest the best way to recycle it."
)
async def analyse_image(file: UploadFile = File(...)):
    """
    Analyse an image for recycling guidance.

    - **file**: JPEG image file of the item.
    - Returns a textual suggestion based on the image.
    """
    image_bytes = await file.read()

    if not image_bytes:
        return JSONResponse({"error": "Empty image file"}, status_code=400)

    contents = [
        types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg"),
        types.Part.from_text(text="Analyse the image and suggest the best way to recycle.")
    ]
  



    response = client.models.generate_content(
        model="gemini-2.5-flash",
        config=types.GenerateContentConfig(system_instruction=instruction_str),
        contents=[*pdf_parts,*contents]
    )

    return {"response": response.text}


@app.post(
    "/analyse-text/",
    summary="Analyse a text description",
    description="Submit a text description of an item. The AI will suggest how best to recycle or repurpose it."
)
async def analyse_text(prompt: str = Form(...)):
    """
    Analyse a text prompt for recycling advice.

    - **prompt**: Text description of the item.
    - Returns recycling suggestions.
    """
    if not prompt.strip():
        return JSONResponse({"error": "Prompt cannot be empty"}, status_code=400)

    contents = [
        types.Part.from_text(text=prompt.strip())
    ]

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        config=types.GenerateContentConfig(system_instruction=instruction_str),
        contents=[*pdf_parts,*contents]
    )

    return {"response": response.text}

