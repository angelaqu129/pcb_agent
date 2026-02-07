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
    """Generate schematic using PCB Agent Stage 0 (Component Filtering)."""
    from flask import request
    import asyncio
    import sys
    import os
    
    # Add parent directory to path for imports
    sys.path.insert(0, os.path.dirname(__file__))
    
    data = request.get_json()
    prompt = data.get('prompt', '')
    
    if not prompt:
        return jsonify({
            'success': False,
            'error': 'No prompt provided'
        }), 400
    
    try:
        # Import PCBAgent
        from pcb_agent import PCBAgent
        
        # Run Stage 0 asynchronously
        async def run_stage0():
            agent = PCBAgent(verbose=True)
            filtered_components = await agent._stage0_filter_components(prompt)
            return filtered_components
        
        # Execute async function
        filtered_components = asyncio.run(run_stage0())
        
        return jsonify({
            'success': True,
            'message': f'Filtered components for: {prompt}',
            'prompt': prompt,
            'components': filtered_components,
            'count': len(filtered_components)
        })
        
    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500

if __name__ == '__main__':
    print("=" * 50)
    print("Flask Test Server Starting...")
    print("=" * 50)
    print("Available endpoints:")
    print("  GET  http://localhost:5000/api/hello")
    print("  POST http://localhost:5000/api/generate")
    print("=" * 50)
    app.run(debug=True, port=5001)
