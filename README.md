# NBNE Personaliser — Template Layout Engine

**A production automation SaaS for personalised print businesses**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)

---

## Overview

NBNE Personaliser is a full-stack web application that automates the workflow from e-commerce order ingestion (Amazon, Etsy) to print-ready PDF/SVG generation for UV printing, laser engraving, and similar personalised-product businesses.

**Core problem solved:** Businesses selling personalised items (memorial plaques, custom signs, engraved gifts) spend 10–15 minutes per order manually copying customer data into design files. This tool reduces that to seconds.

**Live demo:** [demo.nbne.uk](https://demo.nbne.uk)

---

## Technology Stack

| Layer        | Technology                              |
|-------------|-----------------------------------------|
| **Backend**  | Python 3.11, FastAPI, SQLAlchemy, Pydantic |
| **Frontend** | Next.js 14, React 18, TypeScript        |
| **Rendering**| CairoSVG, ReportLab (PDF generation)    |
| **Auth**     | JWT + bcrypt, session-based auth        |
| **Database** | SQLite (dev), PostgreSQL-ready          |
| **Deploy**   | Render.com (backend), Vercel (frontend) |
| **Monitoring**| Sentry error tracking                  |

---

## Architecture

```
┌─────────────────────────────────────────────────┐
│                  Frontend (Next.js)              │
│         React UI · TypeScript · Forms            │
└──────────────────────┬──────────────────────────┘
                       │ REST API
┌──────────────────────▼──────────────────────────┐
│               Backend (FastAPI)                  │
│  ┌──────────┐ ┌───────────┐ ┌────────────────┐  │
│  │  Auth    │ │  Routers  │ │  Middleware     │  │
│  │  (JWT)   │ │  (REST)   │ │  (Rate Limit)  │  │
│  └──────────┘ └─────┬─────┘ └────────────────┘  │
│                     │                            │
│  ┌──────────────────▼─────────────────────────┐  │
│  │           Order Processors                 │  │
│  │  Amazon · Etsy · CSV · Photo · Text-only   │  │
│  └──────────────────┬─────────────────────────┘  │
│                     │                            │
│  ┌──────────────────▼─────────────────────────┐  │
│  │           Layout Engine                    │  │
│  │  SVG Renderer · Template System · Packer   │  │
│  │  CSV Parser · PDF Export · Bed Optimizer   │  │
│  └────────────────────────────────────────────┘  │
│                                                  │
│  ┌────────────────────────────────────────────┐  │
│  │  Database (SQLAlchemy) · File Storage      │  │
│  └────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────┘
```

---

## Project Structure

```
personaliser/
├── backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI application entry point
│   │   ├── settings.py             # Configuration management
│   │   ├── database.py             # SQLAlchemy database setup
│   │   ├── auth.py                 # JWT authentication
│   │   ├── auth_simple.py          # Session-based authentication
│   │   ├── models/                 # Database models (User, Graphic)
│   │   ├── routers/                # API endpoint handlers
│   │   │   ├── auth_router.py      # Auth endpoints
│   │   │   ├── catalog.py          # Product catalog
│   │   │   ├── jobs.py             # Job management
│   │   │   ├── ingest_amazon.py    # Amazon order ingestion
│   │   │   ├── layout_engine.py    # Layout generation API
│   │   │   └── graphics_router.py  # Graphics management
│   │   ├── processors/             # Order processing pipeline
│   │   │   ├── base.py             # Base processor class
│   │   │   ├── item_router.py      # Order routing logic
│   │   │   ├── photo_stakes_v1.py  # Photo product processor
│   │   │   ├── regular_stake_v1.py # Standard product processor
│   │   │   └── text_only_v1.py     # Text-only processor
│   │   ├── layout_engine/          # Core rendering system
│   │   │   ├── renderer.py         # SVG rendering engine
│   │   │   ├── csv_parser.py       # Data parsing & validation
│   │   │   ├── models.py           # Layout data models
│   │   │   ├── pdf_export.py       # PDF generation
│   │   │   └── converters.py       # Format conversions
│   │   ├── middleware/             # Rate limiting
│   │   ├── utils/                  # Security, SKU mapping
│   │   └── packer/                # Bed optimisation algorithms
│   ├── tests/                     # pytest test suite
│   ├── requirements.txt           # Python dependencies
│   └── demo.html                  # Standalone demo interface
├── frontend/
│   ├── app/                       # Next.js app router
│   ├── components/                # React components
│   ├── lib/                       # Utility libraries
│   ├── package.json               # Node dependencies
│   └── tsconfig.json              # TypeScript config
├── docs/                          # User & developer documentation
├── examples/                      # Sample CSV data files
├── assets/                        # Static assets (images, icons)
└── fonts/                         # Font files for rendering
```

---

## Key Features

1. **Multi-platform order ingestion** — Parse CSV exports from Amazon, Etsy, or custom formats
2. **AI-powered data extraction** — Intelligent parsing of personalisation fields from gift messages and order notes
3. **SVG-based layout engine** — Template-driven design system with text and photo placeholders
4. **Bed optimisation** — Efficient tiling/nesting to minimise material waste
5. **PDF export** — Production-ready output with configurable print bed dimensions
6. **User authentication** — JWT + bcrypt with rate limiting and file upload validation
7. **Graphics management** — Per-user graphic libraries with public shared assets
8. **Product catalog** — SKU mapping and template association

---

## Local Development Setup

### Prerequisites
- Python 3.11+
- Node.js 20+
- Git

### Backend

```bash
cd backend
python -m venv .venv
.venv/Scripts/activate      # Windows
# source .venv/bin/activate # macOS/Linux

pip install -r requirements.txt

# Copy and configure environment
cp ../.env.example .env
# Edit .env with your settings

# Run the server
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The frontend runs on `http://localhost:3000` and the backend API on `http://localhost:8000`.

API documentation is auto-generated at `http://localhost:8000/docs` (Swagger UI).

---

## Academic Notes

This repository is shared for **academic review and study purposes** under the MIT License. It represents a real-world SaaS product built for the personalised print industry.

### Areas of Interest for CS Students

- **Software architecture**: Full-stack SaaS with clear separation of concerns
- **API design**: RESTful API with FastAPI, Pydantic validation, dependency injection
- **Authentication**: JWT token flow, password hashing, session management, rate limiting
- **File processing pipeline**: CSV parsing → data validation → template rendering → PDF export
- **SVG manipulation**: Programmatic SVG generation with dynamic text/image placement
- **Database design**: SQLAlchemy ORM with migration-ready models
- **Deployment**: Docker, Render.com, Vercel configuration
- **Security**: Rate limiting, file upload validation, CORS, path traversal protection

---

## Contact

- **Website:** [www.nbne.uk](https://www.nbne.uk)
- **Email:** toby@nbne.uk

---

© 2025 NBNE Origin Ltd. Released under the [MIT License](./LICENSE).
