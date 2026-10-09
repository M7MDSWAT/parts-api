import json
import os
import re
from fastapi import FastAPI, HTTPException
import google.generativeai as genai
import httpx
from pydantic import BaseModel

app = FastAPI(title="Spare Parts Extractor API")

# 1. إعداد Gemini API
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY environment variable is missing!")

genai.configure(api_key=api_key)

# التعديل هنا: استخدام gemini-2.5-flash
model = genai.GenerativeModel("gemini-3.8-flash")

# رابط Webhook الباك إند الخاص بخويك
FRIEND_WEBHOOK_URL = "https://baseerah.duckdns.org/webhook/parts-search"


class UserInput(BaseModel):
    message: str


SYSTEM_PROMPT = """
أنت خبير في استخراج معلومات قطع غيار السيارات من النصوص.
قم باستخراج البيانات التالية فقط وإرجاعها بصيغة JSON صريح بدون أي مقدمات أو شرح:
- car_make (ماركة السيارة)
- car_model (موديل السيارة)
- year (سنة الصنع)
- part_name (اسم القطعة المطلوبة)
- condition (حالة القطعة: جديد / مستعمل / غير محدد)

مثال للناتج المطلوب:
{
  "car_make": "تويوتا",
  "car_model": "كامري",
  "year": 2020,
  "part_name": "صدام أمامي",
  "condition": "جديد"
}
"""


@app.get("/")
def read_root():
    return {"status": "API is running successfully"}


@app.post("/extract")
async def extract_and_forward(user_input: UserInput):
    try:
        prompt = f"{SYSTEM_PROMPT}\n\nنص المستخدم: {user_input.message}"
        response = model.generate_content(prompt)

        raw_text = response.text.strip()
        cleaned_text = re.sub(r"```json\s*|\s*```", "", raw_text).strip()
        extracted_data = json.loads(cleaned_text)

        async with httpx.AsyncClient(timeout=30.0) as client:
            webhook_response = await client.post(
                FRIEND_WEBHOOK_URL, json=extracted_data
            )

            try:
                friend_result = webhook_response.json()
            except Exception:
                friend_result = webhook_response.text

        return {
            "status": "success",
            "extracted_data": extracted_data,
            "result_from_backend": friend_result,
        }

    except json.JSONDecodeError:
        raise HTTPException(
            status_code=500, detail="فشل في تحويل استجابة Gemini إلى JSON"
        )
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=502, detail=f"تعذر الاتصال بسيرفر الباك إند: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
