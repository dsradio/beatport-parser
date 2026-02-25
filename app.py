from flask import Flask, request, jsonify
from flask_cors import CORS  # Добавляем CORS
import requests
from bs4 import BeautifulSoup
import json
import os
import re

app = Flask(__name__)
CORS(app)  # Разрешаем запросы с любых доменов

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
    
    # Название трека
    name_elem = soup.find('h1', class_='TrackHeader-style__Name-sc-95024209-2')
    if not name_elem:
        name_elem = soup.find('h1', {'data-testid': 'trackTitle'})
    
    # Исполнитель
    artist_elem = soup.find('a', {'title': True})
    if artist_elem and '/artist/' not in artist_elem.get('href', ''):
        artist_elem = None
    
    # Лейбл
    label_elem = soup.find('div', class_='Marquee-style__MarqueeElement-sc-b0373cc7-0')
    if not label_elem:
        label_elem = soup.find('a', {'data-testid': 'labelLink'})
    
    # Обложка
    cover_elem = soup.find('img', {'data-testid': 'trackImage'})
    if not cover_elem:
        cover_elem = soup.find('img', class_='track-image')
    cover_url = cover_elem.get('src') if cover_elem else ''
    
    # Жанр
    genre_elem = soup.find('a', {'title': True, 'href': re.compile(r'/genre/')})
    genre = genre_elem.text.strip() if genre_elem else ''
    
    # Длительность
    duration = ''
    for span in soup.find_all('span'):
        text = span.text.strip()
        if re.match(r'^\d+:\d{2}$', text):
            duration = text
            break
    
    # Дата релиза
    release_date = ''
    for span in soup.find_all('span'):
        text = span.text.strip()
        if re.match(r'^\d{4}$', text) or re.match(r'^\d{4}-\d{2}-\d{2}$', text):
            release_date = text
            break
    
    # BPM
    bpm = ''
    for span in soup.find_all('span'):
        text = span.text.strip()
        if text.isdigit() and 60 <= int(text) <= 200:
            bpm = text
            break
    
    name = name_elem.text.strip() if name_elem else 'Неизвестно'
    artist = artist_elem.text.strip() if artist_elem else 'Неизвестно'
    label = label_elem.text.strip() if label_elem else ''
    
    if name_elem:
        span = name_elem.find('span')
        if span:
            name = name.replace(span.text, '').strip()
    
    return {
        'name': name,
        'artist': artist,
        'label': label,
        'genre': genre,
        'duration': duration,
        'releaseDate': release_date,
        'bpm': bpm,
        'coverUrl': cover_url
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
