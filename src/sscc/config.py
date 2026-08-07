"""Application configuration."""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY: str = os.environ.get("SECRET_KEY", "dev-secret-change-in-production")

    # GS1 company prefix (7 digits) — must be assigned by GS1
    GS1_COMPANY_PREFIX: str = os.environ.get("GS1_COMPANY_PREFIX", "1234567")

    # Order service base URL
    ORDER_SERVICE_URL: str = os.environ.get("ORDER_SERVICE_URL", "http://order-service:5007")

    # SSCC extension digit (0–9)
    SSCC_EXTENSION_DIGIT: int = int(os.environ.get("SSCC_EXTENSION_DIGIT", "0"))


class TestingConfig(Config):
    TESTING = True
    ORDER_SERVICE_URL = "http://mock-order-service:5007"
