# Plan: Production-Ready ZDZAS-MCP Refactoring & Testing

This plan refactors your MCP project into a maintainable, tested, production-ready codebase. It addresses code organization, implements testing with CI/CD, establishes code standards, consolidates documentation, and optimizes the MCP architecture.

## Steps

### 1. Security & Dependencies Cleanup

Remove hardcoded API keys from `ecosystem.config.js`, create `.env.example` template, align `pyproject.toml` with `requirements.txt`, delete deprecated `zendesk_mcp_server/server.py` and unused `server_wrapper.py`

**Actions:**
- Remove hardcoded OpenAI API key from `ecosystem.config.js`
- Create `.env.example` with all required environment variables
- Sync dependencies between `pyproject.toml` and `requirements.txt` (add missing zenpy, remove conflicts)
- Delete `src/zendesk_mcp_server/` directory (deprecated stdio-based server)
- Delete `server_wrapper.py` (unused Flask wrapper)
- Add `.env` to `.gitignore` if not already present

### 2. Code Organization & Structure

Delete empty `/src/zas/*` folders, consolidate root `tools_*.py` into `src/zas/tools/` directory with proper `__init__.py`, move `api/` contents to `src/zas/api/`, update all imports, remove `get-pip.py` and test artifacts

**Actions:**
- Remove empty directories: `src/zas/agents/`, `src/zas/api/`, `src/zas/core/`, `src/zas/dashboard/`, `src/zas/services/`, `src/zas/tools/`
- Create new structure:
  ```
  src/zas/
    tools/
      __init__.py
      ticket.py (from tools_ticket.py)
      kb.py (from tools_kb.py)
      jira.py (from tools_jira.py)
      confluence.py (from tools_confluence.py)
      reporting.py (from tools_reporting.py)
      salesforce.py (from tools_salesforce.py)
      general.py (from tools_general.py)
      admin.py (from tools_admin.py)
    api/
      __init__.py
      routes.py (from api/routes.py)
      schemas.py (from api/schemas.py)
      middleware.py (from api/middleware.py)
      logging_utils.py (from api/logging_utils.py)
    core/
      __init__.py
      config.py (new - centralized configuration)
      database.py (from db.py)
      helpers.py (from core.py)
  ```
- Update imports in `mcp_proxy.py`, `chat_api.py`, `zas_agent.py`, `start_all.py`
- Delete: `get-pip.py`, `knowledge_concept_semantic_search_foutmelding.txt`, old root files
- Keep at root: `app.py`, `start_all.py`, `start_mcp.sh` (entry points)
- Configure FastAPI apps with comprehensive OpenAPI metadata:
  ```python
  # In chat_api.py and dashboard/app.py
  app = FastAPI(
      title="ZDZAS-MCP API",
      description="AI-powered support assistant with Zendesk/Jira integration",
      version="1.0.0",
      docs_url="/docs",
      redoc_url="/redoc",
      openapi_tags=[
          {"name": "chat", "description": "Chat and conversation endpoints"},
          {"name": "admin", "description": "Administrative operations"},
      ]
  )
  ```

### 3. Code Quality Standards

Add `ruff` formatter/linter configuration to `pyproject.toml`, setup `mypy` for type checking, create `.pre-commit-config.yaml` with ruff/mypy hooks, standardize all code to English (remove Dutch strings/comments), add consistent type hints replacing `Any`, organize imports with `isort` profile

**Actions:**
- Add to `requirements.txt`: `ruff`, `mypy`, `pre-commit`, `types-requests`
- Configure `ruff` in `pyproject.toml`:
  ```toml
  [tool.ruff]
  line-length = 100
  target-version = "py312"
  
  [tool.ruff.lint]
  select = ["E", "F", "I", "N", "W", "UP", "B", "A", "C4", "T20"]
  ignore = ["E501"]
  
  [tool.ruff.format]
  quote-style = "double"
  indent-style = "space"
  ```
- Configure `mypy` in `pyproject.toml`:
  ```toml
  [tool.mypy]
  python_version = "3.12"
  warn_return_any = true
  warn_unused_configs = true
  disallow_untyped_defs = false
  disallow_incomplete_defs = true
  check_untyped_defs = true
  ```
