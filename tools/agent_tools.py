"""
Ferramentas para o agente Valorant Helper.
Usa google_search do ADK para buscar dados em tempo real.
"""
from typing import List, Optional
from google.adk.tools import FunctionTool, google_search


# Lista de mapas ativos (isso muda pouco)
ACTIVE_MAPS = ["abyss", "ascent", "bind", "haven", "icebox", "lotus", "pearl", "split", "sunset"]

# Roles dos agentes (fixo)
AGENT_ROLES = {
    "jett": "Duelist", "reyna": "Duelist", "raze": "Duelist", "neon": "Duelist",
    "yoru": "Duelist", "phoenix": "Duelist", "iso": "Duelist", "waylay": "Duelist",
    "omen": "Controller", "viper": "Controller", "brimstone": "Controller",
    "astra": "Controller", "clove": "Controller", "harbor": "Controller",
    "sova": "Initiator", "fade": "Initiator", "gekko": "Initiator",
    "breach": "Initiator", "kayo": "Initiator", "skye": "Initiator",
    "killjoy": "Sentinel", "cypher": "Sentinel", "sage": "Sentinel",
    "chamber": "Sentinel", "deadlock": "Sentinel", "vyse": "Sentinel",
}

ALL_AGENTS = [
    "Jett", "Reyna", "Raze", "Neon", "Yoru", "Phoenix", "Iso", "Waylay",
    "Omen", "Viper", "Brimstone", "Astra", "Clove", "Harbor",
    "Sova", "Fade", "Gekko", "Breach", "KAY/O", "Skye",
    "Killjoy", "Cypher", "Sage", "Chamber", "Deadlock", "Vyse"
]


def get_agent_role(agent_name: str) -> str:
    """Retorna a role de um agente."""
    normalized = agent_name.lower().replace("/", "").replace("-", "")
    return AGENT_ROLES.get(normalized, "Unknown")


def get_all_maps() -> dict:
    """
    Retorna a lista de mapas ativos no competitivo.
    """
    return {
        "status": "ok",
        "maps": ACTIVE_MAPS,
        "total": len(ACTIVE_MAPS)
    }


def analyze_team_composition(agents: List[str]) -> dict:
    """
    Analisa uma composição de time (até 5 agentes).
    
    Args:
        agents: Lista de nomes dos agentes (ex: ["Jett", "Omen", "Sova", "Killjoy", "Sage"])
    """
    if not agents:
        return {"error": "Lista de agentes é obrigatória"}
    
    agents_normalized = [a.strip().title() for a in agents]
    
    roles = {"Duelist": 0, "Controller": 0, "Initiator": 0, "Sentinel": 0}
    agent_details = []
    
    for agent in agents_normalized:
        role = get_agent_role(agent)
        if role in roles:
            roles[role] += 1
        agent_details.append({"name": agent, "role": role})
    
    issues = []
    suggestions = []
    
    if roles["Controller"] == 0:
        issues.append("❌ Sem Controller - time sem smokes")
        suggestions.append("Adicione Omen, Clove ou Viper")
    
    if roles["Initiator"] == 0:
        issues.append("⚠️ Sem Initiator - falta informação")
        suggestions.append("Adicione Sova, Fade ou Gekko")
    
    if roles["Sentinel"] == 0:
        issues.append("⚠️ Sem Sentinel - falta defesa de site")
        suggestions.append("Adicione Killjoy, Cypher ou Sage")
    
    if roles["Duelist"] == 0:
        issues.append("⚠️ Sem Duelist - pode faltar entrada")
    
    if roles["Duelist"] >= 3:
        issues.append("⚠️ 3+ Duelistas - composição muito agressiva")
        suggestions.append("Troque um Duelista por utility")
    
    score = 10 - (len(issues) * 2)
    score = max(0, min(10, score))
    
    return {
        "status": "ok",
        "agents": agent_details,
        "role_count": roles,
        "issues": issues,
        "suggestions": suggestions,
        "composition_score": score,
        "verdict": "Boa composição!" if score >= 7 else "Composição precisa de ajustes"
    }


def get_agent_info(agent_name: str) -> dict:
    """
    Retorna a role de um agente específico.
    
    Args:
        agent_name: Nome do agente (ex: "Jett", "Omen")
    """
    if not agent_name:
        return {"error": "Nome do agente é obrigatório"}
    
    agent_normalized = agent_name.strip().title()
    role = get_agent_role(agent_normalized)
    
    if role == "Unknown":
        return {
            "status": "error",
            "error": f"Agente '{agent_name}' não encontrado",
            "available_agents": ALL_AGENTS
        }
    
    return {
        "status": "ok",
        "name": agent_normalized,
        "role": role
    }


# === Exporta ferramentas para o agente ===
# google_search é nativo do ADK - o agente vai usar para buscar tier list e meta
tools = [
    google_search,  # Busca na internet por tier list, meta, etc
    FunctionTool(get_all_maps),
    FunctionTool(analyze_team_composition),
    FunctionTool(get_agent_info),
]
