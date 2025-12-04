#  Valorant Draft Helper

Assistente de IA para ajudar na seleção de agentes (agent select) no Valorant.

##  Funcionalidades

- **Análise de tela de seleção** - Envie uma imagem do agent select e receba recomendações
- **Tier list atualizada** - Meta do Episode 9 Act 3
- **Análise de composição** - Verifica se seu time tem as roles necessárias
- **Recomendações por mapa** - Agentes específicos para cada mapa
- **Interface web** - Chat com suporte a imagens

##  Como usar

### 1. Instalar dependências
`ash
pip install -r requirements.txt
`

### 2. Configurar API Key
Crie um arquivo `.env`:
`
GOOGLE_API_KEY=sua_chave_aqui
`

### 3. Executar

**Interface Web:**
`ash
python app.py
`
Acesse: http://localhost:5000

**CLI:**
`ash
python agent.py
`

##  Estrutura

`
ValorantHelper/
 agent.py           # Agente principal (LlmAgent)
 app.py             # Interface web Flask
 instructions.md    # Instruções do agente
 data/
    meta_data.py   # Dados do meta (fallback)
 tools/
    agent_tools.py # Ferramentas do agente
 static/            # CSS e JavaScript
 templates/         # HTML
 tests/             # Testes
`

##  Ferramentas disponíveis

| Ferramenta | Descrição |
|------------|-----------|
| `get_agents_meta()` | Tier list geral de agentes |
| `get_map_meta(map_name)` | Melhores agentes para um mapa |
| `get_all_maps()` | Lista de mapas ativos |
| `analyze_team_composition(agents)` | Analisa composição de time |
| `get_agent_info(agent_name)` | Info de um agente específico |
| `recommend_agents_for_draft(...)` | Recomendações contextuais |

##  Testes
`ash
python tests/test_tools.py
`

##  Notas

- O agente responde **apenas em português**
- Envie apenas imagens da **tela de seleção de agentes**
- Dados do meta são atualizados periodicamente no arquivo `data/meta_data.py`