- Create `.pre-commit-config.yaml` with hooks for ruff and mypy
- Replace Dutch strings:
  - `"Ontbrekende verplichte Zendesk env vars"` → `"Missing required Zendesk environment variables"`
  - All Dutch comments to English
- Add type hints to functions currently using `Any`
- Add `from __future__ import annotations` to all Python files

### 4. Testing Infrastructure

Add `pytest`, `pytest-asyncio`, `pytest-cov`, `httpx` for testing dependencies; create `tests/` structure with `test_tools/`, `test_api/`, `test_core/`, `test_integration/`; write unit tests for all MCP tools with mocked external APIs; add FastAPI endpoint tests; create GitHub Actions workflow in `.github/workflows/test.yml` running pytest with coverage reports

**Actions:**
- Add to `requirements.txt`:
  ```
  pytest==8.0.0
  pytest-asyncio==0.23.3
  pytest-cov==4.1.0
  pytest-mock==3.12.0
  httpx==0.26.0
  responses==0.25.0
  ```
- Configure pytest in `pyproject.toml`:
  ```toml
  [tool.pytest.ini_options]
  testpaths = ["tests"]
  python_files = ["test_*.py"]
  python_classes = ["Test*"]
  python_functions = ["test_*"]
  addopts = "--cov=src --cov-report=html --cov-report=term-missing --cov-fail-under=80"
  asyncio_mode = "auto"
  ```
- Create test structure:
  ```
  tests/
    __init__.py
    conftest.py (fixtures for DB, API client, mocked services)
    test_tools/
      __init__.py
      test_ticket_tools.py
      test_kb_tools.py
      test_jira_tools.py
      test_confluence_tools.py
      test_salesforce_tools.py
      test_general_tools.py
    test_api/
      __init__.py
      test_routes.py (chat endpoint, feedback, reset)
      test_middleware.py
      test_schemas.py
    test_core/
      __init__.py
      test_database.py
      test_helpers.py
      test_config.py
    test_integration/
      __init__.py
      test_mcp_workflow.py (full MCP request/response)
      test_agent_workflow.py
  ```
- Write tests for each tool using `responses` or `unittest.mock` for API mocking
- Add OpenAPI schema validation tests:
  ```python
  # tests/test_api/test_openapi.py
  def test_openapi_schema_valid():
      """Ensure OpenAPI schema is valid and complete"""
      response = client.get("/openapi.json")
      assert response.status_code == 200
      schema = response.json()
      assert "openapi" in schema
      assert "paths" in schema
      # Validate all endpoints are documented
  
  def test_all_endpoints_have_examples():
      """Ensure all endpoints have request/response examples"""
      # Validate example payloads exist
  ```
- Create GitHub Actions workflow:
  ```yaml
  name: Tests
  
  on:
    push:
      branches: [main, develop]
    pull_request:
      branches: [main, develop]
  
  jobs:
    test:
      runs-on: ubuntu-latest
      strategy:
        matrix:
          python-version: ["3.12"]
      
      steps:
        - uses: actions/checkout@v4
        - name: Set up Python
          uses: actions/setup-python@v5
          with:
            python-version: ${{ matrix.python-version }}
        - name: Install dependencies
          run: |
            python -m pip install --upgrade pip
            pip install -r requirements.txt
        - name: Run tests
          run: pytest
        - name: Upload coverage
          uses: codecov/codecov-action@v4
          if: matrix.python-version == '3.12'
  ```

### 5. Documentation Consolidation

Merge Salesforce docs into single `salesforce/README.md` with sections from `QUICKSTART.md`, `TESTING.md`, `PRODUCTION.md`; create `docs/` folder for `ARCHITECTURE.md` (extracted from README), DEPLOYMENT.md, CONTRIBUTING.md; update main `README.md` to be concise with links to docs; delete redundant files like `FEATURES.md`, `INDEX.md`, `IMPLEMENTATION_SUMMARY.md`

**Actions:**
- Create consolidated `salesforce/README.md`:
  - Overview section
  - Quick Start (from QUICKSTART.md)
  - Features (from FEATURES.md)
  - Testing (from TESTING.md)
  - Production Deployment (from PRODUCTION.md)
  - Implementation Details (from IMPLEMENTATION_SUMMARY.md)
  - Keep existing technical details
