"""HTTP client for the Order Service."""

import requests
from flask import current_app


class OrderServiceError(Exception):
    """Raised when the order service returns an error or is unreachable."""


def fetch_order(po_number: str) -> dict:
    """
    Retrieve order details from the order service.

    Expected response shape:
    {
        "po_number": "PO-001",
        "customer_name": "Customer A",
        "supplier_name": "Supplier B",
        "store": "Store 01",
        "location": "Warehouse 3",
        "quantities": 50,
        "product": "Widget XL"
    }
    """
    base_url: str = current_app.config["ORDER_SERVICE_URL"].rstrip("/")
    url = f"{base_url}/api/v1/orders/{po_number}"

    try:
        response = requests.get(url, timeout=10)
    except requests.exceptions.ConnectionError as exc:
        raise OrderServiceError(f"Cannot reach order service at {base_url}: {exc}") from exc
    except requests.exceptions.Timeout as exc:
        raise OrderServiceError("Order service request timed out.") from exc

    if response.status_code == 404:
        raise OrderServiceError(f"Order '{po_number}' not found in order service.")

    if not response.ok:
        raise OrderServiceError(
            f"Order service returned {response.status_code}: {response.text[:200]}"
        )

    return response.json()
