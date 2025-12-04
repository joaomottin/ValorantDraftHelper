// ============================================
// VALORANT DRAFT HELPER - JavaScript
// ============================================

let selectedImage = null;

function previewImage(event) {
    const file = event.target.files[0];
    if (file) {
        const reader = new FileReader();
        reader.onload = function(e) {
            selectedImage = e.target.result;
            document.getElementById('preview-image').src = selectedImage;
            document.getElementById('preview-container').classList.add('active');
        };
        reader.readAsDataURL(file);
    }
}

function removeImage() {
    selectedImage = null;
    document.getElementById('file-input').value = '';
    document.getElementById('preview-container').classList.remove('active');
}

function handleKeyPress(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        sendMessage();
    }
}

// Ctrl+V para colar imagem do clipboard
document.addEventListener('paste', async function(event) {
    const items = event.clipboardData?.items;
    if (!items) return;
    
    for (const item of items) {
        if (item.type.startsWith('image/')) {
            event.preventDefault();
            const file = item.getAsFile();
            if (file) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    selectedImage = e.target.result;
                    document.getElementById('preview-image').src = selectedImage;
                    document.getElementById('preview-container').classList.add('active');
                };
                reader.readAsDataURL(file);
            }
            break;
        }
    }
});

function formatMessage(content) {
    return content
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/`([^`]+)`/g, '<code>$1</code>')
        .replace(/```([\s\S]*?)```/g, '<pre>$1</pre>')
        .replace(/\n/g, '<br>');
}

function addMessage(content, isUser, imageUrl = null) {
    const chatBox = document.getElementById('chat-box');
    const welcome = chatBox.querySelector('.welcome');
    if (welcome) welcome.remove();
    
    const msg = document.createElement('div');
    msg.className = `message ${isUser ? 'user' : 'assistant'}`;
    
    let html = `<div class="content">${formatMessage(content)}</div>`;
    
    if (imageUrl) {
        html += `<img src="${imageUrl}" alt="Imagem enviada">`;
    }
    
    html += `<div class="avatar">${isUser ? '👤' : '🎮'}</div>`;
    
    msg.innerHTML = html;
    chatBox.appendChild(msg);
    chatBox.scrollTop = chatBox.scrollHeight;
}

function showLoading() {
    const chatBox = document.getElementById('chat-box');
    const loading = document.createElement('div');
    loading.className = 'loading';
    loading.id = 'loading';
    loading.innerHTML = `
        <div class="loading-dots">
            <span></span><span></span><span></span>
        </div>
        <span class="loading-text">Analisando...</span>
    `;
    chatBox.appendChild(loading);
    chatBox.scrollTop = chatBox.scrollHeight;
}

function hideLoading() {
    const loading = document.getElementById('loading');
    if (loading) loading.remove();
}

async function sendMessage() {
    const input = document.getElementById('message-input');
    const message = input.value.trim();
    
    if (!message && !selectedImage) return;
    
    addMessage(message || '📸 Imagem enviada', true, selectedImage);
    
    const imageToSend = selectedImage;
    input.value = '';
    removeImage();
    
    document.getElementById('send-btn').disabled = true;
    showLoading();
    
    try {
        const response = await fetch('/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message: message,
                image: imageToSend
            })
        });
        
        const data = await response.json();
        hideLoading();
        
        if (data.error) {
            addMessage(`❌ Erro: ${data.error}`, false);
        } else {
            addMessage(data.response, false);
        }
    } catch (error) {
        hideLoading();
        addMessage(`❌ Erro de conexão: ${error.message}`, false);
    }
    
    document.getElementById('send-btn').disabled = false;
}

async function executeTool(toolName, params = {}) {
    // Redireciona para o chat - o agente usa google_search para buscar dados
    let message = '';
    
    switch(toolName) {
        case 'get_agents_meta':
            message = 'Qual a tier list atual dos agentes?';
            break;
        case 'get_map_meta':
            message = `Quais os melhores agentes para o mapa ${params.map_name}?`;
            break;
        case 'get_player_stats':
            message = `Busque informações sobre o jogador ${params.nickname}#${params.tag}`;
            break;
        case 'get_all_maps':
            message = 'Quais são os mapas ativos no competitivo?';
            break;
        default:
            message = `Execute a ferramenta ${toolName}`;
    }
    
    // Coloca a mensagem no input e envia
    document.getElementById('message-input').value = message;
    await sendMessage();
}

function formatToolResult(toolName, data) {
    switch(toolName) {
        case 'get_all_maps':
            if (data.maps) {
                return `🗺️ **Mapas Disponíveis**\n\n${data.maps.map(m => `• ${m.charAt(0).toUpperCase() + m.slice(1)}`).join('\n')}`;
            }
            break;
    }
    return `\`\`\`json\n${JSON.stringify(data, null, 2)}\n\`\`\``;
}

function askTierList() {
    document.getElementById('message-input').value = 'Qual a tier list atual dos agentes no meta?';
    sendMessage();
}

function askMap() {
    const map = prompt('Qual mapa? (ascent, bind, haven, split, lotus, sunset, icebox, abyss, pearl)');
    if (map) {
        document.getElementById('message-input').value = `Quais os melhores agentes para ${map}?`;
        sendMessage();
    }
}

function askPlayer() {
    const nick = prompt('Nick#Tag do jogador (ex: Player#BR1):');
    if (nick) {
        document.getElementById('message-input').value = `Busque informações sobre ${nick}`;
        sendMessage();
    }
}

async function clearChat() {
    await fetch('/clear', { method: 'POST' });
    document.getElementById('chat-box').innerHTML = getWelcomeHTML();
}

function getWelcomeHTML() {
    return `
        <div class="welcome">
            <div class="welcome-icon">🎮</div>
            <h2>Draft Helper</h2>
            <p>Seu coach de Valorant com IA</p>
            <div class="feature-cards">
                <div class="feature-card">
                    <div class="icon">📸</div>
                    <h4>Análise Visual</h4>
                    <p>Envie print da seleção</p>
                </div>
                <div class="feature-card">
                    <div class="icon">🔍</div>
                    <h4>Busca na Web</h4>
                    <p>Dados atualizados</p>
                </div>
                <div class="feature-card">
                    <div class="icon">🎯</div>
                    <h4>Meta Atual</h4>
                    <p>Tier list atualizada</p>
                </div>
                <div class="feature-card">
                    <div class="icon">💡</div>
                    <h4>Recomendações</h4>
                    <p>Pick ideal para você</p>
                </div>
            </div>
        </div>
    `;
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    // Hide preview container initially
    document.getElementById('preview-container').classList.remove('active');
});
