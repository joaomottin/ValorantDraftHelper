"""
VALORANT DRAFT HELPER - Agente Principal
Usa Gemini com Google Search Grounding para buscar dados em tempo real
"""

import os
import sys
import re
import asyncio
import cloudscraper
from dotenv import load_dotenv

# Adiciona o diretório do projeto ao sys.path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

load_dotenv()

import google.generativeai as genai


# --- Função para buscar perfil no Tracker.gg via API ---
def fetch_tracker_api(riot_id: str) -> dict:
    """Busca dados do Tracker.gg API usando cloudscraper para bypass de Cloudflare."""
    scraper = cloudscraper.create_scraper(
        browser={
            'browser': 'chrome',
            'platform': 'windows',
            'desktop': True
        }
    )
    
    # Codifica o riot_id para URL
    encoded_id = riot_id.replace("#", "%23")
    url = f"https://api.tracker.gg/api/v2/valorant/standard/profile/riot/{encoded_id}"
    
    try:
        response = scraper.get(url, timeout=20)
        
        if response.status_code == 200:
            return {
                "success": True,
                "data": response.json()
            }
        elif response.status_code == 404:
            return {"success": False, "error": "Perfil não encontrado. Verifique o Nick#Tag."}
        elif response.status_code == 403:
            return {"success": False, "error": "Acesso bloqueado pelo Cloudflare."}
        else:
            return {"success": False, "error": f"Erro HTTP {response.status_code}"}
            
    except Exception as e:
        return {"success": False, "error": str(e)}


async def scrape_tracker_profile(riot_id: str) -> dict:
    """
    Busca perfil de um jogador no Tracker.gg via API.
    
    Args:
        riot_id: ID Riot no formato "Nick#Tag"
    
    Returns:
        Dict com estatísticas formatadas ou mensagem de erro
    """
    # Valida formato
    if "#" not in riot_id:
        return {"error": "Formato inválido. Use: Nick#Tag"}
    
    # Executa em thread separada para não bloquear
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, fetch_tracker_api, riot_id)
    
    if not result.get("success"):
        return {"error": result.get("error", "Erro desconhecido")}
    
    try:
        data = result["data"]["data"]
        
        # Info do perfil
        platform_info = data.get("platformInfo", {})
        user_handle = platform_info.get("platformUserHandle", riot_id)
        avatar_url = platform_info.get("avatarUrl", "")
        
        # Metadata
        metadata = data.get("metadata", {})
        region = metadata.get("activeShard", "N/A").upper()
        
        # Processa segmentos de stats
        segments = data.get("segments", [])
        
        profile = {
            "found": True,
            "name": user_handle,
            "region": region,
            "avatar": avatar_url,
        }
        
        # Extrai overview stats do segmento 'season' (season atual)
        for seg in segments:
            if seg.get("type") == "season":
                stats = seg.get("stats", {})
                
                # Rank
                rank_data = stats.get("rank", {})
                profile["rank"] = rank_data.get("metadata", {}).get("tierName", "Unranked")
                profile["rank_icon"] = rank_data.get("metadata", {}).get("iconUrl", "")
                
                # Peak Rank
                peak_data = stats.get("peakRank", {})
                profile["peak_rank"] = peak_data.get("metadata", {}).get("tierName", "N/A")
                
                # Stats principais
                profile["kd"] = stats.get("kDRatio", {}).get("displayValue", "N/A")
                profile["kda"] = stats.get("kDARatio", {}).get("displayValue", "N/A")
                profile["headshot"] = stats.get("headshotsPercentage", {}).get("displayValue", "N/A")
                profile["winrate"] = stats.get("matchesWinPct", {}).get("displayValue", "N/A")
                profile["damage_round"] = stats.get("damagePerRound", {}).get("displayValue", "N/A")
                profile["kills"] = stats.get("kills", {}).get("displayValue", "N/A")
                profile["deaths"] = stats.get("deaths", {}).get("displayValue", "N/A")
                profile["assists"] = stats.get("assists", {}).get("displayValue", "N/A")
                profile["matches"] = stats.get("matchesPlayed", {}).get("displayValue", "N/A")
                profile["wins"] = stats.get("matchesWon", {}).get("displayValue", "N/A")
                profile["time_played"] = stats.get("timePlayed", {}).get("displayValue", "N/A")
                profile["aces"] = stats.get("aces", {}).get("displayValue", "N/A")
                profile["clutches"] = stats.get("clutches", {}).get("displayValue", "N/A")
                profile["first_bloods"] = stats.get("firstBloods", {}).get("displayValue", "N/A")
                profile["kast"] = stats.get("kAST", {}).get("displayValue", "N/A")
                profile["esr"] = stats.get("esr", {}).get("displayValue", "N/A")
                profile["score_round"] = stats.get("scorePerRound", {}).get("displayValue", "N/A")
                
                # Metadata da season
                season_meta = seg.get("metadata", {})
                profile["season"] = season_meta.get("shortName", "")
                break
        
        # Extrai agentes mais jogados
        agents = []
        for seg in segments:
            if seg.get("type") == "agent":
                agent_meta = seg.get("metadata", {})
                agent_stats = seg.get("stats", {})
                
                agents.append({
                    "name": agent_meta.get("name", "Unknown"),
                    "role": agent_meta.get("role", ""),
                    "image": agent_meta.get("imageUrl", ""),
                    "hours": agent_stats.get("timePlayed", {}).get("displayValue", "0h"),
                    "matches": agent_stats.get("matchesPlayed", {}).get("displayValue", "0"),
                    "winrate": agent_stats.get("matchesWinPct", {}).get("displayValue", "N/A"),
                    "kd": agent_stats.get("kDRatio", {}).get("displayValue", "N/A"),
                    "hs": agent_stats.get("headshotsPercentage", {}).get("displayValue", "N/A"),
                })
        
        # Ordena por horas jogadas e pega top 5
        profile["top_agents"] = agents[:5]
        
        return profile
        
    except Exception as e:
        return {"error": f"Erro ao processar dados: {str(e)}"}

