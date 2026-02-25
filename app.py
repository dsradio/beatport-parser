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
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    
    try:
        print(f"Fetching URL: {url}")
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        print(f"Response status: {response.status_code}")
    except Exception as e:
        print(f"Error fetching URL: {e}")
        return {'error': str(e)}
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Пробуем найти данные в JSON-LD (структурированные данные)
    script = soup.find('script', type='application/ld+json')
    if script:
        try:
            data = json.loads(script.string)
            print("Found JSON-LD data")
            return {
                'name': data.get('name', ''),
                'artist': data.get('byArtist', {}).get('name', '') if isinstance(data.get('byArtist'), dict) else '',
                'label': data.get('recordLabel', ''),
                'releaseDate': data.get('datePublished', ''),
                'coverUrl': data.get('image', '')
            }
        except Exception as e:
            print(f"Error parsing JSON-LD: {e}")
    
    # Ручной парсинг на основе текущей структуры Beatport
    # Название трека
    name_elem = soup.find('h1', {'class': 'styles__Title-sc-1shp3s8-2'})
    if not name_elem:
        name_elem = soup.find('h1', {'data-testid': 'trackTitle'})
    if not name_elem:
        name_elem = soup.find('span', {'class': 'track-name'})
    
    # Исполнитель
    artist_elem = soup.find('a', {'class': 'styles__ArtistLink-sc-1shp3s8-3'})
    if not artist_elem:
        artist_elem = soup.find('a', {'data-testid': 'artistLink'})
    if not artist_elem:
        artist_elem = soup.find('span', {'class': 'artist-name'})
    
    # Лейбл
    label_elem = soup.find('a', {'data-testid': 'labelLink'})
    if not label_elem:
        label_elem = soup.find('a', {'class': 'label-link'})
    
    # Обложка
    cover_elem = soup.find('img', {'data-testid': 'trackImage'})
    if not cover_elem:
        cover_elem = soup.find('img', {'class': 'track-image'})
    cover_url = cover_elem.get('src') if cover_elem else ''
    
    result = {
        'name': name_elem.text.strip() if name_elem else 'Неизвестно',
        'artist': artist_elem.text.strip() if artist_elem else 'Неизвестно',
        'label': label_elem.text.strip() if label_elem else '',
        'releaseDate': '',
        'coverUrl': cover_url
    }
    
    print(f"Parsed result: {result}")
    return result

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
