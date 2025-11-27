"""
Web Scraper para Tracker.gg usando Playwright
Busca TODAS as informações em tempo real: players, mapas, agentes, comps
"""

import os
import re
import tempfile
import shutil
from typing import Dict, Any, List

try:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
    PLAYWRIGHT_OK = True
except ImportError:
    PLAYWRIGHT_OK = False


class TrackerScraper:
    """Scraper para Tracker.gg com Chrome real."""
    
    BASE_URL = "https://tracker.gg/valorant"
    
    def __init__(self, headless=False):
        self.headless = headless
        self.playwright = None
        self.context = None
        self.browser = None
        self._temp_dir = None
    
    def __enter__(self):
        if not PLAYWRIGHT_OK:
            raise ImportError("Instale: pip install playwright && playwright install chromium")
        
        self.playwright = sync_playwright().start()
        
        # Tenta usar Chrome com cookies do usuário
        user_data = os.path.expanduser(r"~\AppData\Local\Google\Chrome\User Data")
        self._temp_dir = tempfile.mkdtemp(prefix="valorant_")
        
        try:
            # Copia cookies
            src = os.path.join(user_data, "Default")
            dst = os.path.join(self._temp_dir, "Default")
            os.makedirs(dst, exist_ok=True)
            for f in ["Cookies", "Preferences"]:
                if os.path.exists(os.path.join(src, f)):
                    try:
                        shutil.copy2(os.path.join(src, f), os.path.join(dst, f))
                    except:
                        pass
            
            self.context = self.playwright.chromium.launch_persistent_context(
                self._temp_dir,
                headless=self.headless,
                channel='chrome',
                args=['--disable-blink-features=AutomationControlled'],
                viewport={'width': 1920, 'height': 1080}
            )
        except:
            self.browser = self.playwright.chromium.launch(headless=self.headless)
            self.context = self.browser.new_context(viewport={'width': 1920, 'height': 1080})
        
        return self
    
    def __exit__(self, *args):
        if self.context: self.context.close()
        if self.browser: self.browser.close()
        if self.playwright: self.playwright.stop()
        if self._temp_dir and os.path.exists(self._temp_dir):
            try: shutil.rmtree(self._temp_dir)
            except: pass
    
    def _new_page(self):
        """Cria nova página."""
        return self.context.new_page()
    
    def get_player_stats(self, nick: str, tag: str) -> Dict[str, Any]:
        """Busca stats do jogador no Tracker.gg"""
        url = f"{self.BASE_URL}/profile/riot/{nick}%23{tag}/overview"
        
        try:
            page = self._new_page()
            page.goto(url, wait_until='networkidle', timeout=60000)
            
            try:
                page.wait_for_selector('.st-content__item', timeout=15000)
            except:
                page.wait_for_timeout(5000)
            
            text = page.inner_text('body').lower()
            
            if "not found" in text or "we couldn't find" in text:
                page.close()
                return {"status": "error", "error": "Perfil não encontrado", "player": f"{nick}#{tag}"}
            
            if "private" in text:
                page.close()
                return {"status": "error", "error": "Perfil privado", "player": f"{nick}#{tag}"}
            
            # Rank
            rank = "Unranked"
            for r in ["radiant", "immortal", "ascendant", "diamond", "platinum", "gold", "silver", "bronze", "iron"]:
                if r in text:
                    m = re.search(rf"{r}\s*(\d)?", text)
                    rank = f"{r.capitalize()} {m.group(1) or ''}".strip() if m else r.capitalize()
                    break
            
            # Top Agents
            agents = []
            rows = page.query_selector_all('.st-content__item')
            for row in rows[:5]:
                try:
                    name_el = row.query_selector('.st__item--sticky .info .value')
                    vals = row.query_selector_all('.st-content__item-value .info .value')
                    if name_el:
                        agents.append({
                            "name": name_el.inner_text().strip(),
                            "matches": int(vals[1].inner_text()) if len(vals) > 1 else 0,
                            "winrate": float(vals[2].inner_text().replace('%','')) if len(vals) > 2 else 0,
                            "kd": float(vals[3].inner_text()) if len(vals) > 3 else 0
                        })
                except:
                    continue
            
            page.close()
            
            return {
                "status": "success",
                "player": f"{nick}#{tag}",
                "rank": rank,
                "top_agents": agents if agents else [{"name": "Sem dados", "matches": 0, "winrate": 0, "kd": 0}],
                "url": url
            }
            
        except Exception as e:
            return {"status": "error", "error": str(e), "player": f"{nick}#{tag}"}
    
    def get_agents_meta(self, map_name: str = None) -> Dict[str, Any]:
        """
        Busca tier list de agentes via Insights do Tracker.gg.
        URL: https://tracker.gg/valorant/insights/agents
        URL com mapa: https://tracker.gg/valorant/insights/agents?playlist=competitive&map={map}
        """
        if map_name:
            url = f"{self.BASE_URL}/insights/agents?playlist=competitive&map={map_name.lower()}"
        else:
            url = f"{self.BASE_URL}/insights/agents"
        
        try:
            page = self._new_page()
            page.goto(url, wait_until='networkidle', timeout=60000)
            
            try:
                page.wait_for_selector('a[href*="/db/agents/"]', timeout=15000)
            except:
                page.wait_for_timeout(5000)
            
            agents = []
            tiers = {"S": [], "A": [], "B": [], "C": [], "D": [], "F": []}
            current_tier = "S"
            
            # Busca links de agentes que contém stats
            agent_links = page.query_selector_all('a[href*="/db/agents/"]')
            
            for link in agent_links:
                try:
                    text = link.inner_text().strip()
                    if not text:
                        continue
                    
                    # Formato: "Clove S Clove Controller 10.0% 52.3% 10.7% 0.95 -7.3"
                    # Ou: "Tier S" antes do agente
                    
                    # Detecta tier
                    for tier in ["S", "A", "B", "C", "D", "F"]:
                        if f" {tier} " in text or text.startswith(f"{tier} "):
                            current_tier = tier
                            break
                    
                    # Extrai dados do agente
                    parts = text.split()
                    if len(parts) >= 5:
                        # Encontra nome do agente (primeira palavra com mais de 1 char que não seja tier)
                        agent_name = None
                        role = None
                        stats = []
                        
                        for i, part in enumerate(parts):
                            if part in ["S", "A", "B", "C", "D", "F"] and len(part) == 1:
                                continue
                            if part in ["Duelist", "Controller", "Initiator", "Sentinel"]:
                                role = part
                                continue
                            if "%" in part or self._is_number(part):
                                stats.append(part)
                                continue
                            if agent_name is None and len(part) > 1:
                                agent_name = part
                        
                        if agent_name and len(stats) >= 2:
                            pick_rate = self._parse_percent(stats[0]) if len(stats) > 0 else 0
                            win_rate = self._parse_percent(stats[1]) if len(stats) > 1 else 0
                            kd = self._parse_float(stats[3]) if len(stats) > 3 else 0
                            
                            agent_data = {
                                "name": agent_name,
                                "role": role or self._get_agent_role(agent_name),
                                "tier": current_tier,
                                "pick_rate": pick_rate,
                                "win_rate": win_rate,
                                "kd": kd
                            }
                            
                            # Evita duplicados
                            if not any(a['name'].lower() == agent_name.lower() for a in agents):
                                agents.append(agent_data)
                                tiers[current_tier].append(agent_name)
                
                except Exception as e:
                    continue
            
            # Fallback: tenta regex no texto
            if not agents:
                text = page.inner_text('body')
                agents = self._parse_insights_text(text)
                for a in agents:
                    tier = a.get('tier', 'C')
                    if tier in tiers:
                        tiers[tier].append(a['name'])
            
            page.close()
            
            # Remove tiers vazios
            tiers = {k: v for k, v in tiers.items() if v}
            
            return {
                "status": "success",
                "map": map_name.capitalize() if map_name else "Todos os mapas",
                "all_agents": agents,
                "tiers": tiers,
                "url": url
            }
            
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def _is_number(self, s: str) -> bool:
        """Verifica se string é número."""
        try:
            s = s.replace('%', '').replace('-', '').replace(',', '.')
            float(s)
            return True
        except:
            return False
    
    def _parse_insights_text(self, text: str) -> List[Dict]:
        """Parse dados do insights via regex."""
        agents = []
        known_agents = [
            "Jett", "Reyna", "Raze", "Neon", "Yoru", "Phoenix", "Iso",
            "Omen", "Viper", "Brimstone", "Astra", "Clove", "Harbor",
            "Sova", "Fade", "Gekko", "Breach", "KAY/O", "Skye",
            "Killjoy", "Cypher", "Sage", "Chamber", "Deadlock", "Vyse"
        ]
        
        # Regex para pegar "AgentName Tier Role XX.X% XX.X%"
        pattern = r'(\w+)\s+([SABCDF])\s+\w+\s+(Duelist|Controller|Initiator|Sentinel)\s+([\d.]+)%\s+([\d.]+)%'
        matches = re.findall(pattern, text)
        
        current_tier = "S"
        for match in matches:
            name, tier, role, pick, win = match
            if name in known_agents:
                agents.append({
                    "name": name,
                    "role": role,
                    "tier": tier,
                    "pick_rate": float(pick),
                    "win_rate": float(win),
                    "kd": 0
                })
        
        return agents
    
    def get_map_meta(self, map_name: str = None) -> Dict[str, Any]:
        """
        Busca meta de um mapa específico via Insights.
        Redireciona para get_agents_meta com filtro de mapa.
        """
        if map_name:
            return self.get_agents_meta(map_name)
        else:
            return self._get_all_maps_list()
    
    def _get_all_maps_list(self) -> Dict[str, Any]:
        """Retorna lista de mapas disponíveis."""
        # Mapas do pool competitivo atual
        maps = ['abyss', 'ascent', 'bind', 'haven', 'icebox', 'lotus', 'pearl', 'split', 'sunset']
        
        return {
            "status": "success",
            "maps": maps,
            "note": "Use get_map_meta(map_name) para ver o meta de cada mapa"
        }
    
    def _get_all_maps_meta(self) -> Dict[str, Any]:
        """Busca lista de todos os mapas - DEPRECATED, use _get_all_maps_list."""
        return self._get_all_maps_list()
    
    def get_compositions(self, map_name: str) -> Dict[str, Any]:
        """
        Busca composições populares/recomendadas para um mapa.
        URL: https://tracker.gg/valorant/meta/comps?map={map}
        """
        url = f"{self.BASE_URL}/meta/comps?map={map_name.lower()}"
        
        try:
            page = self._new_page()
            page.goto(url, wait_until='networkidle', timeout=60000)
            
            try:
                page.wait_for_selector('.comp, .composition, .team-comp', timeout=15000)
            except:
                page.wait_for_timeout(5000)
            
            comps = []
            
            # Tenta diferentes seletores
            comp_elements = page.query_selector_all('.comp-row, .composition, tr[class*="comp"]')
            
            for comp_el in comp_elements:
                try:
                    agents = []
                    agent_els = comp_el.query_selector_all('.agent, .agent-icon, img[alt]')
                    
                    for agent_el in agent_els:
                        name = agent_el.get_attribute('alt') or agent_el.inner_text()
                        if name:
                            agents.append(name.strip())
                    
                    if len(agents) == 5:
                        win_el = comp_el.query_selector('[class*="win"], .winrate')
                        pick_el = comp_el.query_selector('[class*="pick"], .pickrate')
                        
                        comps.append({
                            "agents": agents,
                            "win_rate": self._parse_percent(win_el.inner_text() if win_el else "0"),
                            "pick_rate": self._parse_percent(pick_el.inner_text() if pick_el else "0")
                        })
                except:
                    continue
            
            page.close()
            
            # Ordena por winrate
            comps_sorted = sorted(comps, key=lambda x: x.get('win_rate', 0), reverse=True)
            
            return {
                "status": "success",
                "map": map_name.capitalize(),
                "compositions": comps_sorted[:10],
                "best_comp": comps_sorted[0] if comps_sorted else None,
                "url": url
            }
            
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def get_agent_details(self, agent_name: str) -> Dict[str, Any]:
        """
        Busca detalhes de um agente específico.
        URL: https://tracker.gg/valorant/meta/agents/{agent}
        """
        url = f"{self.BASE_URL}/meta/agents/{agent_name.lower()}"
        
        try:
            page = self._new_page()
            page.goto(url, wait_until='networkidle', timeout=60000)
            
            try:
                page.wait_for_selector('.stat, .agent-stats', timeout=15000)
            except:
                page.wait_for_timeout(5000)
            
            text = page.inner_text('body')
            
            # Extrai stats gerais
            pick_rate = self._find_stat_in_text(text, 'pick rate')
            win_rate = self._find_stat_in_text(text, 'win rate')
            kd = self._find_stat_in_text(text, 'k/d')
            
            # Busca melhores mapas para esse agente
            best_maps = []
            map_rows = page.query_selector_all('.map-row, tr[class*="map"]')
            
            for row in map_rows:
                try:
                    map_name_el = row.query_selector('.map-name, td:first-child')
                    win_el = row.query_selector('[class*="win"], td:nth-child(2)')
                    
                    if map_name_el:
                        best_maps.append({
                            "map": map_name_el.inner_text().strip(),
                            "win_rate": self._parse_percent(win_el.inner_text() if win_el else "0")
                        })
                except:
                    continue
            
            page.close()
            
            # Determina role
            role = self._get_agent_role(agent_name)
            
            return {
                "status": "success",
                "agent": agent_name.capitalize(),
                "role": role,
                "pick_rate": pick_rate,
                "win_rate": win_rate,
                "kd": kd,
                "best_maps": sorted(best_maps, key=lambda x: x.get('win_rate', 0), reverse=True)[:5],
                "url": url
            }
            
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    # === HELPERS ===
    
    def _parse_percent(self, text: str) -> float:
        """Extrai porcentagem de uma string."""
        try:
            m = re.search(r'(\d+\.?\d*)', text.replace(',', '.'))
            return float(m.group(1)) if m else 0.0
        except:
            return 0.0
    
    def _parse_float(self, text: str) -> float:
        """Extrai float de uma string."""
        try:
            m = re.search(r'(\d+\.?\d*)', text.replace(',', '.'))
            return float(m.group(1)) if m else 0.0
        except:
            return 0.0
    
    def _extract_stat(self, elements, stat_type: str) -> float:
        """Extrai stat específico de uma lista de elementos."""
        for el in elements:
            try:
                text = el.inner_text().lower()
                if stat_type in text or '%' in text:
                    return self._parse_percent(text)
            except:
                continue
        return 0.0
    
    def _find_stat_in_text(self, text: str, stat_name: str) -> float:
        """Encontra stat no texto."""
        try:
            pattern = rf'{stat_name}[:\s]*(\d+\.?\d*)%?'
            m = re.search(pattern, text.lower())
            return float(m.group(1)) if m else 0.0
        except:
            return 0.0
    
    def _parse_agents_from_text(self, text: str) -> List[Dict]:
        """Fallback: extrai agentes do texto geral."""
        known_agents = [
            "Jett", "Reyna", "Raze", "Neon", "Yoru", "Phoenix", "Iso",
            "Omen", "Viper", "Brimstone", "Astra", "Clove", "Harbor",
            "Sova", "Fade", "Gekko", "Breach", "KAY/O", "Skye",
            "Killjoy", "Cypher", "Sage", "Chamber", "Deadlock", "Vyse"
        ]
        
        agents = []
        for agent in known_agents:
            if agent.lower() in text.lower():
                agents.append({
                    "name": agent,
                    "pick_rate": 0,
                    "win_rate": 0,
                    "kd": 0
                })
        
        return agents
    
    def _get_agent_role(self, agent_name: str) -> str:
        """Retorna role do agente."""
        roles = {
            "Duelist": ["jett", "reyna", "raze", "neon", "yoru", "phoenix", "iso"],
            "Controller": ["omen", "viper", "brimstone", "astra", "clove", "harbor"],
            "Initiator": ["sova", "fade", "gekko", "breach", "kay/o", "kayo", "skye"],
            "Sentinel": ["killjoy", "cypher", "sage", "chamber", "deadlock", "vyse"]
        }
        
        agent_lower = agent_name.lower()
        for role, agents in roles.items():
            if agent_lower in agents:
                return role
        
        return "Unknown"
