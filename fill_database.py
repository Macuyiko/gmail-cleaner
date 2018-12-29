import httplib2
import os

from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage

from model import *
from tqdm import tqdm
from joblib import Parallel, delayed
from collections import defaultdict
import multiprocessing

# If modifying these scopes, delete previously saved credentials at
# ~/.credentials/gmail-python-quickstart.json
SCOPES = 'https://www.googleapis.com/auth/gmail.modify'
CREDENTIALS_FILE = 'gmail-python-quickstart.json'
# Download this file from the Google API console:
CLIENT_SECRET_FILE = 'client_secret_799876907855-a38rjtvpcslb6g7lh6libe18m4vo8gch.apps.googleusercontent.com.json'
APPLICATION_NAME = 'Gmail API Python Quickstart'
DATABASE = EmailDB(os.path.dirname(os.path.realpath(__file__)) + '/emails.db')


def ParallelExecutor(use_bar='tqdm', **joblib_args):
    def aprun(bar=use_bar, **tq_args):
        bar_func = lambda x: tqdm(x, **tq_args)
        def tmp(op_iter):
            return Parallel(**joblib_args)(bar_func(op_iter))
        return tmp
    return aprun


def get_credentials():
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir, CREDENTIALS_FILE)
    store = Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        credentials = tools.run_flow(flow, store, None)
        print('Storing credentials to ' + credential_path)
    return credentials


def get_service():
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('gmail', 'v1', http=http)
    return service


def fill_db():
    service = get_service()
    token = None
    DATABASE.clear_emails()
    while True:
        results = service.users().messages().list(userId='me', pageToken=token).execute()
        messages = results.get('messages', [])
        DATABASE.insert_emails([(message['id'],) for message in messages])
        token = results.get('nextPageToken')
        if not token:
            break


def fetch_headers(id):
    service = get_service()
    get_header = lambda x, name: [y for y in x if y.get('name') == name][0]['value']
    result = service.users().messages().get(userId='me', id=id).execute()
    try:
        fromf   = get_header(result['payload']['headers'], 'From')
        subject = get_header(result['payload']['headers'], 'Subject')
        return (id, fromf, subject)
    except:
        return (id, None, None)


def update_headers(chunks):
    num_cores = 2
    aprun = ParallelExecutor(n_jobs=num_cores)
    results = aprun(bar='tqdm')(delayed(fetch_headers)(id) for id in chunks)
    for id, fromf, subject in tqdm(results):
        if subject is None or fromf is None:
            DATABASE.trash_email(id)
        else:
            DATABASE.update_email(id, fromf, subject)


def update_db():
    chunk_size = 300
    chunks = []
    for email in tqdm(DATABASE.select_updateable_emails()):
        chunks.append(email['id'])
        if len(chunks) >= chunk_size:
            update_headers(chunks)
            chunks = []
    update_headers(chunks)


def main():
    if not DATABASE.has_emails():
        print('Database is empty, performing first-time setup')
        fill_db()

    print('Updating messages')
    update_db()


if __name__ == '__main__':
    main()