- Delete Salesforce docs: `QUICKSTART.md`, `TESTING.md`, `PRODUCTION.md`, `FEATURES.md`, `INDEX.md`, `IMPLEMENTATION_SUMMARY.md`, `PACKAGE.md`, `PROJECT.md`
- Create `docs/` directory:
  - `ARCHITECTURE.md` - System architecture, component interaction, MCP design decisions
  - `DEPLOYMENT.md` - Docker, PM2, Heroku, ngrok setup, environment configuration
  - `CONTRIBUTING.md` - Code standards, PR process, testing requirements, commit conventions
  - `API.md` - FastAPI endpoints, request/response schemas, authentication (supplement to Swagger)
  - `TOOLS.md` - MCP tool reference, parameters, examples
- Configure OpenAPI/Swagger documentation:
  - Chat API: Available at `http://localhost:9000/docs` (Swagger UI) and `/redoc` (ReDoc)
  - Dashboard API: Available at `http://localhost:9001/docs` and `/redoc`
  - Add comprehensive docstrings to all FastAPI endpoints
  - Use Pydantic models for automatic schema generation
  - Add example requests/responses using `openapi_examples`
  - Document authentication schemes (Bearer tokens, API keys)
  - Add response model documentation with status codes
- Update main `README.md`:
  - Brief project description (2-3 paragraphs)
  - Quick start (setup, run, test)
  - Links to detailed docs
  - License and contribution info
- Keep: `LICENSE`, `README.md`, `salesforce/README.md`

### 6. MCP Architecture Optimization

Keep HTTP server (FastMCP on port 8000) for production as it supports Salesforce webhooks and remote access; add stdio mode via `--stdio` flag for local development/testing; simplify `zas_agent.py` by reducing duplicate tool proxy wrappers using dynamic tool registration; add health check endpoint to `mcp_proxy.py`

**Actions:**
- Update `mcp_proxy.py`:
  - Add CLI argument parser for `--mode` (http/stdio)
  - Add health check endpoint: `GET /health` returning status and registered tools
  - Add metrics endpoint: `GET /metrics` for monitoring
  - Keep HTTP as default for production
- Refactor `zas_agent.py`:
  - Remove 30+ individual tool proxy functions
  - Implement dynamic tool discovery from MCP server
  - Use reflection to automatically register tools
  - Reduce from ~1000 lines to ~300 lines
- Update `start_all.py`:
  - Add environment-based mode selection
  - Add graceful shutdown handlers
  - Add startup health checks
- Document HTTP vs stdio trade-offs in `docs/ARCHITECTURE.md`:
  - HTTP: Production, multi-client, remote access, Salesforce integration
  - stdio: Local development, debugging, MCP CLI compatibility
- Add Docker health check to `Dockerfile`

### 7. Admin Dashboard & EU AI Act Compliance

Build a comprehensive web dashboard for monitoring, auditing, and managing the ZDZAS-MCP system with full transparency and compliance features required by the EU AI Act

**Actions:**
- **Database Schema Extensions** (in `src/zas/core/database.py`):
  ```python
  # New models to add:
  class ConversationLog(Base):
      """EU AI Act compliant conversation logging"""
      id: UUID
      organization_id: FK
      user_id: FK
      session_id: str
      timestamp: DateTime
      input_prompt: Text (encrypted)
      output_response: Text (encrypted)
      tool_calls: JSON (which tools were invoked)
      input_tokens: int
      output_tokens: int
      total_tokens: int
      model_used: str
      latency_ms: int
      flagged_content: bool
      flagged_reason: str (nullable)
      ip_address: str (anonymized/hashed after 30 days)
      user_agent: str
  
  class TokenUsage(Base):
      """Aggregated token usage for billing and monitoring"""
      id: int
      organization_id: FK
      user_id: FK (nullable)
      date: Date
      model: str
      input_tokens: int
      output_tokens: int
      total_tokens: int
      total_requests: int
      average_latency_ms: float
      cost_estimate: Decimal
  
  class AuditLog(Base):
      """System-level audit trail"""
      id: UUID
      timestamp: DateTime
      user_id: FK (nullable)
      action: str (CRUD operation)
      resource_type: str
      resource_id: str
      old_value: JSON (nullable)
      new_value: JSON (nullable)
      ip_address: str
      success: bool
      error_message: str (nullable)
  
  class DataRetentionPolicy(Base):
      """Configurable data retention per organization"""
      organization_id: FK
      conversation_logs_days: int (default 90, EU AI Act minimum)
      token_usage_days: int (default 365)
      audit_logs_days: int (default 730)
      anonymize_after_days: int (default 30)
  ```

