from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
import json
import os
import re

app = Flask(__name__)
CORS(app)

def parse_beatport_track(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
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
    
    # === НАЗВАНИЕ ТРЕКА ===
    name_elem = soup.find('h1', class_='TrackHeader-style__Name-sc-95024209-2')
    if not name_elem:
        name_elem = soup.find('h1', {'data-testid': 'trackTitle'})
    
    if name_elem:
        name = name_elem.get_text(separator=' ', strip=True)
    else:
        name = 'Неизвестно'
    
    # === ИСПОЛНИТЕЛЬ ===
    artist_elem = soup.find('a', {'title': True})
    if artist_elem and '/artist/' not in artist_elem.get('href', ''):
        artist_elem = None
    artist = artist_elem.text.strip() if artist_elem else 'Неизвестно'
    
    # === ЛЕЙБЛ ===
    label_elem = soup.find('div', class_='Marquee-style__MarqueeElement-sc-b0373cc7-0')
    if not label_elem:
        label_elem = soup.find('a', {'data-testid': 'labelLink'})
    label = label_elem.text.strip() if label_elem else ''
    
    # === ОБЛОЖКА ===
    cover_elem = soup.find('img', {'data-testid': 'trackImage'})
    if not cover_elem:
        cover_elem = soup.find('img', class_='track-image')
    cover_url = cover_elem.get('src') if cover_elem else ''
    
    # === ЖАНР ===
    genre_elem = soup.find('a', {'title': True, 'href': re.compile(r'/genre/')})
    genre = genre_elem.text.strip() if genre_elem else ''
    
    # === ДЛИТЕЛЬНОСТЬ ===
    duration = ''
    length_container = soup.find(lambda tag: tag.name == 'div' and 'Length:' in tag.text)
    if length_container:
        meta_item = length_container.parent
        if meta_item:
            span = meta_item.find('span')
            if span:
                duration = span.text.strip()
    
    # === ДАТА РЕЛИЗА ===
    release_date = ''
    released_container = soup.find(lambda tag: tag.name == 'div' and 'Released:' in tag.text)
    if released_container:
        meta_item = released_container.parent
        if meta_item:
            span = meta_item.find('span')
            if span:
                release_date = span.text.strip()
    
    # === BPM (ИСПРАВЛЕНО) ===
    bpm = ''
    bpm_container = soup.find(lambda tag: tag.name == 'div' and 'BPM:' in tag.text)
    if bpm_container:
        meta_item = bpm_container.parent
        if meta_item:
            bpm_span = meta_item.find('span')
            if bpm_span:
                bpm = bpm_span.text.strip()
    
    # === ID ТРЕКА ===
    track_id = url.rstrip('/').split('/')[-1]
    
    # === EMBED-КОД ПЛЕЕРА ===
    embed_code = f'<iframe src="https://embed.beatport.com/?id={track_id}&type=track" width="100%" height="162" frameborder="0" scrolling="no" style="max-width:600px;"></iframe>'
    
    result = {
        'name': name,
        'artist': artist,
        'label': label,
        'genre': genre,
        'duration': duration,
        'releaseDate': release_date,
        'bpm': bpm,
        'coverUrl': cover_url,
        'embedCode': embed_code,
        'trackId': track_id
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
