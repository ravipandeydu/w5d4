from openai import OpenAI
import base64

def analyze_image_with_gpt(image_path: str, query: str):
    with open(image_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    response = client.chat.completions.create(
        model="gpt-4-vision-preview",
        messages=[{"role": "user", "content": [{"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}}, {"type": "text", "text": query}]}]
    )
    return response.choices[0].message.content
