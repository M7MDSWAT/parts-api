import os
import re
from fastapi import FastAPI, HTTPException
import google.generativeai as genai
from pydantic import BaseModel

# 1. تهيئة تطبيق FastAPI
app = FastAPI(title="Spare Parts Extractor API")

# 2. إعداد مفتاح Gemini API من متغيرات البيئة
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY environment variable is missing!")

genai.configure(api_key=api_key)

# 3. إعداد النموذج (تأكد من اسم النموذج المستعمل لديك)
model = genai.GenerativeModel("gemini-1.5-flash")


# 4. تحديد هيكل البيانات المدخلة
class UserInput(BaseModel):
    message: str


# 5. الـ Prompt الموجه لـ Gemini
SYSTEM_PROMPT = """
أنت خبير في استخراج معلومات قطع غيار السيارات من النصوص.
قم باستخراج البيانات التالية فقط وإرجاعها بصيغة JSON نصراني وصريح بدون أي مقدمات أو شرح:
- car_make (ماركة السيارة)
- car_model (موديل السيارة)
- year (سنة الصنع)
- part_name (اسم القطعة المطلوبة)
- condition (حالة القطعة: جديد / مستعمل / غير محدد)

مثال على المخرج المطلوبة:
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
async def extract_part_info(user_input: UserInput):
    try:
        # إرسال الطلب لـ Gemini
        prompt = f"{SYSTEM_PROMPT}\n\nنص المستخدم: {user_input.message}"
        response = model.generate_content(prompt)

        raw_text = response.text.strip()

        # تنظيف علامات الـ Markdown إن وجدت (مثل ```json)
        cleaned_text = re.sub(r"```json\s*|\s*```", "", raw_text).strip()

        # تحويل النص إلى Python Dictionary ليتم إرجاعه كـ JSON حقيقي
        import json

        parsed_json = json.loads(cleaned_text)

        return {"status": "success", "data": parsed_json}

    except json.JSONDecodeError:
        # في حال عدم تمكن النظام من تحويل النص لـ JSON
        return {"status": "success", "data": response.text}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error processing request: {str(e)}"
        )
