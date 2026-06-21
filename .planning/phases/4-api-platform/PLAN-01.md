# Phase 4: API Platform — PLAN-01
## Finaro AP Automation

---

## 1. Phase Overview

**Phase:** 4 — API Platform  
**Type:** FastAPI REST API + PostgreSQL Persistence  
**Priority:** HIGH (requires Phase 3 core engine)  
**Estimated Duration:** 35–50 hours  
**Deliverable:** Production-ready FastAPI application exposing matching engine via REST endpoints

---

## 2. Phase Overview

Phase 4 builds the REST API layer around the Phase 3 matching engine, adding:
1. Persistent storage for Invoices, POs, GRNs, and MatchResults
2. RESTful endpoints for CRUD operations and match triggering
3. JWT-based authentication
4. Background job support for async matching
5. Health checks and monitoring endpoints

---

## 3. Technical Architecture

### 3.1 Project Structure
```
src/
├── api/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── config.py            # API configuration
│   ├── dependencies.py      # Dependency injection
│   ├── middleware/
│   │   ├── __init__.py
│   │   ├── logging.py       # Request/response logging
│   │   ├── error_handler.py # Global error handling
│   │   └── cors.py          # CORS configuration
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── auth.py          # /api/v1/auth
│   │   ├── invoices.py      # /api/v1/invoices
│   │   ├── purchase_orders.py # /api/v1/purchase-orders
│   │   ├── grns.py          # /api/v1/grns
│   │   ├── matching.py      # /api/v1/matching
│   │   └── health.py        # /api/v1/health
│   └── schemas/
│       ├── __init__.py
│       ├── auth.py          # Token, Login schemas
│       ├── invoice.py       # Invoice request/response
│       ├── po.py            # PO request/response
│       ├── grn.py           # GRN request/response
│       ├── matching.py      # Match request/response
│       └── common.py        # Pagination, Error schemas
├── core/                    # Phase 3 matching engine
├── models/                  # SQLAlchemy ORM models
│   ├── __init__.py
│   ├── base.py              # Base model with common fields
│   ├── invoice.py
│   ├── purchase_order.py
│   ├── grn.py
│   ├── line_item.py
│   ├── match_result.py
│   ├── supplier.py
│   ├── customer.py
│   └── user.py
├── services/
│   ├── __init__.py
│   ├── auth.py              # JWT token service
│   ├── invoice_service.py
│   ├── po_service.py
│   ├── grn_service.py
│   └── matching_service.py  # Orchestrates core engine + persistence
├── db/
│   ├── __init__.py
│   ├── database.py          # SQLAlchemy engine, session
│   ├── repositories/
│   │   ├── __init__.py
│   │   ├── invoice_repo.py
│   │   ├── po_repo.py
│   │   ├── grn_repo.py
│   │   └── match_result_repo.py
│   └── migrations/          # Alembic migrations
├── workers/
│   ├── __init__.py
│   └── matching_worker.py   # Background matching jobs
└── tests/
    ├── unit/
    └── integration/
```

### 3.2 Database Schema (PostgreSQL)

#### Tables

**users**
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| email | VARCHAR(255) | UNIQUE, NOT NULL |
| hashed_password | VARCHAR(255) | NOT NULL |
| is_active | BOOLEAN | DEFAULT TRUE |
| is_superuser | BOOLEAN | DEFAULT FALSE |
| created_at | TIMESTAMP | NOT NULL |
| updated_at | TIMESTAMP | NOT NULL |

**suppliers**
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| name | VARCHAR(255) | NOT NULL |
| tax_id | VARCHAR(50) | UNIQUE |
| created_at | TIMESTAMP | NOT NULL |
| updated_at | TIMESTAMP | NOT NULL |

**customers**
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| name | VARCHAR(255) | NOT NULL |
| tax_id | VARCHAR(50) | UNIQUE |
| created_at | TIMESTAMP | NOT NULL |
| updated_at | TIMESTAMP | NOT NULL |

**invoices**
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| document_number | VARCHAR(100) | NOT NULL |
| supplier_id | UUID | FK → suppliers.id |
| customer_id | UUID | FK → customers.id |
| issue_date | DATE | NOT NULL |
| total_amount | DECIMAL(12,4) | NOT NULL |
| tax_amount | DECIMAL(12,4) | NOT NULL |
| currency | VARCHAR(3) | NOT NULL |
| status | VARCHAR(20) | DEFAULT 'pending' |
| raw_metadata | JSONB | |
| created_at | TIMESTAMP | NOT NULL |
| updated_at | TIMESTAMP | NOT NULL |