# Configura API
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# --- Configuração ---
MODEL_NAME = "gemini-2.5-flash"


def load_instruction(filename: str) -> str:
    """Carrega instruções de um arquivo markdown."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    filepath = os.path.join(base_dir, filename)
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return "Você é um assistente de Valorant. Responda em português."
    except Exception as e:
        return "Você é um assistente de Valorant. Responda em português."


# Carrega instrução
SYSTEM_INSTRUCTION = load_instruction("instructions.md")

# Modelo com Google Search Grounding
model = genai.GenerativeModel(
    model_name=MODEL_NAME,
    system_instruction=SYSTEM_INSTRUCTION,
)

# Histórico de chat por usuário
chat_sessions = {}


def get_chat(user_id: str):
    """Retorna ou cria uma sessão de chat para o usuário."""
    if user_id not in chat_sessions:
        chat_sessions[user_id] = model.start_chat(history=[])
    return chat_sessions[user_id]


async def process_message(user_id: str, message: str, image_data: bytes = None):
    """
    Processa uma mensagem do usuário.
    
    Args:
        user_id: ID do usuário
        message: Texto da mensagem
        image_data: Bytes da imagem (opcional)
    
    Returns:
        Resposta do agente
    """
    chat = get_chat(user_id)
    
    # Detecta se é busca EXPLÍCITA de perfil
    riot_id_match = re.search(r'([A-Za-z0-9_]+#[A-Za-z0-9_]+)', message)
    
    # Só busca perfil automaticamente se:
    # 1. A mensagem for APENAS o Nick#Tag (com espaços opcionais)
    # 2. OU tiver palavras de busca explícita como "buscar", "perfil", "stats", "estatísticas"
    is_profile_only = riot_id_match and message.strip().lower() == riot_id_match.group(1).lower()
    search_keywords = ["buscar", "perfil", "stats", "estatísticas", "estatisticas", "procurar", "ver perfil", "dados de", "info de"]
    is_explicit_search = riot_id_match and any(kw in message.lower() for kw in search_keywords)
    
    if (is_profile_only or is_explicit_search) and not image_data:
        riot_id = riot_id_match.group(1)
        
        # Busca perfil no Tracker.gg via API
        profile = await scrape_tracker_profile(riot_id)
        
        if profile.get("found"):
            # Formata resposta bonita com os dados da API
            encoded_id = riot_id.replace("#", "%23")
            
            season_info = f" ({profile.get('season')})" if profile.get('season') else ""
            
            response_text = f"""📊 **Estatísticas de {profile['name']}**{season_info}

🌍 **Região:** {profile.get('region', 'N/A')}

🏆 **Rank Atual:** {profile.get('rank', 'Unranked')}
⭐ **Peak Rank:** {profile.get('peak_rank', 'N/A')}

📈 **Performance Geral:**
• **K/D:** {profile.get('kd', 'N/A')}
• **KDA:** {profile.get('kda', 'N/A')}
• **KAST:** {profile.get('kast', 'N/A')}
• **Headshot %:** {profile.get('headshot', 'N/A')}
• **Win Rate:** {profile.get('winrate', 'N/A')}
• **Dano/Round:** {profile.get('damage_round', 'N/A')}
• **Score/Round:** {profile.get('score_round', 'N/A')}