- **Logging Middleware** (in `src/zas/api/middleware.py`):
  - Intercept all chat API requests/responses
  - Log to `ConversationLog` table with encryption
  - Calculate token usage using tiktoken
  - Flag potentially problematic content (profanity, PII, etc.)
  - Async logging to not block requests
  - Add request correlation IDs

- **Admin Dashboard Application** (`src/zas/dashboard/`):
  ```
  src/zas/dashboard/
    backend/
      __init__.py
      app.py (FastAPI application on port 9001)
      auth.py (admin authentication, role-based access, JWT)
      routes/
        __init__.py
        conversations.py (view, search, export conversation logs)
        analytics.py (token usage charts, cost analysis)
        organizations.py (full CRUD on organizations)
        users.py (full CRUD on users)
        audit.py (view audit trail)
        compliance.py (EU AI Act compliance reports)
        settings.py (system configuration)
      models/
        __init__.py
        responses.py (Pydantic response models)
        requests.py (Pydantic request models)
    
    frontend/  (React + Vite SPA)
      public/
        vite.svg
        favicon.ico
      src/
        assets/
          logo.svg
        components/
          layout/
            Navbar.tsx
            Sidebar.tsx
            Layout.tsx
          conversations/
            ConversationList.tsx
            ConversationDetail.tsx
            ConversationFilter.tsx
          analytics/
            TokenUsageChart.tsx
            CostAnalysisChart.tsx
            LatencyTrends.tsx
            ToolUsageStats.tsx
          organizations/
            OrganizationList.tsx
            OrganizationForm.tsx
            OrganizationStats.tsx
          users/
            UserList.tsx
            UserForm.tsx
            UserActivity.tsx
          audit/
            AuditLog.tsx
            AuditExport.tsx
          compliance/
            ComplianceReport.tsx
            DataRetentionStatus.tsx
            RightToErasure.tsx
          common/
            Table.tsx
            Chart.tsx
            Modal.tsx
            Loading.tsx
            ErrorBoundary.tsx
        pages/
          Dashboard.tsx
          Conversations.tsx
          Analytics.tsx
          Organizations.tsx
          Users.tsx
          Audit.tsx
          Compliance.tsx
          Settings.tsx
          Login.tsx
        services/
          api.ts (Axios client with interceptors)
          auth.ts (JWT token management)
          conversations.ts
          analytics.ts
          organizations.ts
          users.ts
        hooks/
          useAuth.ts
          useApi.ts
          useWebSocket.ts
        context/
          AuthContext.tsx
          ThemeContext.tsx
        utils/
          formatters.ts
          validators.ts
        types/
          index.ts (TypeScript interfaces)
        App.tsx
        main.tsx
        router.tsx
      index.html
      package.json
      vite.config.ts
      tsconfig.json
      tsconfig.node.json
      tailwind.config.js
      postcss.config.js
      .env.example
  ```

- **Dashboard Features**:
  - **Home Dashboard**:
    - Real-time metrics: active sessions, requests/min, error rate
    - Today's token usage by organization
    - Recent conversations (last 100)
    - System health status
  
  - **Conversation History** (`/conversations`):
    - Searchable/filterable table: by organization, user, date range, tool used
    - View full conversation details (input/output)
    - Export to JSON/CSV
    - Delete/anonymize conversations
    - Flag review for problematic content
  
  - **Analytics Dashboard** (`/analytics`):
    - Token usage charts: time series, by organization, by user, by model
    - Cost estimation dashboard
    - Peak usage times heatmap
    - Tool usage statistics
    - Average response latency trends
    - Export reports (PDF/Excel)
  
  - **Organization Management** (`/organizations`):
    - List all organizations with stats
    - Create/Edit/Delete organizations
    - Set token limits and rate limits
    - Configure data retention policies
    - View organization-specific analytics
  
  - **User Management** (`/users`):
    - List all users with activity stats
    - Create/Edit/Delete users
    - Assign to organizations
    - Set user roles and permissions
    - View user-specific conversation history
  
  - **Audit Trail** (`/audit`):
    - Searchable audit log of all system changes
    - Filter by user, action type, date range
    - Export audit reports
    - Immutable log entries
  
  - **EU AI Act Compliance** (`/compliance`):
    - Transparency report: all AI interactions logged
    - Data retention policy status
    - User consent tracking
    - Right to explanation: view reasoning for AI decisions
    - Right to erasure: delete user data
    - Generate compliance reports for regulators
    - Risk assessment documentation
    - Human oversight logs
  
  - **Settings** (`/settings`):
    - System configuration
    - API keys management (masked display)
    - Data retention policies
    - Backup/restore functionality
    - Email notification settings

