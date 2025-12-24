import { LightningElement, track } from 'lwc';
import sendMessage from '@salesforce/apex/ZASChatController.sendMessage';
import resetConversation from '@salesforce/apex/ZASChatController.resetConversation';
import { ShowToastEvent } from 'lightning/platformShowToastEvent';

export default class ZasChatUtility extends LightningElement {
    @track messages = [];
    @track inputMessage = '';
    @track isTyping = false;
    @track conversationId = null;
    @track isLoading = false;
    @track errorMessage = '';

    connectedCallback() {
        // Generate a unique session ID for this chat instance
        this.conversationId = this.generateUUID();
        this.addSystemMessage('ZAS Chat Assistant gestart. Stel gerust uw vraag!');
    }

    generateUUID() {
        return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
            const r = Math.random() * 16 | 0;
            const v = c === 'x' ? r : (r & 0x3 | 0x8);
            return v.toString(16);
        });
    }

    addSystemMessage(text) {
        this.messages = [...this.messages, {
            id: Date.now(),
            text: text,
            isUser: false,
            isSystem: true,
            timestamp: new Date().toLocaleTimeString('nl-NL', { 
                hour: '2-digit', 
                minute: '2-digit' 
            })
        }];
        this.scrollToBottom();
    }

    addUserMessage(text) {
        this.messages = [...this.messages, {
            id: Date.now(),
            text: text,
            isUser: true,
            isSystem: false,
            timestamp: new Date().toLocaleTimeString('nl-NL', { 
                hour: '2-digit', 
                minute: '2-digit' 
            })
        }];
        this.scrollToBottom();
    }

    addAssistantMessage(text) {
        this.messages = [...this.messages, {
            id: Date.now(),
            text: text,
            isUser: false,
            isSystem: false,
            timestamp: new Date().toLocaleTimeString('nl-NL', { 
                hour: '2-digit', 
                minute: '2-digit' 
            })
        }];
        this.scrollToBottom();
    }

    updateLastAssistantMessage(text) {
        const lastMessage = this.messages[this.messages.length - 1];
        if (lastMessage && !lastMessage.isUser && !lastMessage.isSystem) {
            lastMessage.text = text;
            this.messages = [...this.messages];
            this.scrollToBottom();
        }
    }

    handleInputChange(event) {
        this.inputMessage = event.target.value;
    }

    handleKeyPress(event) {
        if (event.key === 'Enter' && !event.shiftKey) {
            event.preventDefault();
            this.handleSend();
        }
    }

    async handleSend() {
        const message = this.inputMessage.trim();
        
        if (!message) {
            return;
        }

        // Disable input and show user message
        this.isLoading = true;
        this.addUserMessage(message);
        this.inputMessage = '';
        this.errorMessage = '';

        // Show typing indicator
        this.isTyping = true;

        try {
            // Call Apex controller
            const response = await sendMessage({
                message: message,
                conversationId: this.conversationId
            });

            // Hide typing indicator
            this.isTyping = false;

            // Parse response
            const result = JSON.parse(response);
            
            if (result.reply) {
                // Update conversation ID if new one was generated
                if (result.conversationId) {
                    this.conversationId = result.conversationId;
                }

                // Simulate streaming effect by showing reply progressively
                this.simulateStreaming(result.reply);
            } else {
                throw new Error('Geen antwoord ontvangen van de server');
            }

        } catch (error) {
            this.isTyping = false;
            console.error('Error sending message:', error);
            this.errorMessage = 'Er is een fout opgetreden bij het verzenden van het bericht: ' + 
                (error.body?.message || error.message);
            
            this.showToast('Fout', this.errorMessage, 'error');
        } finally {
            this.isLoading = false;
        }
    }

    simulateStreaming(text) {
        // Add an empty assistant message first
        this.addAssistantMessage('');
        
        // Split text into chunks for streaming effect
        const words = text.split(' ');
        let currentText = '';
        let wordIndex = 0;

        const streamInterval = setInterval(() => {
            if (wordIndex < words.length) {
                currentText += (wordIndex > 0 ? ' ' : '') + words[wordIndex];
                this.updateLastAssistantMessage(currentText);
                wordIndex++;
            } else {
                clearInterval(streamInterval);
            }
        }, 30); // Adjust speed of streaming here (ms per word)
    }

    async handleReset() {
        if (!confirm('Weet u zeker dat u het gesprek wilt resetten?')) {
            return;
        }

        try {
            await resetConversation({
                conversationId: this.conversationId
            });

            // Clear messages and reset state
            this.messages = [];
            this.conversationId = this.generateUUID();
            this.errorMessage = '';
            this.addSystemMessage('Gesprek gereset. Begin een nieuwe conversatie!');
            
            this.showToast('Succes', 'Gesprek succesvol gereset', 'success');
        } catch (error) {
            console.error('Error resetting conversation:', error);
            this.showToast('Fout', 'Fout bij het resetten van het gesprek', 'error');
        }
    }

    scrollToBottom() {
        // Use setTimeout to ensure DOM is updated
        setTimeout(() => {
            const container = this.template.querySelector('.messages-container');
            if (container) {
                container.scrollTop = container.scrollHeight;
            }
        }, 0);
    }

    showToast(title, message, variant) {
        const event = new ShowToastEvent({
            title: title,
            message: message,
            variant: variant,
        });
        this.dispatchEvent(event);
    }

    get hasError() {
        return this.errorMessage !== '';
    }

    get hasMessages() {
        return this.messages.length > 0;
    }

    get sendButtonDisabled() {
        return this.isLoading || !this.inputMessage.trim();
    }
}
