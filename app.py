"""
Interface Web para o Valorant Draft Helper
"""
import os
import asyncio
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv

load_dotenv()

# Adiciona o diretório ao path
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent import process_message

app = Flask(__name__, static_folder='static', static_url_path='/static')

# Histórico da conversa
conversation_history = []


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/chat', methods=['POST'])
def chat():
    global conversation_history
    
    data = request.json
    message = data.get('message', '')
    image_data = data.get('image', None)
    
    try:
        # Processa imagem se existir
        image_bytes = None
        if image_data:
            import base64
            # Remove prefixo data:image/...;base64,
            if ',' in image_data:
                image_data = image_data.split(',')[1]
            image_bytes = base64.b64decode(image_data)
        
        # Executa agente
        response_text = asyncio.run(process_message(
            user_id="web_user",
            message=message,
            image_data=image_bytes
        ))
        
        # Salva no histórico
        conversation_history.append({"role": "user", "message": message})
        conversation_history.append({"role": "assistant", "message": response_text})
        
        return jsonify({"response": response_text})
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route('/clear', methods=['POST'])
def clear_history():
    global conversation_history
    conversation_history = []
    return jsonify({"status": "ok"})


@app.route('/tool/<tool_name>', methods=['POST'])
def execute_tool(tool_name):
    """Executa uma ferramenta específica via API"""
    from tools.agent_tools import (
        get_all_maps,
        analyze_team_composition,
        get_agent_info,
    )
    
    data = request.json or {}
    
    tools_map = {
        'get_all_maps': lambda: get_all_maps(),
        'analyze_team_composition': lambda: analyze_team_composition(data.get('agents', [])),
        'get_agent_info': lambda: get_agent_info(data.get('agent_name', '')),
    }
    
    if tool_name not in tools_map:
        return jsonify({"error": f"Ferramenta '{tool_name}' não encontrada. Use o chat para tier list e meta."}), 404
    
    try:
        result = tools_map[tool_name]()
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static', exist_ok=True)
    app.run(debug=True, port=5000, host='0.0.0.0')
