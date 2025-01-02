import google.generativeai as genai
GEMINI_API_KEY = "AIzaSyAFN7Jn5lLXgeXPH0H7jc8CX63QGsMrzoE"
genai.configure(api_key=GEMINI_API_KEY)
for m in genai.list_models():
    if 'generateContent' in m.supported_generation_methods:
        print(m.name)