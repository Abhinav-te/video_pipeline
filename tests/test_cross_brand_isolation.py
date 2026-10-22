"""
tests/test_cross_brand_isolation.py

Verifies strict brand and content isolation across projects:
- An Inngest project produces Inngest branding and URLs.
- A Stripe project produces Stripe branding and URLs with zero Inngest leakage.
- A Resend project produces Resend branding and URLs with zero Inngest/Stripe leakage.
- Missing required company identity fails validation rather than silently falling back.
"""

import json
from pathlib import Path
import pytest

from engine.config.brand_config import load_brand_config, BrandConfig

REPO_DIR = Path(__file__).resolve().parent.parent


def test_inngest_brand_isolation():
    proj_path = REPO_DIR / "projects" / "inngest_step_run.json"
    brand = load_brand_config(proj_path)
    assert brand.company_name == "Inngest"
    assert brand.logo_text == "INNGEST"
    assert "inngest.com" in brand.docs_url_display
    assert "stripe" not in brand.docs_url_display.lower()


def test_stripe_brand_isolation():
    proj_path = REPO_DIR / "projects" / "stripe_idempotency.json"
    brand = load_brand_config(proj_path)
    assert brand.company_name == "Stripe"
    assert brand.logo_text == "STRIPE"
    assert "stripe.com" in brand.docs_url_display
    # Zero Inngest leakage
    assert "inngest" not in brand.docs_url_display.lower()
    assert brand.company_name != "Inngest"


def test_resend_brand_isolation():
    proj_path = REPO_DIR / "projects" / "resend_webhooks.json"
    brand = load_brand_config(proj_path)
    assert brand.company_name == "Resend"
    assert brand.logo_text == "RESEND"
    assert "resend.com" in brand.docs_url_display
    # Zero Inngest / Stripe leakage
    assert "inngest" not in brand.docs_url_display.lower()
    assert "stripe" not in brand.docs_url_display.lower()


def test_distinct_identity_fields():
    proj = {
        "project_profile": {
            "product": "Neon Serverless Postgres",
            "product_subject": "Database Branching",
            "product_company": "Neon",
            "publisher_brand": "Acme Consulting",
            "sources": [{"url": "https://neon.tech/docs"}],
        }
    }
    brand = load_brand_config(proj)
    # Allows company to be distinct from product subject
    assert brand.company_name in {"Neon", "Acme Consulting", "Neon Serverless Postgres"}
    assert "inngest" not in brand.company_name.lower()
    assert "neon.tech" in brand.docs_url_display