- **EU AI Act Specific Requirements**:
  - **Transparency Obligations** (Article 13):
    - Log that user is interacting with AI system
    - Disclose when AI-generated content is used
    - Provide information about AI system capabilities and limitations
    - Dashboard shows all logged interactions
  
  - **Data Governance** (Article 10):
    - Track data quality metrics
    - Log training data sources (if applicable)
    - Document data preprocessing steps
    - Version control for models
  
  - **Record-Keeping** (Article 12):
    - Automatic logging of all AI system usage
    - Minimum 90-day retention (configurable per org)
    - Export capabilities for regulatory audits
    - Tamper-proof audit logs
  
  - **Human Oversight** (Article 14):
    - Flag system for reviewing AI decisions
    - Manual approval workflows for sensitive actions
    - Override mechanisms for AI decisions
    - Log all human interventions
  
  - **Accuracy & Robustness** (Article 15):
    - Track model performance metrics
    - Log errors and failures
    - Alert on accuracy degradation
    - Incident response documentation

- **API Endpoints** (in `src/zas/dashboard/routes/`) with OpenAPI/Swagger Documentation:
  ```python
  # All endpoints documented with:
  # - OpenAPI tags for grouping
  # - Comprehensive docstrings
  # - Pydantic request/response models
  # - Example payloads
  # - HTTP status code documentation
  
  # Analytics API (tag: "analytics")
  GET /api/analytics/tokens/summary?org_id=&start_date=&end_date=
  GET /api/analytics/tokens/by-organization
  GET /api/analytics/tokens/by-user?org_id=
  GET /api/analytics/tools/usage
  GET /api/analytics/latency/trends
  
  # Conversations API (tag: "conversations")
  GET /api/conversations?org_id=&user_id=&start_date=&end_date=&page=&limit=
  GET /api/conversations/{conversation_id}
  DELETE /api/conversations/{conversation_id}
  POST /api/conversations/{conversation_id}/anonymize
  GET /api/conversations/export?format=csv|json
  
  # Organizations API (tag: "organizations")
  GET /api/organizations
  GET /api/organizations/{org_id}
  POST /api/organizations
  PUT /api/organizations/{org_id}
  DELETE /api/organizations/{org_id}
  GET /api/organizations/{org_id}/stats
  
  # Users API (tag: "users")
  GET /api/users?org_id=
  GET /api/users/{user_id}
  POST /api/users
  PUT /api/users/{user_id}
  DELETE /api/users/{user_id}
  GET /api/users/{user_id}/activity
  
  # Audit API (tag: "audit")
  GET /api/audit?user_id=&action=&start_date=&end_date=
  GET /api/audit/export
  
  # Compliance API (tag: "compliance")
  GET /api/compliance/transparency-report?org_id=
  GET /api/compliance/data-retention-status
  POST /api/compliance/right-to-erasure
  GET /api/compliance/export-user-data?user_id=
  ```

