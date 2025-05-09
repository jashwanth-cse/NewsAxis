import google.generativeai as genai

# Configure once
genai.configure(api_key="AIzaSyCtfSZKV21ZbjpISuuXs6F4lGt0INoqCKw")

def summarize_with_gemini(description):
    model = genai.GenerativeModel('gemini-pro')

    prompt = f"Summarize the following YouTube short description into a short and catchy news headline:\n\n{description}"

    response = model.generate_content(prompt)
    summarized_text = response.text.strip()
    return summarized_text
