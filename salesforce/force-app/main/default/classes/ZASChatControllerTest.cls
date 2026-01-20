/**
 * Test class for ZASChatController
 * 
 * Tests the Apex controller that handles communication with the ZAS Chat API
 */
@isTest
private class ZASChatControllerTest {
    
    /**
     * Mock class for HTTP callouts
     */
    private class MockHttpResponse implements HttpCalloutMock {
        private Integer statusCode;
        private String body;
        
        public MockHttpResponse(Integer statusCode, String body) {
            this.statusCode = statusCode;
            this.body = body;
        }
        
        public HTTPResponse respond(HTTPRequest req) {
            HttpResponse res = new HttpResponse();
            res.setHeader('Content-Type', 'application/json');
            res.setStatusCode(this.statusCode);
            res.setBody(this.body);
            return res;
        }
    }
    
    /**
     * Test successful message send
     */
    @isTest
    static void testSendMessageSuccess() {
        // Prepare mock response
        Map<String, Object> mockResponse = new Map<String, Object>{
            'reply' => 'Test response from ZAS',
            'conversationId' => 'test-conv-123'
        };
        
        Test.setMock(HttpCalloutMock.class, 
            new MockHttpResponse(200, JSON.serialize(mockResponse)));
        
        Test.startTest();
        String result = ZASChatController.sendMessage('Test message', 'test-conv-123');
        Test.stopTest();
        
        // Verify response
        System.assertNotEquals(null, result, 'Result should not be null');
        Map<String, Object> resultMap = (Map<String, Object>) JSON.deserializeUntyped(result);
        System.assertEquals('Test response from ZAS', resultMap.get('reply'), 'Reply should match');
    }
    
    /**
     * Test message send with empty message
     */
    @isTest
    static void testSendMessageEmptyMessage() {
        Test.startTest();
        try {
            ZASChatController.sendMessage('', 'test-conv-123');
            System.assert(false, 'Should have thrown exception');
        } catch (AuraHandledException e) {
            System.assert(e.getMessage().contains('empty'), 'Error message should mention empty');
        }
        Test.stopTest();
    }
    
    /**
     * Test message send with API error
     */
    @isTest
    static void testSendMessageAPIError() {
        // Prepare mock error response
        Test.setMock(HttpCalloutMock.class, 
            new MockHttpResponse(500, '{"error": "Internal server error"}'));
        
        Test.startTest();
        try {
            ZASChatController.sendMessage('Test message', 'test-conv-123');
            System.assert(false, 'Should have thrown exception');
        } catch (AuraHandledException e) {
            System.assert(e.getMessage().contains('Fout'), 'Error message should be in Dutch');
        }
        Test.stopTest();
    }
    
    /**
     * Test successful conversation reset
     */
    @isTest
    static void testResetConversationSuccess() {
        // Prepare mock response
        Map<String, Object> mockResponse = new Map<String, Object>{
            'status' => 'ok'
        };
        
        Test.setMock(HttpCalloutMock.class, 
            new MockHttpResponse(200, JSON.serialize(mockResponse)));
        
        Test.startTest();
        String result = ZASChatController.resetConversation('test-conv-123');
        Test.stopTest();
        
        // Verify response
        System.assertEquals('OK', result, 'Result should be OK');
    }
    
    /**
     * Test reset with empty conversation ID
     */
    @isTest
    static void testResetConversationEmptyId() {
        Test.startTest();
        String result = ZASChatController.resetConversation('');
        Test.stopTest();
        
        // Should return OK without making callout
        System.assertEquals('OK', result, 'Should return OK for empty ID');
    }
    
    /**
     * Test reset with API error
     */
    @isTest
    static void testResetConversationAPIError() {
        // Prepare mock error response
        Test.setMock(HttpCalloutMock.class, 
            new MockHttpResponse(500, '{"error": "Internal server error"}'));
        
        Test.startTest();
        try {
            ZASChatController.resetConversation('test-conv-123');
            System.assert(false, 'Should have thrown exception');
        } catch (AuraHandledException e) {
            System.assert(e.getMessage().contains('Fout'), 'Error message should be in Dutch');
        }
        Test.stopTest();
    }
    
    /**
     * Test connection test method
     */
    @isTest
    static void testTestConnection() {
        // Prepare mock response
        Map<String, Object> mockResponse = new Map<String, Object>{
            'reply' => 'pong',
            'conversationId' => 'test-conv'
        };
        
        Test.setMock(HttpCalloutMock.class, 
            new MockHttpResponse(200, JSON.serialize(mockResponse)));
        
        Test.startTest();
        String result = ZASChatController.testConnection();
        Test.stopTest();
        
        System.assertNotEquals(null, result, 'Result should not be null');
    }
}
