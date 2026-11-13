"""YouTube Data API ile gizli yükleme. Gerekli OAuth secret'ları README'de."""
import json
import os
from pathlib import Path
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload


def main():
    names = ['YT_CLIENT_ID', 'YT_CLIENT_SECRET', 'YT_REFRESH_TOKEN']
    missing = [n for n in names if not os.environ.get(n)]
    if missing:
        raise SystemExit('YouTube secret eksik: ' + ', '.join(missing))
    plan = json.loads(Path('output/plan.json').read_text(encoding='utf-8'))
    sources = json.loads(Path('output/sources.json').read_text(encoding='utf-8'))
    credentials = Credentials(token=None, refresh_token=os.environ['YT_REFRESH_TOKEN'],
        client_id=os.environ['YT_CLIENT_ID'], client_secret=os.environ['YT_CLIENT_SECRET'],
        token_uri='https://oauth2.googleapis.com/token',
        scopes=['https://www.googleapis.com/auth/youtube.upload'])
    youtube = build('youtube', 'v3', credentials=credentials, cache_discovery=False)
    links = '\n'.join(f"{x['title']}: {x['url']}" for x in sources)
    description = (plan['description'] + '\n\nKaynaklar:\n' + links + '\n\n#Shorts')[:5000]
    body = {'snippet': {'title': (plan['title'][:90] + ' #Shorts')[:100],
             'description': description, 'categoryId': '27', 'defaultLanguage': 'tr'},
            'status': {'privacyStatus': 'private', 'selfDeclaredMadeForKids': False}}
    request = youtube.videos().insert(part='snippet,status', body=body,
        media_body=MediaFileUpload('output/shorts.mp4', mimetype='video/mp4', resumable=True))
    result = None
    while result is None:
        status, result = request.next_chunk()
        if status:
            print(f'Yükleme: %{status.progress()*100:.0f}')
    vid = result['id']
    Path('output/receipt.json').write_text(json.dumps({'id': vid, 'url': f'https://youtube.com/shorts/{vid}',
        'privacy': result.get('status', {}).get('privacyStatus', 'private')}, ensure_ascii=False, indent=2), encoding='utf-8')
    path = Path('history.json')
    history = json.loads(path.read_text(encoding='utf-8')) if path.exists() else []
    history.append(plan['title'])
    path.write_text(json.dumps(history[-100:], ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print('YouTube yüklemesi tamamlandı:', vid)

if __name__ == '__main__':
    main()
