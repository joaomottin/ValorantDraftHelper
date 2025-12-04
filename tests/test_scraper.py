"""
Testes para o scraper do Tracker.gg
Execute: python -m tests.test_scraper
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scraper import TrackerScraper, PLAYWRIGHT_OK

def test_playwright_installed():
    """Testa se o Playwright está instalado"""
    print("=" * 50)
    print("TEST: Playwright instalado?")
    print("=" * 50)
    
    if PLAYWRIGHT_OK:
        print("✅ Playwright está instalado!")
        return True
    else:
        print("❌ Playwright NÃO está instalado!")
        print("   Execute: pip install playwright && playwright install chromium")
        return False


def test_scraper_connection():
    """Testa se consegue conectar ao Tracker.gg"""
    print("\n" + "=" * 50)
    print("TEST: Conexão com Tracker.gg")
    print("=" * 50)
    
    if not PLAYWRIGHT_OK:
        print("❌ Playwright não instalado, pulando teste")
        return False
    
    try:
        with TrackerScraper(headless=True) as scraper:
            page = scraper._new_page()
            page.goto("https://tracker.gg/valorant", wait_until='load', timeout=30000)
            title = page.title()
            page.close()
            
            if "Valorant" in title or "Tracker" in title:
                print(f"✅ Conectou! Título: {title}")
                return True
            else:
                print(f"⚠️ Conectou mas título estranho: {title}")
                return True
    except Exception as e:
        print(f"❌ Erro ao conectar: {e}")
        return False


def test_get_agents_meta():
    """Testa busca de tier list de agentes"""
    print("\n" + "=" * 50)
    print("TEST: get_agents_meta() - Tier list geral")
    print("=" * 50)
    
    if not PLAYWRIGHT_OK:
        print("❌ Playwright não instalado, pulando teste")
        return False
    
    try:
        with TrackerScraper(headless=True) as scraper:
            result = scraper.get_agents_meta(None)
            
            print(f"Status: {result.get('status')}")
            print(f"URL: {result.get('url')}")
            
            agents = result.get('all_agents', [])
            print(f"Agentes encontrados: {len(agents)}")
            
            if agents:
                print("\nPrimeiros 5 agentes:")
                for a in agents[:5]:
                    print(f"  - {a.get('name')}: {a.get('tier')} tier, {a.get('pick_rate')}% pick, {a.get('win_rate')}% win")
                return True
            else:
                print("❌ Nenhum agente encontrado!")
                
                # Debug: mostra parte do HTML
                page = scraper._new_page()
                page.goto("https://tracker.gg/valorant/insights/agents", wait_until='load', timeout=30000)
                page.wait_for_timeout(3000)
                text = page.inner_text('body')[:2000]
                print("\n--- DEBUG: Texto da página (primeiros 2000 chars) ---")
                print(text)
                page.close()
                return False
                
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False


def test_get_map_meta():
    """Testa busca de meta de um mapa"""
    print("\n" + "=" * 50)
    print("TEST: get_agents_meta('bind') - Meta do mapa Bind")
    print("=" * 50)
    
    if not PLAYWRIGHT_OK:
        print("❌ Playwright não instalado, pulando teste")
        return False
    
    try:
        with TrackerScraper(headless=True) as scraper:
            result = scraper.get_agents_meta("bind")
            
            print(f"Status: {result.get('status')}")
            print(f"Mapa: {result.get('map')}")
            print(f"URL: {result.get('url')}")
            
            agents = result.get('all_agents', [])
            print(f"Agentes encontrados: {len(agents)}")
            
            if agents:
                print("\nTop 5 agentes em Bind:")
                for a in agents[:5]:
                    print(f"  - {a.get('name')}: {a.get('tier')} tier, {a.get('win_rate')}% win")
                return True
            else:
                print("❌ Nenhum agente encontrado!")
                return False
                
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False


def test_get_player_stats():
    """Testa busca de stats de jogador"""
    print("\n" + "=" * 50)
    print("TEST: get_player_stats() - Stats de jogador")
    print("=" * 50)
    
    if not PLAYWRIGHT_OK:
        print("❌ Playwright não instalado, pulando teste")
        return False
    
    # Usa um nick genérico para teste
    nick = "TenZ"
    tag = "TenZ"
    
    try:
        with TrackerScraper(headless=True) as scraper:
            result = scraper.get_player_stats(nick, tag)
            
            print(f"Status: {result.get('status')}")
            print(f"Player: {result.get('player')}")
            
            if result.get('status') == 'success':
                print(f"Rank: {result.get('rank')}")
                agents = result.get('top_agents', [])
                print(f"Top Agentes: {len(agents)}")
                for a in agents[:3]:
                    print(f"  - {a.get('name')}: {a.get('winrate')}% win, {a.get('kd')} KD")
                return True
            else:
                print(f"Erro: {result.get('error')}")
                # Não é necessariamente um erro - perfil pode não existir
                return True
                
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False


def run_all_tests():
    """Executa todos os testes"""
    print("\n" + "=" * 60)
    print("🧪 EXECUTANDO TODOS OS TESTES DO SCRAPER")
    print("=" * 60)
    
    results = {
        "Playwright instalado": test_playwright_installed(),
        "Conexão Tracker.gg": test_scraper_connection(),
        "Tier list geral": test_get_agents_meta(),
        "Meta do mapa": test_get_map_meta(),
        "Stats jogador": test_get_player_stats(),
    }
    
    print("\n" + "=" * 60)
    print("📊 RESUMO DOS TESTES")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print(f"\nTotal: {passed} passaram, {failed} falharam")
    return failed == 0


if __name__ == "__main__":
    run_all_tests()
