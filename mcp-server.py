import os
import pickle
import base64
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly',
          'https://www.googleapis.com/auth/gmail.compose']

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
    service = build('gmail', 'v1', credentials=creds)
    return service

def get_unread_emails():
    service = get_gmail_service()
    results = service.users().messages().list(userId='me', labelIds=['UNREAD']).execute()
    messages = results.get('messages', [])
    emails = []
    for msg in messages:
        msg_data = service.users().messages().get(userId='me', id=msg['id']).execute()
        snippet = msg_data.get('snippet')
        emails.append({'id': msg['id'], 'snippet': snippet})
    return emails

def create_draft_reply(message_id, reply_text):
    service = get_gmail_service()
    message = service.users().messages().get(userId='me', id=message_id, format='raw').execute()
    from email.mime.text import MIMEText
    import base64

    original_msg = message['payload']
    mime_msg = MIMEText(reply_text)
    mime_msg['to'] = original_msg['headers'][0]['value']
    mime_msg['subject'] = 'Re: ' + original_msg['headers'][1]['value']

    raw = base64.urlsafe_b64encode(mime_msg.as_bytes()).decode()
    draft = {'message': {'raw': raw}}
    service.users().drafts().create(userId='me', body=draft).execute()
    print(f"Draft reply created for message ID: {message_id}")

if __name__ == "__main__":
    print("Unread emails:")
    for email in get_unread_emails():
        print(email)