**purchase_orders**
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| document_number | VARCHAR(100) | NOT NULL |
| supplier_id | UUID | FK → suppliers.id |
| customer_id | UUID | FK → customers.id |
| order_date | DATE | NOT NULL |
| delivery_date | DATE | |
| total_amount | DECIMAL(12,4) | NOT NULL |
| currency | VARCHAR(3) | NOT NULL |
| status | VARCHAR(20) | DEFAULT 'pending' |
| raw_metadata | JSONB | |
| created_at | TIMESTAMP | NOT NULL |
| updated_at | TIMESTAMP | NOT NULL |

**grns** (Goods Received Notes / Albaranes)
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| document_number | VARCHAR(100) | NOT NULL |
| supplier_id | UUID | FK → suppliers.id |
| customer_id | UUID | FK → customers.id |
| receipt_date | DATE | NOT NULL |
| total_amount | DECIMAL(12,4) | NOT NULL |
| currency | VARCHAR(3) | NOT NULL |
| status | VARCHAR(20) | DEFAULT 'pending' |
| raw_metadata | JSONB | |
| created_at | TIMESTAMP | NOT NULL |
| updated_at | TIMESTAMP | NOT NULL |

**line_items**
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| document_type | VARCHAR(20) | NOT NULL |
| document_id | UUID | NOT NULL |
| line_number | INTEGER | NOT NULL |
| product_code | VARCHAR(100) | |
| description | TEXT | |
| quantity | DECIMAL(12,4) | NOT NULL |
| unit_price | DECIMAL(12,4) | NOT NULL |
| total_price | DECIMAL(12,4) | NOT NULL |
| tax_rate | DECIMAL(5,4) | |
| created_at | TIMESTAMP | NOT NULL |
| updated_at | TIMESTAMP | NOT NULL |

**match_results**
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| invoice_id | UUID | FK → invoices.id |
| po_id | UUID | FK → purchase_orders.id |
| grn_id | UUID | FK → grns.id |
| status | VARCHAR(20) | NOT NULL |
| match_score | DECIMAL(5,2) | |
| mismatch_reasons | JSONB | |
| line_results | JSONB | |
| matched_at | TIMESTAMP | |
| created_at | TIMESTAMP | NOT NULL |
| updated_at | TIMESTAMP | NOT NULL |

**Indexes**
```sql
CREATE INDEX idx_invoices_supplier ON invoices(supplier_id);
CREATE INDEX idx_invoices_customer ON invoices(customer_id);
CREATE INDEX idx_invoices_status ON invoices(status);
CREATE INDEX idx_pos_supplier ON purchase_orders(supplier_id);
CREATE INDEX idx_pos_customer ON purchase_orders(customer_id);
CREATE INDEX idx_grns_supplier ON grns(supplier_id);
CREATE INDEX idx_grns_customer ON grns(customer_id);
CREATE INDEX idx_line_items_document ON line_items(document_type, document_id);
CREATE INDEX idx_match_results_invoice ON match_results(invoice_id);
CREATE INDEX idx_match_results_po ON match_results(po_id);
```

---

## 4. API Specification

### 4.1 Authentication

**POST /api/v1/auth/login**
```json
Request:
{
  "email": "user@example.com",
  "password": "string"
}

Response (200):
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

**POST /api/v1/auth/register** (admin only)
```json
Request:
{
  "email": "user@example.com",
  "password": "string",
  "is_superuser": false
}
```

### 4.2 Invoices

**POST /api/v1/invoices**
```json
Request:
{
  "document_number": "INV-2024-001",
  "supplier_id": "uuid",
  "customer_id": "uuid",
  "issue_date": "2024-01-15",
  "total_amount": 1000.00,
  "tax_amount": 210.00,
  "currency": "EUR",
  "lines": [
    {
      "line_number": 1,
      "product_code": "SKU123",
      "description": "Product A",
      "quantity": 10.0,
      "unit_price": 100.00,
      "total_price": 1000.00,
      "tax_rate": 0.21
    }
  ],
  "metadata": {}
}
```

**GET /api/v1/invoices/{id}**

**GET /api/v1/invoices** (with pagination)
```
GET /api/v1/invoices?page=1&page_size=20&status=pending
```

**PATCH /api/v1/invoices/{id}**

**DELETE /api/v1/invoices/{id}** (soft delete)

### 4.3 Purchase Orders

**POST /api/v1/purchase-orders**
**GET /api/v1/purchase-orders/{id}**
**GET /api/v1/purchase-orders**
**PATCH /api/v1/purchase-orders/{id}**
**DELETE /api/v1/purchase-orders/{id}**

### 4.4 GRNs (Delivery Notes)

**POST /api/v1/grns**
**GET /api/v1/grns/{id}**
**GET /api/v1/grns**
**PATCH /api/v1/grns/{id}**
**DELETE /api/v1/grns/{id}**

### 4.5 Matching

**POST /api/v1/matching/match**
```json
Request:
{
  "invoice_id": "uuid",
  "po_id": "uuid",
  "grn_id": "uuid"
}

