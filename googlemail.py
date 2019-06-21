from __future__ import print_function
from apiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools
import csv

# Setup the Gmail API
SCOPES = 'https://www.googleapis.com/auth/gmail.readonly'
store = file.Storage('credentials.json')
creds = store.get()
if not creds or creds.invalid:
    flow = client.flow_from_clientsecrets('client_secret.json', SCOPES)
    creds = tools.run_flow(flow, store)
service = build('gmail', 'v1', http=creds.authorize(Http()))
failed_recipients = set()
all_recipients = set()

# Call the Gmail API
messages = service.users().messages()
request = messages.list(userId='me', includeSpamTrash=True)
with open('recipients.csv', 'w') as csvfile:
    fieldnames = ['all', 'failed', 'replied', 'autoreplied']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    while request is not None:
        messages_list = request.execute()
        for m in messages_list.get('messages'):
            failed = False
            replied = False
            auto_replied = False
            from_header = ''
            to_header = ''
            failed_recipient = ''
            message = messages.get(userId='me', id=m.get('id')).execute()
            payload = message.get('payload')
            headers = payload.get('headers')
            # result = filter(lambda h: h['name'] in 'X-Failed-Recipients', headers)
            for item in headers:
                if 'X-Failed-Recipients' in item['name']:
                    failed = True
                    failed_recipient = item['value']
                    break
                if 'In-Reply-To' in item['name']:
                    replied = True
                if 'X-AutoReply' in item['name'] and item['value'] in 'YES':
                    auto_replied = True
                if 'From' in item['name']:
                    from_header = item['value']
                if 'To' in item['name']:
                    to_header = item['value']

            if not replied and not failed and not auto_replied:
                writer.writerow({'all': to_header, 'failed': None, 'replied': None, 'autoreplied': None})
            elif replied:
                writer.writerow({'all': from_header, 'failed': None, 'replied': from_header, 'autoreplied': None})
            elif auto_replied:
                writer.writerow({'all': from_header, 'failed': None, 'replied': None, 'autoreplied': from_header})
            elif failed:
                writer.writerow({'all': failed_recipient, 'failed': failed_recipient, 'replied': None, 'autoreplied': from_header})

        request = messages.list_next(request, messages_list)

print(failed_recipients)

