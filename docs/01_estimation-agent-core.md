# Estimation Agent Core Architecture

## Overview
The estimation-agent-core is an orchestration layer that coordinates between client requests and estimation calculation services.

## System Architecture

### Components
1. **Flask Web Server** (app.py)
   - Port: 8001 (default)
   - Debug mode enabled for development
   - Handles HTTP POST requests for estimation

2. **API Endpoints**
   - `POST /estimate`: Main estimation endpoint
     - Accepts JSON payload with project details
     - Returns HTML formatted results

3. **External Dependencies**
   - Calculation API: External service for performing estimation calculations
     - Base URL: Configurable via CALC_API_BASE environment variable
     - Default: http://localhost:7071
     - Endpoint: /api/calculate_estimate

### Data Flow
```
Client Request (JSON)
    ↓
Flask App (/estimate)
    ↓
External Calc API (/api/calculate_estimate)
    ↓
Response Processing
    ↓
HTML Rendering
    ↓
Client Response (HTML)
```

## Request Format
```json
{
  "project_name": "プロジェクト名",
  "summary": "プロジェクト概要",
  "scope": "プロジェクト範囲",
  "screen_count": 10,
  "complexity": "medium"
}
```

## Response Format
HTML document containing:
- Project name
- Summary
- Scope
- Screen count
- Complexity level
- Estimated person-days
- Estimated cost (JPY)

## Configuration
Environment variables:
- `CALC_API_BASE`: Base URL for calculation API service

## Dependencies
See requirements.txt for Python package dependencies:
- Flask 3.1.2: Web framework
- requests 2.32.5: HTTP client for API calls
- python-dotenv 1.2.1: Environment variable management