Response (200):
{
  "id": "uuid",
  "invoice_id": "uuid",
  "po_id": "uuid",
  "grn_id": "uuid",
  "status": "MATCHED",
  "match_score": 100.0,
  "mismatch_reasons": [],
  "line_results": [...],
  "matched_at": "2024-01-15T10:30:00Z"
}
```

**POST /api/v1/matching/match-async** (background job)
```json
Request:
{
  "invoice_id": "uuid",
  "po_id": "uuid",
  "grn_id": "uuid"
}

Response (202):
{
  "job_id": "uuid",
  "status": "PROCESSING"
}
```

**GET /api/v1/matching/results/{id}**

**GET /api/v1/matching/results** (list, filterable by status)

### 4.6 Health

**GET /api/v1/health**
```json
Response (200):
{
  "status": "healthy",
  "database": "connected",
  "version": "1.0.0"
}
```

---

## 5. Functionality Specification

### 5.1 Core Features

| # | Feature | Description | Priority |
|---|---------|-------------|----------|
| F1 | User Authentication | JWT-based login/register | MUST |
| F2 | Invoice CRUD | Create, read, update, delete invoices | MUST |
| F3 | PO CRUD | Create, read, update, delete purchase orders | MUST |
| F4 | GRN CRUD | Create, read, update, delete delivery notes | MUST |
| F5 | Sync Matching | Trigger synchronous match operation | MUST |
| F6 | Async Matching | Background job for matching (returns job_id) | SHOULD |
| F7 | Result Retrieval | Fetch match results by ID or filter | MUST |
| F8 | Pagination | Paginated list endpoints | MUST |
| F9 | Soft Delete | Soft delete with is_deleted flag | SHOULD |
| F10 | Raw Metadata | Store original document JSON | SHOULD |

### 5.2 Authentication & Authorization

- JWT tokens with HS256 algorithm
- Access token expires in 1 hour
- Password hashing with bcrypt
- Role-based access: `superuser` can register new users

### 5.3 Error Handling

Standard error response format:
```json
{
  "detail": "Error message",
  "code": "ERROR_CODE",
  "errors": [
    {
      "field": "field_name",
      "message": "Field-specific error"
    }
  ]
}
```

Error codes:
| Code | HTTP Status | Description |
|------|-------------|-------------|
| AUTH_INVALID_CREDENTIALS | 401 | Invalid email/password |
| AUTH_TOKEN_EXPIRED | 401 | Token has expired |
| RESOURCE_NOT_FOUND | 404 | Document not found |
| VALIDATION_ERROR | 422 | Request validation failed |
| MATCH_BLOCKED | 400 | Match returned BLOCKING reason |

---

## 6. Configuration

### config.yaml
```yaml
database:
  host: "${DB_HOST:localhost}"
  port: "${DB_PORT:5432}"
  name: "${DB_NAME:finaro}"
  user: "${DB_USER:postgres}"
  password: "${DB_PASSWORD:postgres}"
  pool_size: 10
  max_overflow: 20

app:
  host: "0.0.0.0"
  port: 8000
  debug: false
  version: "1.0.0"

auth:
  secret_key: "${JWT_SECRET_KEY}"
  algorithm: "HS256"
  access_token_expire_minutes: 60

matching:
  tolerances:
    amount_percent: 0.01
    quantity_percent: 2.0
    date_days: 90
```

### Environment Variables
```
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/finaro
JWT_SECRET_KEY=your-secret-key-here
CORS_ORIGINS=http://localhost:3000
```

---

## 7. Docker Configuration

### Dockerfile
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### docker-compose.yml
```yaml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/finaro
      - JWT_SECRET_KEY=dev-secret-key
    depends_on:
      - db
      - redis
    volumes:
      - .:/app

  db:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=finaro
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