- **OpenAPI/Swagger Implementation**:
  ```python
  # Example endpoint with full OpenAPI documentation:
  
  from fastapi import APIRouter, Query, Path, Body
  from pydantic import BaseModel, Field
  from typing import Optional
  
  router = APIRouter(prefix="/api/conversations", tags=["conversations"])
  
  class ConversationResponse(BaseModel):
      """Response model for conversation details"""
      id: str = Field(..., description="Unique conversation identifier")
      organization_id: str
      user_id: str
      timestamp: str = Field(..., description="ISO 8601 timestamp")
      input_prompt: str = Field(..., description="User's input message")
      output_response: str = Field(..., description="AI assistant's response")
      tool_calls: list[str] = Field(default=[], description="Tools invoked")
      total_tokens: int = Field(..., ge=0, description="Total tokens used")
      
      class Config:
          json_schema_extra = {
              "example": {
                  "id": "conv-123abc",
                  "organization_id": "org-456def",
                  "user_id": "user-789ghi",
                  "timestamp": "2026-01-20T10:30:00Z",
                  "input_prompt": "What is ticket #12345 about?",
                  "output_response": "Ticket #12345 is regarding...",
                  "tool_calls": ["search_ticket", "get_ticket"],
                  "total_tokens": 245
              }
          }
  
  @router.get(
      "/{conversation_id}",
      response_model=ConversationResponse,
      summary="Get conversation details",
      description="Retrieve full details of a specific conversation by ID",
      responses={
          200: {"description": "Conversation found", "model": ConversationResponse},
          404: {"description": "Conversation not found"},
          403: {"description": "Insufficient permissions"}
      }
  )
  async def get_conversation(
      conversation_id: str = Path(..., description="Conversation UUID"),
      include_metadata: bool = Query(False, description="Include system metadata")
  ) -> ConversationResponse:
      """Fetch a single conversation with optional metadata."""
      # Implementation
      pass
  ```
  
- **Swagger UI Customization**:
  - Add custom logo and branding
  - Configure default authorization (JWT bearer tokens)
  - Add "Try it out" examples for common use cases
  - Document rate limits and pagination
  - Add links to main documentation site
  - Enable CORS for API testing from different origins

- **Security & Privacy**:
  - Encrypt sensitive data at rest (conversation logs)
  - Role-based access control (super admin, org admin, viewer)
  - Audit all dashboard access
  - Implement PII detection and redaction
  - GDPR-compliant data export/deletion
  - Two-factor authentication for admin access
  - IP whitelisting for dashboard access
  - Rate limiting on dashboard API

- **Frontend Technology Stack** (React + Vite):
  - **Framework**: React 18+ with TypeScript
  - **Build Tool**: Vite 5+ for fast development and optimized builds
  - **Routing**: React Router v6
  - **State Management**: React Query (TanStack Query) for server state + Zustand for client state
  - **UI Library**: Tailwind CSS + shadcn/ui components
  - **Charts**: Recharts for visualizations (token usage, latency trends)
  - **Tables**: TanStack Table (React Table v8) for complex data tables
  - **HTTP Client**: Axios with interceptors for auth and error handling
  - **Real-time**: WebSocket connection for live updates
  - **Forms**: React Hook Form + Zod for validation
  - **Date Handling**: date-fns
  - **Icons**: Lucide React
  - **Notifications**: React Hot Toast
  
- **Frontend Package.json Dependencies**:
  ```json
  {
    "dependencies": {
      "react": "^18.2.0",
      "react-dom": "^18.2.0",
      "react-router-dom": "^6.22.0",
      "@tanstack/react-query": "^5.17.0",
      "@tanstack/react-table": "^8.11.0",
      "zustand": "^4.5.0",
      "axios": "^1.6.5",
      "recharts": "^2.10.0",
      "react-hook-form": "^7.49.0",
      "zod": "^3.22.4",
      "date-fns": "^3.3.1",
      "lucide-react": "^0.312.0",
      "react-hot-toast": "^2.4.1",
      "tailwindcss": "^3.4.1",
      "@radix-ui/react-dialog": "^1.0.5",
      "@radix-ui/react-dropdown-menu": "^2.0.6",
      "@radix-ui/react-select": "^2.0.0"
    },
    "devDependencies": {
      "@types/react": "^18.2.48",
      "@types/react-dom": "^18.2.18",
      "@vitejs/plugin-react": "^4.2.1",
      "typescript": "^5.3.3",
      "vite": "^5.0.11",
      "eslint": "^8.56.0",
      "prettier": "^3.2.4",
      "autoprefixer": "^10.4.17",
      "postcss": "^8.4.33"
    }
  }
  ```

