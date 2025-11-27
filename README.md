# 🎮 Valorant Draft Helper

<div align="center">

![Valorant](https://img.shields.io/badge/VALORANT-ff4655?style=for-the-badge&logo=valorant&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.10+-3776ab?style=for-the-badge&logo=python&logoColor=white)
![Gemini](https://img.shields.io/badge/Gemini_2.5-4285F4?style=for-the-badge&logo=google&logoColor=white)

**Seu coach de Valorant com IA** 🤖

Envie uma foto da tela de seleção e receba recomendações personalizadas!

</div>

---

## ✨ Features

| Feature | Descrição |
|---------|-----------|
| 📸 **Análise de Imagem** | Envia print da seleção, IA identifica mapa e agentes |
| 📊 **Stats em Tempo Real** | Busca dados do Tracker.gg automaticamente |
| 🎯 **Tier List Atualizada** | Meta atual de todos os mapas |
| 💡 **Recomendações** | Sugere o melhor pick baseado no seu perfil |

---

## 🚀 Como Rodar

### 1️⃣ Clone o repositório
```bash
git clone https://github.com/joaomottin/DraftHelperValorant.git
cd DraftHelperValorant
```

### 2️⃣ Instale as dependências
```bash
pip install -r requirements.txt
playwright install chromium
```

### 3️⃣ Configure a API Key
Crie um arquivo `.env` na pasta do projeto:
```env
GOOGLE_API_KEY=sua_chave_aqui
```

> 🔑 Pegue sua chave em: [Google AI Studio](https://aistudio.google.com/apikey)

### 4️⃣ Rode o servidor
```bash
python app.py
```

### 5️⃣ Acesse no navegador
```
http://127.0.0.1:5000
```

---

## 📁 Estrutura

```
ValorantHelper/
├── app.py          # Servidor Flask
├── agent.py        # Agente ADK (alternativo)
├── tools.py        # Ferramentas de busca
├── scraper.py      # Web scraper Tracker.gg
├── .env            # API Key (criar)
├── requirements.txt
├── static/
│   ├── style.css   # Estilos
│   └── script.js   # JavaScript
└── templates/
    └── index.html  # Interface
```

---

## 🎮 Como Usar

1. **Envie uma imagem** da tela de seleção de agentes
2. A IA vai identificar o **mapa** e os **agentes** já escolhidos
3. Digite seu **nick#tag** para buscar suas stats
4. Receba **recomendações** personalizadas!

### Comandos Rápidos (Sidebar)
- 📊 **Tier List** - Meta atual de todos os agentes
- 🗺️ **Mapas** - Lista de mapas disponíveis  
- 🎯 **Meta** - Tier list específica de um mapa
- 👤 **Player** - Buscar stats de um jogador

---

## 🔧 Requisitos

- Python 3.10+
- Google Chrome instalado
- Chave da API Gemini

---

## 📝 Licença

MIT License - Use à vontade! 🎉

---

<div align="center">

**Feito com ❤️ para a comunidade Valorant**

⭐ Deixe uma star se curtiu!

</div>
