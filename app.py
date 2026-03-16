import streamlit as st
import json
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from openai import OpenAI

# --- 1. SETUP & KEYS ---
GROQ_API_KEY = st.secrets["GROQ_API_KEY"]

client = OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=GROQ_API_KEY
)

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

# --- 2. GMAIL LOGIC ---
def get_gmail_service():
    """Build Gmail service using OAuth token stored in Streamlit secrets."""
    gc = st.secrets["google_credentials"]

    creds = Credentials(
        token=gc["token"],
        refresh_token=gc["refresh_token"],
        token_uri=gc["token_uri"],
        client_id=gc["client_id"],
        client_secret=gc["client_secret"],
        scopes=SCOPES,
    )

    # Refresh the token if it has expired
    if not creds.valid:
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())

    return build('gmail', 'v1', credentials=creds)

# --- 3. GROQ AI LOGIC ---
def analyze_with_groq(subject, snippet):
    # Using Llama 3 on Groq for insane speed
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": "You are a fast-speed email assistant. Summarize into one short sentence and pick a category: [Urgent, Work, Personal, or Spam]."},
            {"role": "user", "content": f"Subject: {subject}\nSnippet: {snippet}"}
        ]
    )
    return response.choices[0].message.content

# --- 4. THE WEB INTERFACE (UI) ---
st.set_page_config(page_title="Lightning AI Email", page_icon="⚡")
st.title("⚡ Lightning Fast AI Email Agent")
st.write("Using Groq LPU technology to triage your inbox instantly.")

# THIS IS THE BUTTON
if st.button("🚀 Analyze My Inbox Now"):
    try:
        with st.status("Connecting to Gmail...", expanded=True) as status:
            service = get_gmail_service()
            results = service.users().messages().list(userId='me', maxResults=5).execute()
            messages = results.get('messages', [])

            if not messages:
                st.write("No emails found.")
                status.update(label="Complete!", state="complete")
            else:
                st.write(f"Found {len(messages)} emails. Analyzing...")

                for msg in messages:
                    full_msg = service.users().messages().get(userId='me', id=msg['id']).execute()
                    headers = full_msg['payload']['headers']
                    subject = next((h['value'] for h in headers if h['name'] == 'Subject'), "No Subject")
                    snippet = full_msg.get('snippet', '')

                    # Run Groq Analysis
                    analysis = analyze_with_groq(subject, snippet)

                    # Show in UI
                    with st.expander(f"✉️ {subject}"):
                        st.markdown(f"**AI Summary:** {analysis}")
                        st.caption(f"Preview: {snippet}")

                status.update(label="Analysis Finished!", state="complete")

    except Exception as e:
        st.error(f"Something went wrong: {e}")