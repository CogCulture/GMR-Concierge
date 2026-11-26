# GMR Aerocity chatbot (prototype)

Answers questions using website_info.txt and the CSV files in the sheets folder.
Needs Python 3.10 or newer and a Gemini API key.

## Run it

Open a terminal in this folder.

Windows (Command Prompt):

    python -m venv venv
    venv\Scripts\activate
    pip install -r requirements.txt
    set GEMINI_API_KEY=your-key
    python get_website_text.py
    streamlit run app.py

Mac:

    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    export GEMINI_API_KEY="your-key"
    python get_website_text.py
    streamlit run app.py

## Files you may change

- pages.txt: website links to copy
- extra_info.txt: facts you type yourself
- sheets/: the events sheet saved as CSV
- qa_data.json: the 8 question buttons
