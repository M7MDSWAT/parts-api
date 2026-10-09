from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from google import genai
import os

app = FastAPI(title="Spare Parts Extractor API")

api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

system_prompt = """
أنت مساعد ذكي متخصص في استخراج طلبات قطع غيار السيارات.
أخرج البيانات المكتملة بصيغة JSON فقط.
"""

class UserInput(BaseModel):
    message: str

@app.post("/extract")
def extract_part_info(data: UserInput):
    try:
        full_prompt = f"{system_prompt}\n\nطلب العميل: {data.message}"
        response = client.models.generate_content(
            model="models/gemini-3.8-flash",
            contents=full_prompt
        )
        return {"status": "success", "data": response.text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
