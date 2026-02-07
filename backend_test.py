"""
Simple Flask backend for testing frontend connection.
Run with: python backend_test.py
"""

from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS for Electron app

@app.route('/api/hello', methods=['GET'])
def hello_world():
    """Simple endpoint that returns hello world."""
    return jsonify({
        'message': 'Hello World!',
        'status': 'success',
        'timestamp': '2024-02-06'
    })

@app.route('/api/generate', methods=['POST'])
def generate():
    """Test endpoint for schematic generation."""
    from flask import request
    
    data = request.get_json()
    prompt = data.get('prompt', '')
    
    return jsonify({
        'success': True,
        'message': f'Received prompt: {prompt}',
        'prompt': prompt,
        'components': [
            {
                'name': 'Test Component 1',
                'type': 'resistor',
                'value': '10k'
            },
            {
                'name': 'Test Component 2',
                'type': 'led',
                'value': 'red'
            }
        ]
    })

if __name__ == '__main__':
    print("=" * 50)
    print("Flask Test Server Starting...")
    print("=" * 50)
    print("Available endpoints:")
    print("  GET  http://localhost:5000/api/hello")
    print("  POST http://localhost:5000/api/generate")
    print("=" * 50)
    app.run(debug=True, port=5001)
