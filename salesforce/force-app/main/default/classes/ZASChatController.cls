/**
 * ZASChatController
 * 
 * Apex REST controller that acts as a proxy between the Lightning Web Component
 * and the ZAS Chat API endpoint. Handles communication with the external chat service
 * and manages conversation sessions.
 * 
 * @author ZAS Development Team
 * @version 1.0
 */
public with sharing class ZASChatController {
    
    // API endpoint - should be configured via Custom Settings or Custom Metadata
    private static final String API_ENDPOINT = getAPIEndpoint();
    private static final Integer TIMEOUT = 60000; // 60 seconds
    
    /**
     * Get API endpoint from Custom Metadata or fallback to default
     * In production, this should be configured via Custom Settings or Custom Metadata
     */
    private static String getAPIEndpoint() {
        // First, try to get from Custom Metadata (recommended approach)
        try {
            // ZAS_Chat_Config__mdt is a custom metadata type you should create
            // For now, we'll use a fallback
            return 'https://your-domain.ngrok-free.app/chat';
        } catch (Exception e) {
            // Fallback to environment variable or default
            return 'http://127.0.0.1:9000/chat';
        }
    }
    
    /**
     * Send a message to the ZAS Chat API
     * 
     * @param message The user's message text
     * @param conversationId The conversation ID for maintaining context
     * @return String JSON response from the API
     */
    @AuraEnabled
    public static String sendMessage(String message, String conversationId) {
        try {
            // Validate inputs
            if (String.isBlank(message)) {
                throw new IllegalArgumentException('Message cannot be empty');
            }
            
            // Prepare request payload
            Map<String, Object> requestBody = new Map<String, Object>{
                'message' => message,
                'conversationId' => conversationId
            };
            
            // Make HTTP callout
            HttpRequest req = new HttpRequest();
            req.setEndpoint(API_ENDPOINT);
            req.setMethod('POST');
            req.setHeader('Content-Type', 'application/json');
            req.setHeader('Accept', 'application/json');
            
            // Add session ID as header for better tracking
            if (String.isNotBlank(conversationId)) {
                req.setHeader('X-Session-Id', conversationId);
            }
            
            // Add tenant context if available
            String tenantId = getTenantId();
            if (String.isNotBlank(tenantId)) {
                req.setHeader('X-ZAS-Tenant-Id', tenantId);
            }
            
            req.setBody(JSON.serialize(requestBody));
            req.setTimeout(TIMEOUT);
            
            Http http = new Http();
            HttpResponse res = http.send(req);
            
            // Handle response
            if (res.getStatusCode() == 200) {
                return res.getBody();
            } else {
                throw new CalloutException(
                    'API returned error: ' + res.getStatusCode() + ' - ' + res.getStatus()
                );
            }
            
        } catch (Exception e) {
            System.debug(LoggingLevel.ERROR, 'Error in sendMessage: ' + e.getMessage());
            System.debug(LoggingLevel.ERROR, 'Stack trace: ' + e.getStackTraceString());
            throw new AuraHandledException('Fout bij het verzenden van bericht: ' + e.getMessage());
        }
    }
    
    /**
     * Reset a conversation by its ID
     * 
     * @param conversationId The conversation ID to reset
     * @return String Success message
     */
    @AuraEnabled
    public static String resetConversation(String conversationId) {
        try {
            if (String.isBlank(conversationId)) {
                return 'OK'; // Nothing to reset
            }
            
            // Prepare request payload
            Map<String, Object> requestBody = new Map<String, Object>{
                'conversationId' => conversationId
            };
            
            // Make HTTP callout to reset endpoint
            String resetEndpoint = API_ENDPOINT.replace('/chat', '/reset');
            
            HttpRequest req = new HttpRequest();
            req.setEndpoint(resetEndpoint);
            req.setMethod('POST');
            req.setHeader('Content-Type', 'application/json');
            req.setHeader('X-Session-Id', conversationId);
            req.setBody(JSON.serialize(requestBody));
            req.setTimeout(TIMEOUT);
            
            Http http = new Http();
            HttpResponse res = http.send(req);
            
            if (res.getStatusCode() == 200) {
                return 'OK';
            } else {
                throw new CalloutException(
                    'Reset API returned error: ' + res.getStatusCode()
                );
            }
            
        } catch (Exception e) {
            System.debug(LoggingLevel.ERROR, 'Error in resetConversation: ' + e.getMessage());
            throw new AuraHandledException('Fout bij het resetten van gesprek: ' + e.getMessage());
        }
    }
    
    /**
     * Get tenant ID from current org/user context
     * Can be customized based on your multi-tenant setup
     */
    private static String getTenantId() {
        // This can be customized to return:
        // - Organization ID
        // - Custom field from User
        // - Custom Setting value
        // For now, return the org ID
        return UserInfo.getOrganizationId();
    }
    
    /**
     * Test method to verify API connectivity
     * This can be called from Setup or as a health check
     */
    @AuraEnabled
    public static String testConnection() {
        try {
            return sendMessage('ping', null);
        } catch (Exception e) {
            return 'Connection failed: ' + e.getMessage();
        }
    }
}
