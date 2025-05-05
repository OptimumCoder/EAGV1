from flask import Flask, request, jsonify
from flask_cors import CORS
from markitdown import MarkItDown
from bs4 import BeautifulSoup

app = Flask(__name__)
CORS(app)
storage = {}  # {url: text}


@app.route('/extract', methods=['POST'])
def extract():
    data = request.json
    html_content = data['html']
    # Convert HTML to readable plain-text
    soup = BeautifulSoup(html_content, features='html.parser')
    storage[data['url']] = soup.get_text(separator="\n")
    return jsonify({"status": "ok"})

@app.route('/search', methods=['POST'])
def search():
    query = request.json['query'].lower()
    results = [url for url, text in storage.items() if query in text.lower()]
    print(f'results: {results}')
    return jsonify({"urls": results})

if __name__ == '__main__':
    app.run(port=5000)