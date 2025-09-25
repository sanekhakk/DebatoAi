class DebateRoom {
    constructor() {
        //DATA INITIALIZATION 
        const debateDataElement = document.getElementById('debate-data');
        if (!debateDataElement) {
            console.error("Critical Error: Debate data script tag not found.");
            return;
        }
        this.debate = JSON.parse(debateDataElement.textContent);
        this.csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
        this.isAuthenticated = window.isAuthenticated === 'true'; 

        //TIMER STATE
        this.mainTimerInterval = null;
        this.replyTimerInterval = null;
        this.totalSeconds = this.debate.total_time_limit * 60;
        this.replySeconds = this.debate.reply_time_limit;

        //DOM ELEMENTS
        this.elements = {
            startButton: document.getElementById('start-debate-btn'),
            sendButton: document.getElementById('send-btn'),
            giveUpButton: document.getElementById('give-up-btn'),
            messageInput: document.getElementById('message-input'),
            messagesContainer: document.getElementById('messages-container'),
            welcomeMessage: document.getElementById('welcome-message'),
            typingIndicator: document.getElementById('typing-indicator'),
            mainTimerDisplay: document.getElementById('main-timer-display'),
            replyTimerDisplay: document.getElementById('reply-timer-display'),
            guestModal: document.getElementById('guest-trial-ended-modal'), // New modal element
        };

        this.initialize();
    }

    initialize() {
        this.addEventListeners();
    }

    addEventListeners() {
        if (this.elements.startButton) {
            this.elements.startButton.addEventListener('click', this.startDebate.bind(this));
        }
        if (this.elements.sendButton) {
            this.elements.sendButton.addEventListener('click', this.sendUserMessage.bind(this));
        }
        if (this.elements.giveUpButton) {
            this.elements.giveUpButton.addEventListener('click', this.giveUp.bind(this));
        }
        if (this.elements.messageInput) {
            this.elements.messageInput.addEventListener('keydown', (event) => {
                if (event.key === 'Enter' && !event.shiftKey) {
                    event.preventDefault();
                    this.sendUserMessage();
                }
            });
        }
    }

    async startDebate() {
        this.elements.startButton.disabled = true;
        try {
            const response = await fetch(`/api/debates/${this.debate.id}/`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': this.csrfToken },
                body: JSON.stringify({ action: 'start' }),
            });
            if (!response.ok) throw new Error('Failed to start debate on server.');
            this.debate.status = 'active';
            this.updateUIAfterStart();
            this.startTimers();
        } catch (error) {
            this.elements.startButton.disabled = false;
        }
    }

    async sendUserMessage() {
        const content = this.elements.messageInput.value.trim();
        if (!content || this.elements.sendButton.disabled) return;

        this.elements.sendButton.disabled = true;
        this.elements.messageInput.value = '';
        this.addMessageToUI({ sender: 'user', content });
        this.showTypingIndicator();
        this.stopReplyTimer();

        try {
            await fetch(`/api/debates/${this.debate.id}/messages/`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': this.csrfToken },
                body: JSON.stringify({ content: content, sender: 'user' }),
            });

            const aiResponse = await fetch(`/api/debates/${this.debate.id}/ai-response/`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': this.csrfToken },
                body: JSON.stringify({ user_message: content }),
            });
            if (!aiResponse.ok) throw new Error('Failed to get AI response.');

            const aiData = await aiResponse.json();
            this.hideTypingIndicator();
            this.addMessageToUI(aiData.message);
            
            this.elements.sendButton.disabled = false;
            this.startReplyTimer();

        } catch (error) {
            this.hideTypingIndicator();
            this.addMessageToUI({ sender: 'system', content: 'An error occurred. Please try again.' });
            this.elements.sendButton.disabled = false;
        }
    }
    
    giveUp() {
        if (window.confirm("Are you sure you want to give up? The AI will win this round.")) {
            this.endDebate('ai');
        }
    }

    async endDebate(winner) {
        this.stopTimers();
        this.elements.messageInput.disabled = true;
        this.elements.sendButton.disabled = true;
        this.elements.giveUpButton.disabled = true;
        
        await fetch(`/api/debates/${this.debate.id}/`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': this.csrfToken },
            body: JSON.stringify({ action: 'end', winner: winner }),
        });

        if (this.isAuthenticated) {
            // If user is logged in, redirect to dashboard
            alert(`Debate Over! Winner: ${winner.toUpperCase()}`);
            window.location.href = '/dashboard/';
        } else {
            // If user is a guest, show the trial ended modal
            if (this.elements.guestModal) {
                this.elements.guestModal.classList.remove('hidden');
            }
        }
    }

    //TIMER MANAGEMENT
    startTimers() {
        this.mainTimerInterval = setInterval(() => this.updateMainTimer(), 1000);
        this.startReplyTimer();
    }
    stopTimers() {
        clearInterval(this.mainTimerInterval);
        clearInterval(this.replyTimerInterval);
    }
    startReplyTimer() {
        this.replySeconds = this.debate.reply_time_limit;
        this.elements.replyTimerDisplay.textContent = this.replySeconds;
        clearInterval(this.replyTimerInterval);
        this.replyTimerInterval = setInterval(() => this.updateReplyTimer(), 1000);
    }
    stopReplyTimer() {
        clearInterval(this.replyTimerInterval);
    }
    updateMainTimer() {
        if (this.totalSeconds > 0) {
            this.totalSeconds--;
            const minutes = Math.floor(this.totalSeconds / 60);
            const seconds = this.totalSeconds % 60;
            this.elements.mainTimerDisplay.textContent = `${minutes}:${seconds.toString().padStart(2, '0')}`;
        } else {
            this.endDebate('user');
        }
    }
    updateReplyTimer() {
        if (this.replySeconds > 0) {
            this.replySeconds--;
            this.elements.replyTimerDisplay.textContent = this.replySeconds;
        } else {
            this.endDebate('ai');
        }
    }

    updateUIAfterStart() {
        if (this.elements.welcomeMessage) {
            this.elements.welcomeMessage.style.display = 'none';
        }
        this.elements.messageInput.disabled = false;
        this.elements.sendButton.disabled = false;
        this.elements.messageInput.placeholder = 'Type your argument here...';
    }
    addMessageToUI(message) {
        const messageElement = document.createElement('div');
        messageElement.className = `message ${message.sender}-message`;
        const avatar = message.sender === 'user' ? `<img src="/static/images/default-avatar.png" alt="You">` : `<div class="ai-avatar"><i class="fas fa-brain"></i></div>`;
        messageElement.innerHTML = `<div class="message-avatar">${avatar}</div><div class="message-content"><div class="message-header"><span class="sender-name">${message.sender === 'user' ? 'You' : 'Debato AI'}</span></div><div class="message-text">${message.content}</div></div>`;
        this.elements.messagesContainer.appendChild(messageElement);
        this.elements.messagesContainer.scrollTop = this.elements.messagesContainer.scrollHeight;
    }
    showTypingIndicator() {
        if (!this.elements.typingIndicator) {
            this.elements.typingIndicator = document.createElement('div');
            this.elements.typingIndicator.className = 'message ai-message';
            this.elements.typingIndicator.innerHTML = `<div class="message-avatar"><div class="ai-avatar"><i class="fas fa-brain"></i></div></div><div class="message-content"><span class="typing-text">AI is thinking...</span></div>`;
            this.elements.messagesContainer.appendChild(this.elements.typingIndicator);
        }
        this.elements.typingIndicator.style.display = 'flex';
        this.elements.messagesContainer.scrollTop = this.elements.messagesContainer.scrollHeight;
    }
    hideTypingIndicator() {
        if (this.elements.typingIndicator) {
            this.elements.typingIndicator.style.display = 'none';
        }
    }
}
document.addEventListener('DOMContentLoaded', () => {
    new DebateRoom();
});