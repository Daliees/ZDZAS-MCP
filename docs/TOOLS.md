# Tools Reference

Complete reference for all MCP tools exposed to the Zendesk AI Agent.

## General Tools

### `ping`
**Description**: Test if the MCP-server is active  
**Parameters**: None  
**Returns**: Server status

### `tickets_export_csv`
**Description**: Export tickets to CSV file  
**Parameters**: 
- Search query parameters
**Returns**: CSV file path

### `tickets_search`
**Description**: Advanced searches in Zendesk  
**Parameters**:
- Query string
- Filter options
**Returns**: List of matching tickets

### `ticket_get`
**Description**: Retrieve ticket details  
**Parameters**:
- `ticket_id`: Ticket ID
**Returns**: Full ticket information

### `ticket_comments`
**Description**: Retrieve all comments on a ticket  
**Parameters**:
- `ticket_id`: Ticket ID
**Returns**: List of comments

### `ticket_add_internal_note`
**Description**: Add internal note to a ticket  
**Parameters**:
- `ticket_id`: Ticket ID
- `note`: Note content
**Returns**: Success status

### `tickets_tag_stats`
**Description**: Analyze tag statistics  
**Parameters**: None  
**Returns**: Tag frequency analysis

## Analysis & AI Tools

### `ticket_cluster_topics`
**Description**: Cluster tickets by topic using AI  
**Parameters**:
- `ticket_ids`: List of ticket IDs
**Returns**: Topic clusters

### `ticket_categorize`
**Description**: Automatically categorize tickets  
**Parameters**:
- `ticket_id`: Ticket ID
**Returns**: Category assignment

### `ticket_generate_draft`
**Description**: Generate draft responses via AI  
**Parameters**:
- `ticket_id`: Ticket ID
- Context information
**Returns**: Draft response text

### `ticket_solution_rate`
**Description**: Calculate solution types and success rates  
**Parameters**:
- Date range
**Returns**: Solution metrics

### `tickets_analyze`
**Description**: End-to-end ticket analysis  
**Parameters**:
- Analysis parameters
**Returns**: Comprehensive analysis report

## Knowledge Base Tools

### `kb_search_articles`
**Description**: Search articles in Zendesk Guide  
**Parameters**:
- `query`: Search query
**Returns**: Matching articles

### `kb_generate_draft`
**Description**: Generate new KB article content  
**Parameters**:
- Topic
- Context
**Returns**: Draft article content

### `kb_create_draft_article`
**Description**: Create draft articles in a section  
**Parameters**:
- `section_id`: Section ID
- `title`: Article title
- `body`: Article body
**Returns**: Created article ID

### `kb_list_permissions_and_segments`
**Description**: Retrieve access and permission groups  
**Parameters**: None  
**Returns**: Permissions and segments

## Jira Tools

### `jira_get_issue`
**Description**: Retrieve status, comments & updates from Jira issues  
**Parameters**:
- `issue_key`: Jira issue key (e.g., PROJ-123)
**Returns**: Issue details including:
  - Status
  - Comments
  - Developer notes
  - Updates

**Use cases**:
- Support ticket is "parked" → retrieve real-time developer updates
- Jira issue contains latest error analysis → show summary to agent

## Confluence Tools

### `confluence_search_pages`
**Description**: Search product documentation and guides  
**Parameters**:
- `query`: Search query
**Returns**: Matching Confluence pages

### `confluence_get_page`
**Description**: Retrieve full page content  
**Parameters**:
- `page_id`: Confluence page ID
**Returns**: Complete page content

**Use cases**:
- Agent needs product explanation
- Ticket contains error message → search directly in Confluence documentation
