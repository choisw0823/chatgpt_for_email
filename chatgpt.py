#import openai_secret_manager
import openai
from Email import Gmail
import time
from datetime import datetime, timedelta

# Load the API key for ChatGPT
#secrets = openai_secret_manager.get_secret("openai")
# openai.api_key = secrets["api_key"]
openai.api_key = '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'
# Define a function to generate a reply message using ChatGPT
def generate_reply(message_text):
    prompt = f"Reply to this email:\n{message_text}\n\nResponse:"
    response = openai.Completion.create(
        engine="davinci", prompt=prompt, max_tokens=1024, n=1, stop=None, temperature=0.5,
    )
    return response.choices[0].text.strip()

# Initialize a Gmail client object
gmail_client = Gmail('./credentials.json')

# Retrieve the list of messages received in the past 24 hours
max_results = 10
query = 'subject:'
after_date = datetime.utcnow() - timedelta(days=3)
messages = gmail_client.get_email_by_max(maxResults = max_results, after_date = after_date)

# Loop over the messages and generate a reply for each one
for message in messages:
    # Get the sender and subject of the message
    sender = message[2]
    subject = message[0]

    # Get the message text and generate a reply using ChatGPT
    message_text = message[1]
    reply_text = generate_reply(message_text)

    # Send the reply back to the sender
    #gmail_client.send_email(sender, subject, reply_text)
    print(reply_text)
    # Wait for a few seconds to avoid rate limiting
    time.sleep(5)