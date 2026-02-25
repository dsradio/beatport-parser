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
    
    # 1. Название трека (по классу, который ты нашёл)
    name_elem = soup.find('h1', class_='TrackHeader-style__Name-sc-95024209-2')
    if not name_elem:
        name_elem = soup.find('h1', {'data-testid': 'trackTitle'})
    
    # 2. Исполнитель (ищем по тегу a с атрибутом title)
    artist_elem = soup.find('a', {'title': True})
    # Уточняем: ищем ссылку, которая ведёт на страницу артиста
    if artist_elem:
        # Проверяем, что это действительно артист (href содержит /artist/)
        if '/artist/' not in artist_elem.get('href', ''):
            artist_elem = None
    
    # 3. Лейбл (по классу, который ты нашёл)
    label_elem = soup.find('div', class_='Marquee-style__MarqueeElement-sc-b0373cc7-0')
    if not label_elem:
        # Если не нашли по классу, ищем ссылку на лейбл
        label_elem = soup.find('a', {'data-testid': 'labelLink'})
    
    # 4. Обложка
    cover_elem = soup.find('img', {'data-testid': 'trackImage'})
    if not cover_elem:
        cover_elem = soup.find('img', class_='track-image')
    cover_url = cover_elem.get('src') if cover_elem else ''
    
    # Извлекаем текст
    name = name_elem.text.strip() if name_elem else 'Неизвестно'
    artist = artist_elem.text.strip() if artist_elem else 'Неизвестно'
    label = label_elem.text.strip() if label_elem else ''
    
    # Чистим название от лишних слов типа "Extended Mix" (они в отдельном теге span)
    if name_elem:
        # Убираем текст внутри span (обычно это Extended Mix, Original Mix и т.д.)
        span = name_elem.find('span')
        if span:
            name = name.replace(span.text, '').strip()
    
    result = {
        'name': name,
        'artist': artist,
        'label': label,
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
