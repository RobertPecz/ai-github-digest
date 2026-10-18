"""Run on a trusted local machine only. Never commit OAuth files or paste tokens in chat."""
from pathlib import Path
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ['https://www.googleapis.com/auth/gmail.send']


def main():
    path = Path('credentials.json')
    if not path.exists():
        raise SystemExit('Download Google OAuth Desktop client JSON as credentials.json first.')
    flow = InstalledAppFlow.from_client_secrets_file(str(path), SCOPES)
    creds = flow.run_local_server(port=0, access_type='offline', prompt='consent')
    if not creds.refresh_token:
        raise SystemExit('No refresh token returned. Revoke existing app access, then retry with consent.')
    print('\nOAuth succeeded. Copy these values directly into GitHub Actions secrets (NOT into chat):')
    print('GMAIL_CLIENT_ID =', creds.client_id)
    print('GMAIL_CLIENT_SECRET =', creds.client_secret)
    print('GMAIL_REFRESH_TOKEN =', creds.refresh_token)
    print('\nDelete local credentials.json if it is no longer needed; never commit it.')


if __name__ == '__main__':
    main()
