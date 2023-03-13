import os
import base64
import json
from google.oauth2.credentials import Credentials
from googleapiclient.errors import HttpError
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage

class Gmail:
    def __init__(self, credentials_path: str):
        self.service = self._create_gmail_service(credentials_path)
    
    def _create_gmail_service(self, credentials_path: str):
        creds = None
        if os.path.exists('token.json'):
            creds = Credentials.from_authorized_user_file('token.json', ['https://www.googleapis.com/auth/gmail.modify'])
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(credentials_path, ['https://www.googleapis.com/auth/gmail.modify'])
                creds = flow.run_local_server(port=0)
            with open('token.json', 'w') as token:
                token.write(creds.to_json())
        return build('gmail', 'v1', credentials=creds)
    
    def get_messages(self, query: str, max_results: int, after_date: datetime):
        """Get a list of messages matching the specified query."""
        after_date_str = after_date.strftime('%Y/%m/%d')
        query = f'{query} after:{after_date_str}'
        try:
            response = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=max_results
            ).execute()
            messages = []
            if 'messages' in response:
                messages.extend(response['messages'])
            while 'nextPageToken' in response:
                page_token = response['nextPageToken']
                response = self.service.users().messages().list(
                    userId='me',
                    q=query,
                    maxResults=max_results,
                    pageToken=page_token
                ).execute()
                if 'messages' in response:
                    messages.extend(response['messages'])
            return messages
        except HttpError as error:
            print(f'An error occurred: {error}')
            return []

    def get_email_by_max(self, maxResults=1, after_date=datetime.utcnow()):
        try:
            return_result = []
            after_date_str = after_date.strftime('%Y/%m/%d')
            query = f'after:{after_date_str}'
            results = self.service.users().messages().list(userId='me', maxResults=maxResults, q=query).execute()
            
            for result in results['messages']:
                last_email_id = result['id']
                message = self.service.users().messages().get(userId='me', id=last_email_id).execute()
                message_subject = ""
                message_body = ""
                message_sender = ""

                for header in message['payload']['headers']:
                    if header['name'] == 'Subject':
                        message_subject = header['value']
                    if header['name'] == 'From':
                        message_sender = header['value']

                if 'parts' in message['payload']:
                    parts = message['payload']['parts']
                    for part in parts:
                        if part['mimeType'] == 'text/plain':
                            message_body = part['body']['data']
                        elif part['mimeType'] == 'text/html':
                            message_body = part['body']['data']
                else:
                    message_body = message['payload']['body']['data']

                decoded_message = base64.urlsafe_b64decode(message_body.encode('UTF-8')).decode('UTF-8')
                return_result.append((message_subject, decoded_message, message_sender))

            return return_result
        except HttpError as error:
            print('An error occurred: %s' % error)
            return None      
             
    def send_email(self, to: str, subject: str, message_text: str, message_html: str = None, attachment_path: str = None):
        """Send an email message."""
        message = MIMEMultipart()
        message['to'] = to
        message['subject'] = subject
        if message_html:
            message.attach(MIMEText(message_text, 'plain'))
            message.attach(MIMEText(message_html, 'html'))
        else:
            message.attach(MIMEText(message_text))
        if attachment_path:
            with open(attachment_path, 'rb') as attachment:
                image = MIMEImage(attachment.read())
                message.attach(image)
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        try:
            message = self.service.users().messages().send(
                userId='me',
                body={'raw': raw_message}
            ).execute()
            print(f'Message Id: {message["id"]}')
        except HttpError as error:
            print(f'An error occurred: {error}')
    
    def send_email_with_attachment(self, to, subject, message_text, file_path, subtype):
        """Sends an email with an attachment to the specified recipient.

        Args:
            to (str): The email address of the recipient.
            subject (str): The subject line of the email.
            message_text (str): The text of the email message.
            file_path (str): The path to the file to attach.

        Returns:
            None
        """

        try:
            # Create a message object
            message = MIMEMultipart()
            message['to'] = to
            message['subject'] = subject

            # Add the email message as plain text
            message.attach(MIMEText(message_text))

            # Add the file attachment
            with open(file_path, 'rb') as file:
                attachment = MIMEImage(file.read(), _subtype=subtype)
                attachment.add_header('Content-Disposition', 'attachment', filename=os.path.basename(file_path))
                message.attach(attachment)

            # Convert the message to a raw string
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

            # Send the message
            send_message = self.service.users().messages().send(userId='me', body={'raw': raw_message}).execute()
            print(F'Sent message to {to} Message Id: {send_message["id"]}')

        except HttpError as error:
            print(F'An error occurred: {error}')
            send_message = None

        return send_message

# gmail = Gmail('./credentials.json')
# max_results = 10
# query = 'subject:'
# after_date = datetime.utcnow() - timedelta(days=3)
# # messages = gmail.get_messages(query=query, max_results=max_results, after_date=after_date)
# messages = gmail.get_email_by_max(maxResults = max_results, after_date = after_date)

# # with open('test', 'w') as f:
# #     for i in messages:
# #         f.writelines(json.dumps(i[0]) + '\n')
# #         f.writelines(json.dumps(i[1]) + '\n')
# #         f.writelines(json.dumps(i[2]) + '\n')
# print(messages[9][0] + '\n' + messages[9][1] + '\n' + messages[9][2])