🎯 **Estatísticas Totais:**
• **Kills:** {profile.get('kills', 'N/A')}
• **Deaths:** {profile.get('deaths', 'N/A')}
• **Assists:** {profile.get('assists', 'N/A')}
• **Partidas:** {profile.get('matches', 'N/A')} ({profile.get('wins', 'N/A')} vitórias)
• **First Bloods:** {profile.get('first_bloods', 'N/A')}
• **Aces:** {profile.get('aces', 'N/A')}
• **Clutches:** {profile.get('clutches', 'N/A')}
• **Tempo Jogado:** {profile.get('time_played', 'N/A')}"""
            
            # Adiciona agentes favoritos
            if profile.get('top_agents'):
                response_text += "\n\n🎭 **Agentes Mais Jogados:**"
                for i, agent in enumerate(profile['top_agents'][:5], 1):
                    response_text += f"\n{i}. **{agent['name']}** ({agent.get('role', '')}) - {agent['matches']} partidas | K/D: {agent['kd']} | WR: {agent['winrate']} | HS: {agent['hs']}"
            
            response_text += f"\n\n🔗 [Ver perfil completo](https://tracker.gg/valorant/profile/riot/{encoded_id}/overview)"
            
            return response_text
        
        elif profile.get("error"):
            error_msg = profile["error"]
            encoded_id = riot_id.replace("#", "%23")
            
            return f"""❌ **Erro ao buscar perfil:** {error_msg}

🔗 [Tente acessar diretamente no Tracker.gg](https://tracker.gg/valorant/profile/riot/{encoded_id}/overview)

💡 **Dica:** Verifique se o Nick#Tag está correto e se o perfil está público."""
    
    # Se tem Nick#Tag mas NÃO é busca explícita, busca dados para contexto
    player_context = ""
    if riot_id_match and not is_profile_only and not is_explicit_search:
        riot_id = riot_id_match.group(1)
        profile = await scrape_tracker_profile(riot_id)
        
        if profile.get("found"):
            # Formata contexto do jogador para o Gemini usar na análise
            top_agents = profile.get('top_agents', [])
            agents_str = ", ".join([f"{a['name']} (K/D: {a['kd']}, WR: {a['winrate']})" for a in top_agents[:3]])
            
            player_context = f"""

[CONTEXTO DO JOGADOR - USE PARA PERSONALIZAR A RECOMENDAÇÃO]
Jogador: {profile['name']}
Rank: {profile.get('rank', 'N/A')}
K/D Geral: {profile.get('kd', 'N/A')}
Win Rate: {profile.get('winrate', 'N/A')}
Agentes mais jogados: {agents_str}
[FIM DO CONTEXTO - NÃO MOSTRE ESSES DADOS BRUTOS, USE PARA DAR RECOMENDAÇÕES PERSONALIZADAS]
"""
    
    # Monta conteúdo para Gemini
    content = []
    
    if image_data:
        content.append({
            "mime_type": "image/png",
            "data": image_data
        })
    
    # Adiciona contexto do jogador se existir
    final_message = message
    if player_context:
        final_message = message + player_context
    
    if final_message:
        content.append(final_message)
    
    if not content:
        return "Envie uma mensagem ou imagem."
    
    try:
        # Envia com grounding habilitado
        response = chat.send_message(
            content,
            tools=[{"google_search": {}}],  # Habilita busca na web
        )
        return response.text
    except Exception as e:
        # Tenta sem grounding se falhar
        try:
            response = chat.send_message(content)
            return response.text
        except Exception as e2:
            return f"Erro: {str(e2)}"


# --- Execução CLI ---
if __name__ == '__main__':
    import asyncio
    
    print("=" * 50)
    print("🎮 VALORANT DRAFT HELPER")
    print("=" * 50)
    print("Digite 'sair' para terminar.\n")
    
    async def main():
        while True:
            try:
                user_input = input("\n👤 Você: ")
                if user_input.lower() in ['sair', 'exit', 'quit']:
                    print("\n👋 Até a próxima! GG!")
                    break
                
                if not user_input.strip():
                    continue
                
                print("\n🔄 Buscando...")
                
                response = await process_message(
                    user_id="cli_user",
                    message=user_input
                )
                print(f"\n🎮 Helper: {response}")
                
            except KeyboardInterrupt:
                print("\n\n👋 Até a próxima!")
                break
            except Exception as e:
                print(f"\n❌ Erro: {e}")
                continue
    
    asyncio.run(main())

