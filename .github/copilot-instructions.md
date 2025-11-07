# Copilot Instructions for AI Coding Agents

## Project Overview
This repository implements an AI-powered middleware for bank statement reconciliation, focused on the Nigerian banking ecosystem. The solution ingests PDF/Excel statements, extracts and standardizes transaction data, and outputs ISO 20022 camt.053-compliant files for ERP and open banking integration.

## Architectural Principles & Best Practices
- **KISS:** Keep modules, functions, and APIs simple and focused.
- **DRY:** Avoid code duplication; use shared utilities and base classes.
- **SOLID:**
  - Single Responsibility: Each module/class should have one clear purpose.
  - Open/Closed: Modules should be extensible without modifying core logic.
  - Liskov Substitution: Use clear interfaces for interchangeable components (e.g., extractors).
  - Interface Segregation: APIs and classes should expose only what is needed.
  - Dependency Inversion: Use dependency injection for integrations and model selection.
- **Separation of Concerns:**
  - Extraction, mapping, and API logic must be in separate modules/packages.
  - Avoid mixing business logic with I/O or presentation code.
- **Configurable & Extensible:**
  - Use config files or environment variables for settings (API keys, model paths).
  - Design for easy addition of new banks, formats, or extraction methods.
- **Testing:**
  - Write unit tests for each module.
  - Use integration tests for end-to-end flows.
- **Documentation:**
  - Document module boundaries, interfaces, and extension points.
  - Use docstrings and markdown files for clarity.

## Architecture & Major Components

- **Backend (Python/FastAPI):** Modular design with clear separation of concerns:
  - File upload/ingestion
  - Extraction/parsing
  - Data mapping (ISO 20022)
  - API exposure
  - External integrations
  - Each major function should be in its own module/package (e.g., `extractors/`, `mappers/`, `api/`, `integrations/`).
- **Frontend (React/Vue):** Component-based dashboard for uploads, results, and model management.
- **AI Layer:** Integrates open-source models (LayoutLM, Donut) via Hugging Face for document extraction and fine-tuning.
- **External Integration:** DocuClipper API for OCR/extraction fallback; OAuth-based API key management.
- **Output Generator:** Uses lxml for camt.053 XML/JSON generation.
- **Deployment:** Dockerized for portability; supports cloud and on-prem setups.

## Developer Workflows
- **Build/Run:**
  - Backend: `uvicorn main:app --reload` (FastAPI entrypoint)
  - Frontend: `npm start` or `yarn start` (React/Vue)
  - Docker: `docker-compose up` for full stack
- **Testing:**
  - Backend: `pytest` for unit/integration tests
  - Frontend: `npm test` or `yarn test`
- **Documentation:**
  - API docs auto-generated via OpenAPI/Swagger (FastAPI)
  - See `IMPLEMENTATION_PLAN.md` for roadmap and backlog

## Project-Specific Patterns & Conventions
- **File Uploads:** Use FastAPI endpoints for PDF/Excel ingestion; batch support up to 100 files/session.
- **Extraction:** Prefer PyPDF2 for PDFs, openpyxl/pandas for Excel; fallback to DocuClipper API if local extraction fails.
- **Mapping:** All transaction data must be mapped to ISO 20022 camt.053 format using lxml; validate output against schema.
- **AI Training:** Model management dashboard supports upload, labeling, training, and deployment of custom models for Nigerian bank formats.
- **Security:** Enforce end-to-end encryption and anonymization for all data handling and training workflows.
- **API Exposure:** RESTful endpoints for upload, processing, retrieval; webhook support for ERP notifications.

## Integration Points & Dependencies
- **DocuClipper API:** Used for OCR/extraction when local parsing is insufficient; requires OAuth API keys.
- **Hugging Face Transformers:** For local AI model training and inference.
- **ERP Systems:** Output is designed for easy integration with SAP, QuickBooks, and other ERPs.

## Key Files & Directories
- `IMPLEMENTATION_PLAN.md`: Project roadmap, backlog, and conventions
- `.github/copilot-instructions.md`: AI agent instructions (this file)
- Backend source: `/backend/` (expected)
- Frontend source: `/frontend/` (expected)

- Example backend structure:
  - `/backend/api/` (API routes)
  - `/backend/extractors/` (PDF/Excel/DocuClipper extraction modules)
  - `/backend/mappers/` (ISO 20022 mapping)
  - `/backend/integrations/` (external APIs)
  - `/backend/models/` (AI models, training logic)
  - `/backend/utils/` (shared utilities)

## Example Patterns
- When adding new extraction logic, always update the mapping to camt.053 and validate output.
- For new AI models, document training steps and update the dashboard UI for model management.
- All new API endpoints must be documented in OpenAPI/Swagger and tested with sample files.

- When refactoring, always preserve modularity and separation of concerns.
- Use dependency injection for integrations and model selection.
- Prefer composition over inheritance for extensibility.

---

For questions or unclear conventions, review `IMPLEMENTATION_PLAN.md` or ask for clarification. Please suggest improvements if any section is incomplete or ambiguous.