volumes:
  postgres_data:
```

---

## 8. Dependencies

```txt
# requirements.txt (Phase 4)
fastapi>=0.104
uvicorn[standard]>=0.24
sqlalchemy>=2.0
alembic>=1.12
pydantic>=2.0
pydantic-settings>=2.0
python-jose[cryptography]>=3.3
passlib[bcrypt]>=1.7
python-multipart>=0.0.6
asyncpg>=0.29
redis>=5.0
PyYAML>=6.0
pytest>=7.4
pytest-asyncio>=0.21
httpx>=0.25
```

---

## 9. Acceptance Criteria

### 9.1 Functional Criteria

- [ ] All CRUD endpoints return 200/201/204 as appropriate
- [ ] Authentication returns valid JWT on correct credentials
- [ ] Invalid credentials return 401
- [ ] Matching endpoint calls Phase 3 engine and persists result
- [ ] Async matching returns job_id immediately
- [ ] Pagination works on all list endpoints
- [ ] Health endpoint returns database connection status

### 9.2 Technical Criteria

- [ ] All endpoints documented with OpenAPI/Swagger
- [ ] Request validation returns 422 with field-level errors
- [ ] Database migrations run successfully via Alembic
- [ ] Configuration loaded from config.yaml + environment variables
- [ ] Connection pooling configured for PostgreSQL
- [ ] CORS middleware configured for frontend origin

### 9.3 Security Criteria

- [ ] Passwords hashed with bcrypt
- [ ] JWT tokens expire after 1 hour
- [ ] Superuser endpoint restricted to admin users
- [ ] SQL injection prevented via parameterized queries

---

## 10. Out of Scope (Phase 4)

- File upload (PDF/image parsing) — Phase 5+
- Real-time WebSocket notifications — Phase 5+
- Advanced analytics/reporting — Phase 5+
- Multi-tenancy — Phase 5+
- Email/notification services — Phase 5+

---

## 11. Success Gate

Phase 5 (Testing & Ops) cannot begin until Phase 4:
- Passes all integration tests
- API documentation complete
- Docker Compose local environment works
- Database migrations verified
- Health checks operational

---

## 12. Files to Create

The following files must be created in Phase 4:

### API Layer
```
src/api/__init__.py
src/api/main.py
src/api/config.py
src/api/dependencies.py
```

### API Middleware
```
src/api/middleware/__init__.py
src/api/middleware/logging.py
src/api/middleware/error_handler.py
src/api/middleware/cors.py
```

### API Routes
```
src/api/routes/__init__.py
src/api/routes/auth.py
src/api/routes/invoices.py
src/api/routes/purchase_orders.py
src/api/routes/grns.py
src/api/routes/matching.py
src/api/routes/health.py
```

### API Schemas
```
src/api/schemas/__init__.py
src/api/schemas/auth.py
src/api/schemas/invoice.py
src/api/schemas/po.py
src/api/schemas/grn.py
src/api/schemas/matching.py
src/api/schemas/common.py
```

### Database Layer
```
src/db/__init__.py
src/db/database.py
src/db/repositories/__init__.py
src/db/repositories/invoice_repo.py
src/db/repositories/po_repo.py
src/db/repositories/grn_repo.py
src/db/repositories/match_result_repo.py
src/db/migrations/  (Alembic migration files)
```

### ORM Models
```
src/models/__init__.py
src/models/base.py
src/models/invoice.py
src/models/purchase_order.py
src/models/grn.py
src/models/line_item.py
src/models/match_result.py
src/models/supplier.py
src/models/customer.py
src/models/user.py
```

### Services
```
src/services/__init__.py
src/services/auth.py
src/services/invoice_service.py
src/services/po_service.py
src/services/grn_service.py
src/services/matching_service.py
```

### Workers
```
src/workers/__init__.py
src/workers/matching_worker.py
```

### Configuration
```
config.yaml
requirements.txt (Phase 4 dependencies)
.env.example
.env.production
```

### Docker
```
Dockerfile
docker-compose.yml
docker-compose.prod.yml
```

### Tests
```
src/tests/unit/  (unit tests for API layer)
src/tests/integration/  (integration tests)
```

### Documentation
```
README.md (update with Phase 4 content)
```

---

## 13. Next Phase

Phase 5: Testing & Operations — Unit/integration tests, CI/CD pipeline, monitoring, alerting.
