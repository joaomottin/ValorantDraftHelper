"""
Testes das ferramentas locais (sem scraping)
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.agent_tools import (
    get_agents_meta,
    get_map_meta,
    get_all_maps,
    analyze_team_composition,
    get_agent_info,
    recommend_agents_for_draft
)


def test_get_agents_meta():
    print("\n" + "=" * 50)
    print("TEST: get_agents_meta()")
    result = get_agents_meta()
    
    assert result["status"] == "ok", "Status deveria ser 'ok'"
    assert "agents" in result, "Deveria ter 'agents'"
    assert len(result["agents"]) > 0, "Deveria ter agentes"
    
    print(f"✅ {len(result['agents'])} agentes encontrados")
    print(f"   Tiers: {list(result['tier_list'].keys())}")
    return True


def test_get_map_meta():
    print("\n" + "=" * 50)
    print("TEST: get_map_meta('ascent')")
    result = get_map_meta("ascent")
    
    assert result["status"] == "ok", f"Status deveria ser 'ok': {result}"
    assert "top_agents" in result, "Deveria ter 'top_agents'"
    
    print(f"✅ Mapa: {result['map']}")
    print(f"   Top agents: {result['top_agents']}")
    return True


def test_get_map_meta_invalid():
    print("\n" + "=" * 50)
    print("TEST: get_map_meta('mapa_fake')")
    result = get_map_meta("mapa_fake")
    
    assert result["status"] == "error", "Deveria retornar erro"
    assert "available_maps" in result, "Deveria listar mapas disponíveis"
    
    print(f"✅ Erro correto: {result['error']}")
    return True


def test_get_all_maps():
    print("\n" + "=" * 50)
    print("TEST: get_all_maps()")
    result = get_all_maps()
    
    assert result["status"] == "ok", "Status deveria ser 'ok'"
    assert len(result["maps"]) >= 8, "Deveria ter pelo menos 8 mapas"
    
    print(f"✅ {result['total']} mapas: {result['maps']}")
    return True


def test_analyze_team_composition():
    print("\n" + "=" * 50)
    print("TEST: analyze_team_composition(['Jett', 'Omen', 'Sova', 'Killjoy', 'Sage'])")
    result = analyze_team_composition(["Jett", "Omen", "Sova", "Killjoy", "Sage"])
    
    assert result["status"] == "ok", "Status deveria ser 'ok'"
    assert "role_count" in result, "Deveria ter contagem de roles"
    assert result["role_count"]["Controller"] == 1, "Deveria ter 1 controller"
    
    print(f"✅ Score: {result['composition_score']}/10")
    print(f"   Roles: {result['role_count']}")
    print(f"   Verdict: {result['verdict']}")
    return True


def test_analyze_bad_composition():
    print("\n" + "=" * 50)
    print("TEST: analyze_team_composition(['Jett', 'Reyna', 'Phoenix'])")
    result = analyze_team_composition(["Jett", "Reyna", "Phoenix"])
    
    assert len(result["issues"]) > 0, "Deveria ter issues"
    assert len(result["suggestions"]) > 0, "Deveria ter sugestões"
    
    print(f"✅ Issues encontradas: {len(result['issues'])}")
    for issue in result["issues"]:
        print(f"   {issue}")
    return True


def test_get_agent_info():
    print("\n" + "=" * 50)
    print("TEST: get_agent_info('Jett')")
    result = get_agent_info("Jett")
    
    assert result["status"] == "ok", f"Status deveria ser 'ok': {result}"
    assert result["role"] == "Duelist", "Jett deveria ser Duelist"
    
    print(f"✅ {result['name']}: {result['role']}")
    print(f"   Tier: {result['tier']}, Win Rate: {result['win_rate']}%")
    return True


def test_recommend_agents_for_draft():
    print("\n" + "=" * 50)
    print("TEST: recommend_agents_for_draft('ascent', ['Jett'], ['Omen'])")
    result = recommend_agents_for_draft(
        map_name="ascent",
        allied_agents=["Jett"],
        enemy_agents=["Omen"]
    )
    
    assert result["status"] == "ok", f"Status deveria ser 'ok': {result}"
    assert "recommendations" in result, "Deveria ter recomendações"
    assert len(result["recommendations"]) > 0, "Deveria ter pelo menos 1 recomendação"
    
    # Omen não pode estar nas recomendações (enemy já pegou)
    rec_names = [r["agent"].lower() for r in result["recommendations"]]
    assert "omen" not in rec_names, "Omen não deveria ser recomendado (já foi pickado)"
    
    print(f"✅ Roles necessárias: {result['roles_needed']}")
    print("   Recomendações:")
    for rec in result["recommendations"][:3]:
        print(f"   - {rec['agent']} ({rec['role']}): {rec['reason']}")
    return True


def main():
    print("🧪 TESTES DAS FERRAMENTAS LOCAIS")
    print("=" * 50)
    
    tests = [
        test_get_agents_meta,
        test_get_map_meta,
        test_get_map_meta_invalid,
        test_get_all_maps,
        test_analyze_team_composition,
        test_analyze_bad_composition,
        test_get_agent_info,
        test_recommend_agents_for_draft,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
        except AssertionError as e:
            print(f"❌ FALHOU: {e}")
            failed += 1
        except Exception as e:
            print(f"❌ ERRO: {e}")
            failed += 1
    
    print("\n" + "=" * 50)
    print(f"📊 RESULTADO: {passed} passaram, {failed} falharam")
    
    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
