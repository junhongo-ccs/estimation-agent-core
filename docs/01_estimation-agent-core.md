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
Key application dependencies (see requirements.txt for complete list):
- Flask 3.1.2: Web framework
- requests 2.32.5: HTTP client for API calls
- python-dotenv 1.2.1: Environment variable management
- Jinja2 3.1.6: Template engine (available but not yet utilized)

All dependencies:
- blinker 1.9.0
- certifi 2025.11.12
- charset-normalizer 3.4.4
- click 8.3.1
- Flask 3.1.2
- idna 3.11
- itsdangerous 2.2.0
- Jinja2 3.1.6
- MarkupSafe 3.0.3
- python-dotenv 1.2.1
- requests 2.32.5
- urllib3 2.6.2
- Werkzeug 3.1.4
