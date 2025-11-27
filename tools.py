"""
Tools para o Agente - TUDO buscado em tempo real do Tracker.gg
"""

from typing import Dict, Any, List

# Import que funciona tanto com ADK quanto com Flask
try:
    from ValorantHelper.scraper import TrackerScraper, PLAYWRIGHT_OK
except ImportError:
    from scraper import TrackerScraper, PLAYWRIGHT_OK


def get_player_stats(nickname: str, tag: str = None) -> Dict[str, Any]:
    """
    Busca stats do jogador no Tracker.gg em tempo real.
    
    Args:
        nickname: Nick do jogador (ex: "Player" ou "Player#BR1")
        tag: Tag opcional (ex: "BR1")
    
    Returns:
        Dict com rank, top_agents, winrates ou erro.
    """
    # Parse nick#tag
    if tag is None and "#" in nickname:
        parts = nickname.split("#")
        nickname, tag = parts[0], parts[1] if len(parts) > 1 else "BR1"
    tag = (tag or "BR1").replace("#", "")
    
    print(f"🔍 Buscando stats de {nickname}#{tag}...")
    
    if not PLAYWRIGHT_OK:
        return {"status": "error", "error": "Playwright não instalado", "player": f"{nickname}#{tag}"}
    
    with TrackerScraper(headless=False) as scraper:
        result = scraper.get_player_stats(nickname, tag)
    
    if result.get('status') == 'success':
        print(f"✅ {result['rank']} - {len(result.get('top_agents', []))} agentes")
    else:
        print(f"❌ {result.get('error')}")
    
    return result


def get_map_meta(map_name: str) -> Dict[str, Any]:
    """
    Busca meta/tier list de agentes para um mapa específico via Tracker.gg Insights.
    URL: https://tracker.gg/valorant/insights/agents?playlist=competitive&map={map}
    
    Args:
        map_name: Nome do mapa (ex: "ascent", "bind", "haven", "abyss", "lotus", "split", "sunset", "icebox", "pearl")
    
    Returns:
        Dict com all_agents (com tier, pick_rate, win_rate), tiers (S/A/B/C)
    """
    print(f"🗺️ Buscando meta de {map_name} via Insights...")
    
    if not PLAYWRIGHT_OK:
        return {"status": "error", "error": "Playwright não instalado"}
    
    with TrackerScraper(headless=False) as scraper:
        result = scraper.get_agents_meta(map_name)
    
    if result.get('status') == 'success':
        print(f"✅ {map_name.capitalize()} - {len(result.get('all_agents', []))} agentes")
    else:
        print(f"❌ {result.get('error')}")
    
    return result


def get_agents_meta() -> Dict[str, Any]:
    """
    Busca tier list de TODOS os agentes do meta atual (todos os mapas) via Tracker.gg Insights.
    URL: https://tracker.gg/valorant/insights/agents
    
    Returns:
        Dict com all_agents (com tier, pick_rate, win_rate, role), tiers (S/A/B/C)
    """
    print("🎮 Buscando tier list de agentes via Insights...")
    
    if not PLAYWRIGHT_OK:
        return {"status": "error", "error": "Playwright não instalado"}
    
    with TrackerScraper(headless=False) as scraper:
        result = scraper.get_agents_meta(None)  # None = todos os mapas
    
    if result.get('status') == 'success':
        print(f"✅ {len(result.get('all_agents', []))} agentes encontrados")
    else:
        print(f"❌ {result.get('error')}")
    
    return result


def get_compositions(map_name: str) -> Dict[str, Any]:
    """
    Busca composições populares/recomendadas para um mapa.
    Retorna as melhores comps com winrates.
    
    Args:
        map_name: Nome do mapa (ex: "ascent", "bind")
    
    Returns:
        Dict com compositions, best_comp
    """
    print(f"👥 Buscando composições para {map_name}...")
    
    if not PLAYWRIGHT_OK:
        return {"status": "error", "error": "Playwright não instalado"}
    
    with TrackerScraper(headless=False) as scraper:
        result = scraper.get_compositions(map_name)
    
    if result.get('status') == 'success':
        print(f"✅ {len(result.get('compositions', []))} composições encontradas")
    else:
        print(f"❌ {result.get('error')}")
    
    return result


def get_agent_details(agent_name: str) -> Dict[str, Any]:
    """
    Busca detalhes de um agente específico.
    Retorna role, winrate, pickrate e melhores mapas.
    
    Args:
        agent_name: Nome do agente (ex: "jett", "omen")
    
    Returns:
        Dict com role, pick_rate, win_rate, best_maps
    """
    print(f"🔎 Buscando detalhes de {agent_name}...")
    
    if not PLAYWRIGHT_OK:
        return {"status": "error", "error": "Playwright não instalado"}
    
    with TrackerScraper(headless=False) as scraper:
        result = scraper.get_agent_details(agent_name)
    
    if result.get('status') == 'success':
        print(f"✅ {agent_name.capitalize()} - {result.get('role')}")
    else:
        print(f"❌ {result.get('error')}")
    
    return result


def analyze_team_composition(agents: List[str]) -> Dict[str, Any]:
    """
    Analisa composição do time e identifica o que falta.
    
    Args:
        agents: Lista de agentes já escolhidos pelo time
    
    Returns:
        Dict com roles preenchidas, faltando e dicas
    """
    # Roles são fixas (não mudam no tracker)
    roles = {
        "Duelist": ["jett", "reyna", "raze", "neon", "yoru", "phoenix", "iso"],
        "Controller": ["omen", "viper", "brimstone", "astra", "clove", "harbor"],
        "Initiator": ["sova", "fade", "gekko", "breach", "kay/o", "kayo", "skye"],
        "Sentinel": ["killjoy", "cypher", "sage", "chamber", "deadlock", "vyse"]
    }
    
    agent_role = {}
    for role, agent_list in roles.items():
        for a in agent_list:
            agent_role[a] = role
    
    filled = {}
    for a in agents:
        r = agent_role.get(a.lower(), "Unknown")
        if r not in filled:
            filled[r] = []
        filled[r].append(a)
    
    missing = [r for r in roles if r not in filled]
    
    tips = []
    if "Controller" in missing:
        tips.append("⚠️ SEM SMOKE! Precisa de Omen, Viper, Clove ou Astra")
    if "Sentinel" in missing:
        tips.append("⚠️ SEM SENTINEL! Precisa de Killjoy, Cypher ou Sage")
    if "Initiator" in missing:
        tips.append("⚠️ SEM INFO! Precisa de Sova, Fade, Gekko ou Skye")
    if len(filled.get("Duelist", [])) >= 2:
        tips.append("⚡ 2 duelists = jogue agressivo, busque entry")
    if len(filled.get("Duelist", [])) == 0:
        tips.append("⚠️ SEM DUELIST! Precisa de Jett, Reyna ou Raze")
    
    return {
        "agents": agents,
        "filled_roles": filled,
        "missing_roles": missing,
        "tips": tips
    }


def get_all_maps() -> Dict[str, Any]:
    """
    Busca lista de todos os mapas disponíveis.
    
    Returns:
        Dict com lista de mapas
    """
    print("🗺️ Buscando lista de mapas...")
    
    if not PLAYWRIGHT_OK:
        return {"status": "error", "error": "Playwright não instalado"}
    
    with TrackerScraper(headless=False) as scraper:
        result = scraper.get_map_meta(None)  # None = busca todos
    
    if result.get('status') == 'success':
        print(f"✅ {len(result.get('maps', []))} mapas encontrados")
    else:
        print(f"❌ {result.get('error')}")
    
    return result
