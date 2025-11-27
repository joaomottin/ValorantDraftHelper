"""
Interface Web para o Valorant Draft Helper
Permite enviar imagens e conversar com o agente
"""

import os
import base64
import asyncio
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
import google.generativeai as genai

from tools import (
    get_player_stats,
    get_map_meta,
    get_agents_meta,
    get_compositions,
    get_agent_details,
    analyze_team_composition,
    get_all_maps
)

load_dotenv()

app = Flask(__name__, static_folder='static', static_url_path='/static')
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Modelo com visão
model = genai.GenerativeModel('gemini-2.5-flash')

# Histórico da conversa
conversation_history = []

SYSTEM_PROMPT = """
Você é o **Draft Helper**. Sua ÚNICA função é ajudar no draft de Valorant.

## REGRAS ABSOLUTAS:
- NUNCA descreva imagens
- NUNCA analise conteúdo fora do draft
- NUNCA faça conversa social
- IDIOMA: PORTUGUÊS BRASILEIRO

## IMAGENS ACEITAS (responda apenas estas):

### 1. TELA DE SELEÇÃO DE AGENTES (agent select):
Se a imagem mostrar a tela onde os jogadores escolhem agentes ANTES da partida:
- Identifique o MAPA
- Identifique os AGENTES já escolhidos
- Recomende um agente

Formato:
"**[MAPA]** - Time: [AGENTES]

🎯 **[AGENTE]**
- [Motivo 1]
- [Motivo 2]

**Alt:** [Outro]"

### 2. TELA DE TAB/SCOREBOARD:
Se mostrar a tabela com nicks dos jogadores:
"Nicks: [LISTA]"

## QUALQUER OUTRA IMAGEM:
Se a imagem NÃO for tela de seleção de agentes ou tab, responda APENAS:
"Manda o print da **tela de seleção de agentes** (antes da partida começar)"

NÃO descreva o que vê na imagem. NÃO analise skins, armas, mapas durante jogo, etc.

## MENSAGENS DE TEXTO (sem imagem):
Responda APENAS: "Manda o print da tela de seleção"

## PROIBIDO:
- Dizer "oi", "olá", "tudo bem"
- Fazer conversa social
- Perguntar como o usuário está
"""


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
        # Prepara conteúdo
        content = []
        
        if image_data:
            # Remove prefixo data:image/...;base64,
            if ',' in image_data:
                image_data = image_data.split(',')[1]
            
            # Adiciona imagem
            content.append({
                "mime_type": "image/png",
                "data": image_data
            })
        
        if message:
            content.append(message)
        
        # Adiciona histórico + nova mensagem
        messages = [{"role": "user", "parts": [SYSTEM_PROMPT]}]
        for h in conversation_history[-10:]:  # Últimas 10 mensagens
            messages.append(h)
        
        if content:
            messages.append({"role": "user", "parts": content})
        
        # Gera resposta
        response = model.generate_content(content if not conversation_history else messages)
        
        assistant_message = response.text
        
        # Salva no histórico
        conversation_history.append({"role": "user", "parts": content if isinstance(content, list) else [content]})
        conversation_history.append({"role": "model", "parts": [assistant_message]})
        
        return jsonify({"response": assistant_message})
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/tool/<tool_name>', methods=['POST'])
def execute_tool(tool_name):
    """Executa uma ferramenta específica"""
    data = request.json
    
    tools = {
        'get_player_stats': get_player_stats,
        'get_map_meta': get_map_meta,
        'get_agents_meta': get_agents_meta,
        'get_compositions': get_compositions,
        'get_agent_details': get_agent_details,
        'analyze_team_composition': analyze_team_composition,
        'get_all_maps': get_all_maps
    }
    
    if tool_name not in tools:
        return jsonify({"error": f"Tool '{tool_name}' não encontrada"}), 404
    
    try:
        result = tools[tool_name](**data)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/clear', methods=['POST'])
def clear_history():
    global conversation_history
    conversation_history = []
    return jsonify({"status": "ok"})


if __name__ == '__main__':
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static', exist_ok=True)
    app.run(debug=True, port=5000, host='0.0.0.0')