- **Vite Configuration** (`frontend/vite.config.ts`):
  ```typescript
  import { defineConfig } from 'vite'
  import react from '@vitejs/plugin-react'
  import path from 'path'
  
  export default defineConfig({
    plugins: [react()],
    server: {
      port: 3000,
      proxy: {
        '/api': {
          target: 'http://localhost:9001',
          changeOrigin: true,
        },
        '/ws': {
          target: 'ws://localhost:9001',
          ws: true,
        },
      },
    },
    build: {
      outDir: '../backend/static',
      emptyOutDir: true,
    },
    resolve: {
      alias: {
        '@': path.resolve(__dirname, './src'),
      },
    },
  })
  ```

- **API Service Example** (`frontend/src/services/api.ts`):
  ```typescript
  import axios from 'axios'
  
  const api = axios.create({
    baseURL: '/api',
    headers: {
      'Content-Type': 'application/json',
    },
  })
  
  // Request interceptor for auth tokens
  api.interceptors.request.use(
    (config) => {
      const token = localStorage.getItem('access_token')
      if (token) {
        config.headers.Authorization = `Bearer ${token}`
      }
      return config
    },
    (error) => Promise.reject(error)
  )
  
  // Response interceptor for error handling
  api.interceptors.response.use(
    (response) => response,
    async (error) => {
      if (error.response?.status === 401) {
        // Handle token refresh or logout
        localStorage.removeItem('access_token')
        window.location.href = '/login'
      }
      return Promise.reject(error)
    }
  )
  
  export default api
  ```

- **Background Jobs** (using APScheduler or Celery):
  - Hourly: Aggregate token usage into `TokenUsage` table
  - Daily: Generate compliance reports
  - Daily: Anonymize old data per retention policy
  - Daily: Archive old logs to cold storage
  - Weekly: Calculate cost estimates
  - Monthly: Generate billing reports

- **Integration Points**:
  - Update `chat_api.py` to log all requests/responses
  - Update `zas_agent.py` to track tool invocations
  - Update `mcp_proxy.py` to expose metrics endpoint
  - Update `start_all.py` to launch both dashboard backend (port 9001) and frontend dev server (port 3000)
  - Configure FastAPI backend to serve React build in production:
    ```python
    from fastapi.staticfiles import StaticFiles
    from fastapi.responses import FileResponse
    
    # Serve React app
    app.mount("/assets", StaticFiles(directory="static/assets"), name="assets")
    
    @app.get("/{full_path:path}")
    async def serve_react_app(full_path: str):
        # Serve index.html for all non-API routes (SPA routing)
        if full_path.startswith("api/"):
            raise HTTPException(404)
        return FileResponse("static/index.html")
    ```
  - Add JWT-based authentication for dashboard API
  - Add CORS middleware for development:
    ```python
    from fastapi.middleware.cors import CORSMiddleware
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000"],  # Vite dev server
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    ```

- **Documentation**:
  - Add `docs/COMPLIANCE.md` - EU AI Act compliance guide
  - Add `docs/DASHBOARD.md` - Dashboard user guide
  - Add `docs/DATA_RETENTION.md` - Data retention and privacy policies
  - Update `docs/API.md` with dashboard API endpoints

## Further Considerations

### 1. Database Migrations

Add Alembic for SQLAlchemy migration tracking? Recommended if schema changes are frequent, otherwise document manual migration steps in deployment guide.

**Recommendation:** Add Alembic
- Create `alembic/` directory with migration scripts
- Add `alembic.ini` configuration
- Document migration workflow in `docs/DEPLOYMENT.md`
- Include initial migration capturing current schema

### 2. CI/CD Pipeline Additions

Beyond tests, add linting job, type-check job, Docker image build/push, and automatic deployment to staging environment on main branch?

**Recommendation:** Extend GitHub Actions
- Add separate jobs for:
  - Linting (ruff check)
  - Type checking (mypy)
  - Security scan (bandit, safety)
  - Docker build and push to registry
- Add deployment workflow for staging on main branch
- Add manual approval for production deployment

### 3. Code Coverage Targets

Aim for 80% coverage minimum? Focus first on critical paths (MCP tools, API endpoints) then expand to utilities and edge cases?

**Recommendation:** Phased Approach
- Phase 1: 60% overall, 90% for MCP tools
- Phase 2: 70% overall, 80% for API endpoints
- Phase 3: 80% overall, 70% for utilities
- Configure coverage thresholds in `pyproject.toml`
- Add coverage badge to README

### 4. Monorepo vs Separate Repos

