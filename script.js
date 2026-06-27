// Clock and Date Update
function updateClock() {
    const now = new Date();
    const timeElement = document.getElementById('time');
    const dateElement = document.getElementById('date');
    
    const hours = String(now.getHours()).padStart(2, '0');
    const minutes = String(now.getMinutes()).padStart(2, '0');
    const seconds = String(now.getSeconds()).padStart(2, '0');
    
    timeElement.textContent = `${hours}:${minutes}:${seconds}`;
    
    const options = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
    dateElement.textContent = now.toLocaleDateString('en-US', options);
}

// System Stats Simulation
function updateSystemStats() {
    const cpuValue = Math.floor(Math.random() * 30) + 30; // 30-60%
    const ramValue = Math.floor(Math.random() * 20) + 50; // 50-70%
    const diskValue = Math.floor(Math.random() * 10) + 35; // 35-45%
    const networkValue = Math.floor(Math.random() * 40) + 10; // 10-50%
    
    document.getElementById('cpu-bar').style.width = `${cpuValue}%`;
    document.getElementById('cpu-value').textContent = `${cpuValue}%`;
    
    document.getElementById('ram-bar').style.width = `${ramValue}%`;
    document.getElementById('ram-value').textContent = `${ramValue}%`;
    
    document.getElementById('disk-bar').style.width = `${diskValue}%`;
    document.getElementById('disk-value').textContent = `${diskValue}%`;
    
    document.getElementById('network-bar').style.width = `${networkValue}%`;
    document.getElementById('network-value').textContent = `${networkValue}%`;
}

// System Uptime
let startTime = new Date();
let commandCount = 0;

function updateUptime() {
    const now = new Date();
    const diff = now - startTime;
    
    const hours = Math.floor(diff / (1000 * 60 * 60));
    const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
    const seconds = Math.floor((diff % (1000 * 60)) / 1000);
    
    const uptimeElement = document.getElementById('uptime');
    uptimeElement.textContent = `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
}

// Control Buttons
const cameraBtn = document.getElementById('camera-btn');
const micBtn = document.getElementById('mic-btn');
const keyboardBtn = document.getElementById('keyboard-btn');
const assistantStatus = document.getElementById('assistant-status');

let cameraActive = false;
let micActive = false;

cameraBtn.addEventListener('click', () => {
    cameraActive = !cameraActive;
    cameraBtn.classList.toggle('active', cameraActive);
    
    const cameraStatus = document.querySelector('.camera-status .status-dot');
    const cameraText = document.querySelector('.camera-status .status-text');
    
    if (cameraActive) {
        cameraStatus.classList.remove('offline');
        cameraStatus.classList.add('online');
        cameraText.textContent = 'Camera ON';
        assistantStatus.textContent = 'Camera activated - Monitoring...';
    } else {
        cameraStatus.classList.remove('online');
        cameraStatus.classList.add('offline');
        cameraText.textContent = 'Camera OFF';
        assistantStatus.textContent = 'Listening for wake words...';
    }
});

micBtn.addEventListener('click', async () => {
    micActive = !micActive;
    micBtn.classList.toggle('active', micActive);
    
    // Update backend mic status
    await setMicStatus(micActive ? 'True' : 'False');
    
    if (micActive) {
        assistantStatus.textContent = 'Microphone active - Listening...';
    } else {
        assistantStatus.textContent = 'Listening for wake words...';
    }
});

keyboardBtn.addEventListener('click', () => {
    document.getElementById('message-input').focus();
    assistantStatus.textContent = 'Keyboard input mode active';
});

// Chat Functionality
const messageInput = document.getElementById('message-input');
const sendBtn = document.getElementById('send-btn');
const conversationMessages = document.getElementById('conversation-messages');
const clearChatBtn = document.getElementById('clear-chat');
const exportChatBtn = document.getElementById('export-chat');

let conversationHistory = [];
let lastResponseContent = '';

// API Communication
async function sendTextToBackend(text) {
    try {
        const response = await fetch('/api/text-input', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ text: text })
        });
        return await response.json();
    } catch (error) {
        console.error('Error sending text to backend:', error);
        return { success: false };
    }
}

async function setWeatherLocation(location) {
    try {
        const response = await fetch('/api/weather-location', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ location: location })
        });
        return await response.json();
    } catch (error) {
        console.error('Error setting weather location:', error);
        return { success: false };
    }
}

async function getWeatherData() {
    try {
        const response = await fetch('/api/weather');
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Error getting weather data:', error);
        return null;
    }
}

async function getResponses() {
    try {
        const response = await fetch('/api/responses');
        const data = await response.json();
        return data.responses || '';
    } catch (error) {
        console.error('Error getting responses:', error);
        return '';
    }
}

async function getStatus() {
    try {
        const response = await fetch('/api/status');
        const data = await response.json();
        return data.status || 'Available...';
    } catch (error) {
        console.error('Error getting status:', error);
        return 'Available...';
    }
}

async function getMicStatus() {
    try {
        const response = await fetch('/api/mic');
        const data = await response.json();
        return data.mic || 'False';
    } catch (error) {
        console.error('Error getting mic status:', error);
        return 'False';
    }
}

async function setMicStatus(status) {
    try {
        const response = await fetch('/api/mic', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ status: status })
        });
        return await response.json();
    } catch (error) {
        console.error('Error setting mic status:', error);
        return { success: false };
    }
}

function addMessage(content, isUser = false) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${isUser ? 'user-message' : 'ai-message'}`;
    
    const avatarDiv = document.createElement('div');
    avatarDiv.className = 'message-avatar';
    avatarDiv.textContent = isUser ? 'U' : 'AI';
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    
    const paragraph = document.createElement('p');
    paragraph.textContent = content;
    
    contentDiv.appendChild(paragraph);
    messageDiv.appendChild(avatarDiv);
    messageDiv.appendChild(contentDiv);
    
    conversationMessages.appendChild(messageDiv);
    conversationMessages.scrollTop = conversationMessages.scrollHeight;
    
    conversationHistory.push({
        content: content,
        isUser: isUser,
        timestamp: new Date().toISOString()
    });
}

