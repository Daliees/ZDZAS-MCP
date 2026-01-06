import { LightningElement, track } from 'lwc';
import { ShowToastEvent } from 'lightning/platformShowToastEvent';
import sendMessage from '@salesforce/apex/ZASChatController.sendMessage';

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
        this.addSystemMessage('💬 ZAS Chat Assistant gestart. Stel gerust uw vraag!');
    }

    get hasError() {
        return this.errorMessage && this.errorMessage.length > 0;
    }

    get hasMessages() {
        return this.messages && this.messages.length > 0;
    }

    get sendButtonDisabled() {
        return this.isLoading || !this.inputMessage.trim();
    }

    generateUUID() {
        return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
            const r = Math.random() * 16 | 0;
            const v = c === 'x' ? r : (r & 0x3 | 0x8);
            return v.toString(16);
        });
    }

    addSystemMessage(text) {
        const html = this.markdownToHtml(text);
        this.messages = [...this.messages, {
            id: Date.now(),
            text: text,
            html: html,
            isUser: false,
            isSystem: true,
            cssClass: 'message system',
            timestamp: new Date().toLocaleTimeString('nl-NL', {
                hour: '2-digit',
                minute: '2-digit'
            })
        }];
        this.scrollToBottom();
    }

    addUserMessage(text) {
        const html = this.markdownToHtml(text);
        this.messages = [...this.messages, {
            id: Date.now(),
            text: text,
            html: html,
            isUser: true,
            isSystem: false,
            cssClass: 'message user',
            timestamp: new Date().toLocaleTimeString('nl-NL', {
                hour: '2-digit',
                minute: '2-digit'
            })
        }];
        this.scrollToBottom();
    }

    addAssistantMessage(text) {
        const html = this.markdownToHtml(text);
        this.messages = [...this.messages, {
            id: Date.now(),
            text: text,
            html: html,
            isUser: false,
            isSystem: false,
            cssClass: 'message assistant',
            timestamp: new Date().toLocaleTimeString('nl-NL', {
                hour: '2-digit',
                minute: '2-digit'
            })
        }];
        this.scrollToBottom();
    }

    updateLastAssistantMessage(text) {
        if (this.messages.length > 0) {
            const lastMessage = this.messages[this.messages.length - 1];
            if (lastMessage && !lastMessage.isUser && !lastMessage.isSystem) {
                lastMessage.text = text;
                lastMessage.html = this.markdownToHtml(text);
                this.messages = [...this.messages];
                this.scrollToBottom();
            }
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
        this.errorMessage = '';
        this.addUserMessage(message);
        this.inputMessage = '';
        this.isTyping = true;

        try {
            // Call Apex controller which handles the HTTP request
            const result = await sendMessage({
                message: message,
                conversationId: this.conversationId
            });

            const data = JSON.parse(result);

            if (data.conversationId) {
                this.conversationId = data.conversationId;
            }

            if (data.reply) {
                this.simulateStreaming(data.reply);
            } else {
                throw new Error('No reply received from the API');
            }

        } catch (error) {
            console.error('Chat error:', error);
            this.errorMessage = `Error: ${error.message}`;
            this.addSystemMessage('❌ ' + this.errorMessage);
        } finally {
            this.isLoading = false;
            this.isTyping = false;
        }
    }

    simulateStreaming(text) {
        // Add an empty assistant message first
        this.addAssistantMessage('');

        // Split text into words for streaming effect
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
        }, 30);
    }

    handleReset() {
        if (!confirm('Weet u zeker dat u het gesprek wilt resetten?')) {
            return;
        }

        try {
            this.conversationId = this.generateUUID();
            this.messages = [];
            this.errorMessage = '';
            this.addSystemMessage('🔄 Gesprek gereset. Begin een nieuwe conversatie!');

            this.dispatchEvent(
                new ShowToastEvent({
                    title: 'Succes',
                    message: 'Gesprek succesvol gereset',
                    variant: 'success',
                })
            );
        } catch (error) {
            console.error('Error resetting conversation:', error);
            this.dispatchEvent(
                new ShowToastEvent({
                    title: 'Fout',
                    message: 'Fout bij het resetten van het gesprek',
                    variant: 'error',
                })
            );
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

    // Minimal Markdown -> HTML converter for bold, italics, code and links.
    // Output is rendered via lightning-formatted-rich-text, which sanitizes HTML.
    markdownToHtml(md) {
        if (!md) {
            return '';
        }
        let html = md;
        // Escape HTML basic characters first to avoid injection
        html = html
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;');
        // Code blocks ```code```
        html = html.replace(/```([\s\S]*?)```/g, (m, p1) => {
            return `<pre><code>${p1.replace(/\n/g, '\n')}</code></pre>`;
        });
        // Inline code `code`
        html = html.replace(/`([^`]+)`/g, '<code>$1</code>');
        // Bold **text**
        html = html.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
        // Italic _text_ or *text*
        html = html.replace(/(?:^|\W)_(.*?)_(?=\W|$)/g, (m, p1) => m.replace(`_${p1}_`, `<em>${p1}</em>`));
        html = html.replace(/\*(.*?)\*/g, '<em>$1</em>');
        // Links [text](url)
        html = html.replace(/\[([^\]]+)\]\((https?:[^\)]+)\)/g, '<a href="$2" target="_blank">$1</a>');
        // Simple headers #, ##, ###
        html = html.replace(/^###\s+(.*)$/gm, '<h3>$1</h3>');
        html = html.replace(/^##\s+(.*)$/gm, '<h2>$1</h2>');
        html = html.replace(/^#\s+(.*)$/gm, '<h1>$1</h1>');
        // Line breaks: double newline -> paragraph
        html = html.replace(/\r\n/g, '\n');
        html = html.replace(/\n\n+/g, '</p><p>');
        html = `<p>${html}</p>`;
        // Single newline -> <br/>
        html = html.replace(/\n/g, '<br/>');
        return html;
    }
}
