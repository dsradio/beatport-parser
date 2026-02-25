from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup
import json
import os

app = Flask(__name__)

def parse_beatport_track(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
    except Exception as e:
        return {'error': str(e)}
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    script = soup.find('script', type='application/ld+json')
    if script:
        try:
            data = json.loads(script.string)
            return {
                'name': data.get('name', ''),
                'artist': data.get('byArtist', {}).get('name', '') if isinstance(data.get('byArtist'), dict) else '',
                'label': data.get('recordLabel', ''),
                'releaseDate': data.get('datePublished', ''),
                'coverUrl': data.get('image', '')
            }
        except:
            pass
    
    name = soup.find('span', {'class': 'track-name'})
    artist = soup.find('span', {'class': 'artist-name'})
    label = soup.find('a', {'data-testid': 'labelLink'})
    
    return {
        'name': name.text.strip() if name else 'Неизвестно',
        'artist': artist.text.strip() if artist else 'Неизвестно',
        'label': label.text.strip() if label else '',
        'releaseDate': '',
        'coverUrl': ''
    }

@app.route('/')
def home():
    return 'Beatport Parser API is running'

@app.route('/parse', methods=['GET'])
def parse_track():
    url = request.args.get('url')
    if not url:
        return jsonify({'error': 'Missing url parameter'}), 400
    
    track_data = parse_beatport_track(url)
    return jsonify(track_data)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