function sendMessage() {
    const message = messageInput.value.trim();
    if (message) {
        addMessage(message, true);
        messageInput.value = '';
        commandCount++;
        document.getElementById('commands').textContent = commandCount;
        
        // Send to Python backend
        sendTextToBackend(message);
        assistantStatus.textContent = 'Processing...';
        
        // Clear the last response content to force refresh
        lastResponseContent = '';
    }
}

sendBtn.addEventListener('click', sendMessage);

messageInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        sendMessage();
    }
});

// Clear Chat
clearChatBtn.addEventListener('click', () => {
    conversationMessages.innerHTML = '';
    conversationHistory = [];
    addMessage("Chat cleared. How can I assist you today?", false);
});

// Export Chat
exportChatBtn.addEventListener('click', () => {
    if (conversationHistory.length === 0) {
        alert('No conversation to export.');
        return;
    }
    
    let exportText = 'J.A.R.V.I.S Conversation Export\n';
    exportText += '==============================\n\n';
    
    conversationHistory.forEach((msg, index) => {
        const timestamp = new Date(msg.timestamp).toLocaleString();
        const sender = msg.isUser ? 'USER' : 'JARVIS';
        exportText += `[${timestamp}] ${sender}: ${msg.content}\n\n`;
    });
    
    const blob = new Blob([exportText], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `jarvis_conversation_${new Date().toISOString().slice(0, 10)}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
});

// Initialize
updateClock();
updateSystemStats();
updateUptime();

// Initialize weather display on load
window.addEventListener('load', async () => {
    messageInput.focus();
    await updateWeatherDisplay();
    // Initial poll for conversation
    await pollForResponses();
});

// Update intervals
setInterval(updateClock, 1000);
setInterval(updateSystemStats, 3000);
setInterval(updateUptime, 1000);

// Add some initial random system activity
setInterval(() => {
    const activityElement = document.getElementById('activity');
    const activities = ['Active', 'Processing', 'Monitoring', 'Standby', 'Analyzing'];
    activityElement.textContent = activities[Math.floor(Math.random() * activities.length)];
}, 5000);

// Keyboard shortcut for microphone
document.addEventListener('keydown', (e) => {
    if (e.ctrlKey && e.key === 'm') {
        e.preventDefault();
        micBtn.click();
    }
});

// Add visual feedback when typing
messageInput.addEventListener('input', () => {
    if (messageInput.value.length > 0) {
        assistantStatus.textContent = 'Receiving input...';
    } else {
        assistantStatus.textContent = 'Listening for wake words...';
    }
});

// Poll for responses from backend
async function pollForResponses() {
    try {
        const responses = await getResponses();
        if (responses && responses !== lastResponseContent) {
            const newContent = responses.replace(lastResponseContent, '').trim();
            
            if (newContent) {
                lastResponseContent = responses;
                
                // Parse the responses and add new messages
                const lines = newContent.split('\n');
                
                // Process all lines to show conversation history
                for (const line of lines) {
                    const trimmedLine = line.trim();
                    if (!trimmedLine) continue;
                    
                    // Check if it's a user message or AI response
                    if (trimmedLine.includes('User:')) {
                        const userMessage = trimmedLine.replace('User:', '').trim();
                        // Don't add duplicate user messages
                        const lastMsg = conversationHistory[conversationHistory.length - 1];
                        if (!lastMsg || !lastMsg.isUser || lastMsg.content !== userMessage) {
                            addMessage(userMessage, true);
                        }
                    } else if (trimmedLine.includes('Assistant:') || trimmedLine.includes('JARVIS:')) {
                        const aiMessage = trimmedLine.replace(/Assistant:|JARVIS:/, '').trim();
                        // Don't add duplicate AI messages
                        const lastMsg = conversationHistory[conversationHistory.length - 1];
                        if (!lastMsg || lastMsg.isUser || lastMsg.content !== aiMessage) {
                            addMessage(aiMessage, false);
                        }
                    }
                }
            }
        }
        
        // Update status from backend
        const status = await getStatus();
        if (status && status !== 'Processing...') {
            assistantStatus.textContent = status;
        }
        
        // Update mic status from backend
        const micStatus = await getMicStatus();
        if (micStatus === 'True' && !micActive) {
            micActive = true;
            micBtn.classList.add('active');
        } else if (micStatus === 'False' && micActive) {
            micActive = false;
            micBtn.classList.remove('active');
        }
        
    } catch (error) {
        console.error('Error polling for responses:', error);
    }
}

// Weather location change functionality
const locationInput = document.getElementById('location-input');
const locationBtn = document.getElementById('location-btn');

locationBtn.addEventListener('click', async () => {
    const location = locationInput.value.trim();
    if (location) {
        console.log(`Setting weather location to: ${location}`);
        const result = await setWeatherLocation(location);
        console.log('Weather location result:', result);
        locationInput.value = '';
        assistantStatus.textContent = `Updating weather for ${location}...`;
        
        // Immediately update the weather display
        setTimeout(async () => {
            await updateWeatherDisplay();
            assistantStatus.textContent = 'Listening for wake words...';
        }, 500);
    }
});

locationInput.addEventListener('keypress', async (e) => {
    if (e.key === 'Enter') {
        const location = locationInput.value.trim();
        if (location) {
            console.log(`Setting weather location to: ${location}`);
            const result = await setWeatherLocation(location);
            console.log('Weather location result:', result);
            locationInput.value = '';
            assistantStatus.textContent = `Updating weather for ${location}...`;
            
            // Immediately update the weather display
            setTimeout(async () => {
                await updateWeatherDisplay();
                assistantStatus.textContent = 'Listening for wake words...';
            }, 500);
        }
    }
});

// Update weather display from backend
async function updateWeatherDisplay() {
    try {
        const weatherData = await getWeatherData();
        if (weatherData) {
            document.getElementById('weather-temp').textContent = `${weatherData.temp}°C`;
            document.getElementById('weather-condition').textContent = weatherData.condition;
            document.getElementById('weather-location').textContent = weatherData.location;
            document.getElementById('weather-humidity').textContent = `${weatherData.humidity}%`;
            document.getElementById('weather-wind').textContent = `${weatherData.wind} km/h`;
            document.getElementById('weather-feels').textContent = `${weatherData.feels_like}°C`;
        }
    } catch (error) {
        console.error('Error updating weather display:', error);
    }
}

// Poll for weather updates every 30 seconds
setInterval(updateWeatherDisplay, 30000);

// Start polling every 500ms
setInterval(pollForResponses, 500);

console.log('J.A.R.V.I.S System Initialized');
console.log('All systems operational');
