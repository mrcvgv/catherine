# test_openai_key.py
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

api = os.getenv("OPENAI_API_KEY")
print("OPENAI_API_KEY prefix:", (api or "")[:10] + "..." if api else "None", "len=", len(api or ""))

if not api:
    print("❌ OPENAI_API_KEY not found in environment")
    exit(1)

try:
    client = OpenAI(api_key=api)
    resp = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role":"user","content":"1+1?"}],
        temperature=0
    )
    print("✅ OpenAI ok:", resp.choices[0].message.content)
except Exception as e:
    print("❌ OpenAI API failed:", e)