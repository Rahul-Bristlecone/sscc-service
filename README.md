# SSCC Service

A Flask microservice that generates **GS1 Serial Shipping Container Codes (SSCC)** and produces PDF shipping labels, consuming order data from an upstream order service.

---

## Features

| Feature | Detail |
|---|---|
| SSCC generation | 18-digit GS1-compliant SSCC via Mod-10 check digit |
| Carton numbering | Auto-generated from supplier/customer initials + 7-digit sequence |
| PDF label | GS1-128 barcode + shipping details via ReportLab |
| Order integration | Fetches order data from `order-service:5007` |
| Validation | Marshmallow schemas on all incoming payloads |

---

## Project Structure

```
sscc-service/
├── src/
│   └── sscc/
│       ├── __init__.py          # App factory (create_app)
│       ├── config.py            # Configuration classes
│       ├── extensions.py        # Flask extensions (Marshmallow)
│       ├── models/
│       │   └── sscc_model.py    # SSCCRequest / SSCCResult dataclasses
│       ├── schemas/
│       │   └── sscc_schema.py   # Marshmallow validation schemas
│       ├── resources/
│       │   ├── __init__.py      # Blueprint registration
│       │   ├── sscc_resource.py # /api/v1/sscc/* routes
│       │   └── health_resource.py
│       └── services/
│           ├── sscc_service.py  # SSCC generation logic
│           ├── pdf_service.py   # ReportLab PDF label generation
│           └── order_client.py  # HTTP client for order-service
├── tests/
│   ├── conftest.py
│   ├── test_sscc_service.py
│   └── test_sscc_resource.py
├── run.py
├── pyproject.toml
├── Dockerfile
├── .env
├── .flaskenv
└── .github/workflows/ci.yml
```

---

## API Endpoints

### `POST /api/v1/sscc/generate`
Generate SSCC and download a PDF shipping label.

**Request body (JSON):**
```json
{
  "po_number": "PO-2024-001",
  "customer_name": "Acme Retail",
  "supplier_name": "Beta Logistics",
  "store": "Store 42",
  "location": "Warehouse A",
  "check_digit": 0,
  "quantities": 100,
  "product": "Widget XL",
  "carton_number": "BLAR0000001"
}
```
> `carton_number` is optional. If omitted, it is auto-generated as  
> `<2 supplier initials><2 customer initials><7-digit sequence>` e.g. `BLAR0000001`.

**Response:** `application/pdf`  
**Headers:** `X-SSCC-Code`, `X-Carton-Number`

---

### `POST /api/v1/sscc/generate/json`
Same as above but returns SSCC metadata as JSON (no PDF).

**Response:**
```json
{
  "sscc_code": "012345670000000014",
  "carton_number": "BLAR0000001",
  "po_number": "PO-2024-001",
  "customer_name": "Acme Retail",
  "supplier_name": "Beta Logistics",
  "store": "Store 42",
  "location": "Warehouse A",
  "quantities": 100,
  "product": "Widget XL"
}
```

---

### `POST /api/v1/sscc/generate-from-order`
Fetch order details from the order service, then return a PDF label.

**Request body:**
```json
{
  "po_number": "PO-2024-001",
  "check_digit": 0,
  "carton_number": null
}
```

---

### `GET /health`
```json
{ "status": "ok", "service": "sscc-service" }
```

---

## SSCC Structure

```
[ Extension (1) ][ GS1 Company Prefix (7) ][ Serial Reference (9) ][ Check Digit (1) ]
       ↑                    ↑                        ↑                      ↑
  check_digit input    GS1_COMPANY_PREFIX      from carton seq.       GS1 Mod-10
```

---

## Configuration

| Variable | Default | Description |
|---|---|---|
| `SECRET_KEY` | `dev-secret-...` | Flask secret key |
| `GS1_COMPANY_PREFIX` | `1234567` | Your GS1-assigned 7-digit company prefix |
| `SSCC_EXTENSION_DIGIT` | `0` | Default extension digit |
| `ORDER_SERVICE_URL` | `http://order-service:5007` | Upstream order service URL |

---

## Running Locally

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install ".[dev]"
flask run
```

## Running with Docker

```bash
docker build -t sscc-service .
docker run -p 5000:5000 \
  -e GS1_COMPANY_PREFIX=1234567 \
  -e ORDER_SERVICE_URL=http://order-service:5007 \
  sscc-service
```

## Tests

```bash
pytest --cov=sscc --cov-report=term-missing
```
