import streamlit as st
import os
from dotenv import load_dotenv # Add this
from openai import OpenAI

# Load the secret keys from the .env file
load_dotenv()
GROQ_API_KEY = os.getenv("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")

# Now your client uses the variable, not the hardcoded string
client = OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=GROQ_API_KEY
)

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

# --- 2. GMAIL LOGIC ---
def get_gmail_service():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
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

# THIS IS THE BUTTON - If this is missing, the page stays blank!
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