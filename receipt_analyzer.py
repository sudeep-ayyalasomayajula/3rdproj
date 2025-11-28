import streamlit as st
import google.generativeai as genai
import re  # Standard library for "Regular Expressions" (text pattern matching)
# 1. NEW LIBRARY: Pillow (PIL) for image handling
from PIL import Image
import json

# 2. PAGE CONFIG
st.set_page_config(page_title="Visual Receipt Analyzer", page_icon="🧾")
st.title("🧾 Visual Receipt Analyzer")
st.write("Upload a photo of a receipt, and AI will extract the data into JSON.")

# 3. API SETUP
api_key = None
if "GOOGLE_API_KEY" in st.secrets:
    api_key = st.secrets["GOOGLE_API_KEY"]
else:
    api_key = st.text_input("Enter Google API Key:", type="password")

if api_key:
    genai.configure(api_key=api_key)

    # 4. FILE UPLOADER FOR IMAGES
    # We only allow jpg, jpeg, and png files.
    uploaded_file = st.file_uploader("Choose an image...", type=["jpg", "jpeg", "png"])

    if uploaded_file is not None:
        # 5. DISPLAY THE IMAGE
        # We use PIL to open the uploaded file so we can show it to the user.
        image = Image.open(uploaded_file)
        st.image(image, caption='Uploaded Receipt', use_column_width=True)
        st.write("")
        st.write("Analyzing...")

        # 6. THE MULTIMODAL PROMPT
        # This is the most important part. We tell the AI exactly what structure we want.
        # We ask for JSON specifically so a computer can read the output easily.
        prompt = """
        You are an expert document analyzer. Look at this receipt image and extract the following information.
        Return the output ONLY as a raw JSON object with the following keys:
        - merchant_name (string)
        - transaction_date (string, format DD-MM-YYYY)
        - total_amount (float)
        - line_items (list of strings, just the item names)

        If you cannot find a value, return null for that key. Do not write any other text or markdown formatting like ```json.
        """

        # 7. CALLING THE CHEF (Gemini 2.5 Flash)
        # Note: We pass a LIST [prompt, image]. The model can handle both at once.
        # gemini-2.5-flash is excellent at vision tasks.
        model = genai.GenerativeModel('gemini-2.5-flash')
        # This line forces the AI to ONLY return JSON, no markdown wrapper
        generation_config={"response_mime_type": "application/json"}    
        
        with st.spinner("Extracting data..."):
            response = model.generate_content([prompt, image])
            
        # 8. PROCESSING THE RESPONSE (ROBUST VERSION)
        try:
            # 1. Get the raw text
            raw_text = response.text
            
            # 2. Use Regex to find the JSON content inside the markdown
            # This pattern looks for: ```json (optional) ... content ... ```
            json_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", raw_text)
            
            if json_match:
                # If we found a markdown block, extract just the content inside
                clean_json_str = json_match.group(1)
            else:
                # If no markdown, assume the whole text is JSON
                clean_json_str = raw_text

            # 3. specific cleanup for any trailing commas (common AI error)
            # This is optional but helpful for stability
            clean_json_str = clean_json_str.strip()

            # 4. Parse the cleaned string
            json_data = json.loads(clean_json_str)
            
            st.success("Data Extracted Successfully!")
            st.json(json_data)

        except json.JSONDecodeError as e:
            st.error(f"Failed to parse JSON even after cleaning.")
            st.warning(f"Error details: {e}")
            st.text("Raw AI Output was:")
            st.code(response.text)