Keep Salesforce code integrated or split into separate `zdzas-mcp-salesforce` repository? Current structure works well for coordinated releases, but separation improves Salesforce AppExchange packaging.

**Recommendation:** Keep Monorepo
- Easier coordinated releases
- Shared documentation context
- Simplified testing (integration tests across boundaries)
- Use `salesforce/` as clean package boundary
- Can extract later if needed for AppExchange
- Add clear package metadata and versioning

### 5. Dashboard Technology Stack

**Decision:** React SPA with Vite + FastAPI Backend

**Rationale:**
- **Rich Interactive Experience**: Complex analytics dashboards with real-time updates
- **Modern Developer Experience**: Hot module replacement, fast builds with Vite
- **Type Safety**: TypeScript throughout frontend and backend (Python type hints)
- **Component Reusability**: Build once, use everywhere
- **Better Performance**: Code splitting, lazy loading, optimized bundles
- **Real-time Updates**: WebSocket integration for live metrics
- **Mobile Responsive**: Tailwind CSS makes responsive design straightforward
- **Future-Proof**: Easy to add features like PWA, offline support

**Trade-offs Accepted:**
- Slightly more complex initial setup (worth it for long-term maintainability)
- Need to build frontend before production deployment (automated in CI/CD)
- Larger initial bundle (~200KB gzipped), but acceptable for admin dashboard

**Development Workflow:**
- Development: Run Vite dev server (port 3000) + FastAPI backend (port 9001)
- Production: Build React app into `backend/static/`, serve via FastAPI

### 6. Data Encryption Strategy

How to handle encryption of conversation logs for EU AI Act compliance?

**Recommendation:** Field-Level Encryption
- Use SQLAlchemy TypeDecorator for transparent encryption
- Encrypt `input_prompt` and `output_response` fields only
- Use Fernet (symmetric encryption) with key rotation
- Store encryption keys in environment variables or KMS
- Document key management in `docs/COMPLIANCE.md`
- Balance security with searchability (consider encrypted search solutions if needed)

### 7. Cost Tracking Accuracy

Track actual OpenAI API costs or estimate based on tokens?

**Recommendation:** Hybrid Approach
- Calculate estimates based on token counts + model pricing
- Periodically sync with OpenAI API usage endpoint
- Store both estimated and actual costs
- Alert on significant discrepancies
- Add cost prediction ML model for budgeting
- Support multiple LLM providers (OpenAI, Anthropic, etc.)

## Execution Order

1. **Phase 1: Foundation** (Steps 1, 2) - Clean up security issues, organize code structure
2. **Phase 2: Quality** (Step 3) - Establish code standards, run formatters
3. **Phase 3: Testing** (Step 4) - Build comprehensive test suite, setup CI/CD
4. **Phase 4: Documentation** (Step 5) - Consolidate and improve docs
5. **Phase 5: Optimization** (Step 6) - Refine architecture, reduce complexity
6. **Phase 6: Compliance & Monitoring** (Step 7)
   - 6a: Setup FastAPI dashboard backend with all API endpoints
   - 6b: Initialize React + Vite frontend project
   - 6c: Build React components and pages
   - 6d: Integrate frontend with backend APIs
   - 6e: Add WebSocket for real-time updates
   - 6f: Implement EU AI Act compliance features

## Rollback Strategy

- Tag current state as `v0.9-pre-refactor` before starting
- Commit after each phase completes
- Keep deprecated code in `backup_old/` temporarily
- Full test suite must pass before merging any phase

## Success Metrics

- ✅ Zero hardcoded secrets in repository
- ✅ 80%+ test coverage
- ✅ All CI checks passing
- ✅ Type checking with mypy enabled
- ✅ Code formatted with ruff
- ✅ Documentation under 10 markdown files
- ✅ MCP tools under 2000 total lines
- ✅ All imports organized and typed
- ✅ Admin dashboard operational with all CRUD operations
- ✅ 100% conversation logging with EU AI Act compliance
- ✅ Token usage tracking by org/user with cost estimation
- ✅ Audit trail for all system operations
- ✅ Data retention policies implemented and automated
- ✅ Compliance reports exportable for regulatory audits
- ✅ OpenAPI/Swagger documentation complete and accessible at `/docs` and `/redoc`
- ✅ All API endpoints have example requests/responses in Swagger UI
- ✅ OpenAPI schema validation tests passing
