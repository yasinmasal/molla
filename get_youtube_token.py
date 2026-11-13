"""Yerel bilgisayarda OAuth izni al: pip install google-auth-oauthlib; python get_youtube_token.py client_secret.json"""
import sys
from google_auth_oauthlib.flow import InstalledAppFlow

if len(sys.argv) != 2:
    raise SystemExit('Kullanım: python get_youtube_token.py client_secret.json')
flow = InstalledAppFlow.from_client_secrets_file(sys.argv[1], scopes=['https://www.googleapis.com/auth/youtube.upload'])
creds = flow.run_local_server(port=0, access_type='offline', prompt='consent')
print('GitHub Actions secrets içine aşağıdaki değerleri ekleyin:')
print('YT_CLIENT_ID=', creds.client_id)
print('YT_CLIENT_SECRET=', creds.client_secret)
print('YT_REFRESH_TOKEN=', creds.refresh_token or 'TOKEN ALINAMADI; erişimi kaldırıp yeniden deneyin')
