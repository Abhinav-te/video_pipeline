"""
engine/config/brand_config.py

Client Brand Configuration & Design System Token Loader.
Extracts brand colors, typography, company name, logo badges, and documentation
URLs from project configs or brand_config.json to inject directly into Remotion BrandContext.
Strictly isolates branding between projects to prevent cross-brand leakage.
"""

import json
from pathlib import Path
from typing import Any, Dict, Optional, Union
from pydantic import BaseModel, Field

REPO_DIR = Path(__file__).resolve().parent.parent.parent


class BrandConfig(BaseModel):
    company_name: str = Field(default="Developer Tools", description="Company or product display name")
    logo_text: str = Field(default="DEVTOOL", description="High-contrast logo badge text")
    primary_color: str = Field(default="#6366F1", description="Primary brand accent color (hex)")
    secondary_color: str = Field(default="#10B981", description="Secondary brand color (hex)")
    warning_color: str = Field(default="#F59E0B", description="Warning / alert state color (hex)")
    danger_color: str = Field(default="#EF4444", description="Error / crash state color (hex)")
    bg_canvas: str = Field(default="#090A0F", description="Deep background canvas color (hex)")
    bg_surface: str = Field(default="#11131C", description="Elevated card surface color (hex)")
    font_sans: str = Field(default="Inter, system-ui, -apple-system, sans-serif", description="Main typography font family")
    font_mono: str = Field(default="JetBrains Mono, Fira Code, monospace", description="Code and monospace font family")
    docs_url_display: str = Field(default="docs.example.com", description="Display link for docs pill")


def load_brand_config(project_input: Union[Dict[str, Any], str, Path, None] = None) -> BrandConfig:
    """
    Loads BrandConfig from:
    1. 'brand' or 'brand_config' block in project dictionary
    2. Derived from project_profile (product_company, publisher_brand, product, sources)
    3. Neutral fallback tokens (never silently substituting another company)
    """
    raw_brand: Dict[str, Any] = {}

    # Case 1: Dict input
    if isinstance(project_input, dict):
        pp = project_input.get("project_profile") if isinstance(project_input.get("project_profile"), dict) else project_input
        
        # Check explicit brand block
        if "brand" in project_input and isinstance(project_input["brand"], dict):
            raw_brand = dict(project_input["brand"])
        elif "brand_config" in project_input and isinstance(project_input["brand_config"], dict):
            raw_brand = dict(project_input["brand_config"])
        elif "brand" in pp and isinstance(pp["brand"], dict):
            raw_brand = dict(pp["brand"])

        # Derive company name / logo from project identity
        company = (
            raw_brand.get("company_name")
            or pp.get("product_company")
            or pp.get("publisher_brand")
            or pp.get("client_brand")
            or pp.get("product")
        )
        if company:
            raw_brand.setdefault("company_name", company)
            raw_brand.setdefault("logo_text", company.upper())

        # Derive docs URL from sources if not specified
        sources = pp.get("sources", [])
        if "docs_url_display" not in raw_brand and sources and isinstance(sources, list):
            first_src = sources[0]
            if isinstance(first_src, dict) and first_src.get("url"):
                clean_url = first_src["url"].replace("https://", "").replace("http://", "").rstrip("/")
                raw_brand["docs_url_display"] = clean_url

        # Check render_profile theme if brand colors not specified
        rp = project_input.get("render_profile") or pp.get("render_profile", {})
        if isinstance(rp, dict):
            theme = rp.get("theme", {})
            if "accent" in theme and "primary_color" not in raw_brand:
                raw_brand["primary_color"] = theme["accent"]
            if "success" in theme and "secondary_color" not in raw_brand:
                raw_brand["secondary_color"] = theme["success"]
            if "warning" in theme and "warning_color" not in raw_brand:
                raw_brand["warning_color"] = theme["warning"]
            if "danger" in theme and "danger_color" not in raw_brand:
                raw_brand["danger_color"] = theme["danger"]
            if "background" in theme and "bg_canvas" not in raw_brand:
                raw_brand["bg_canvas"] = theme["background"]
            if "card_background" in theme and "bg_surface" not in raw_brand:
                raw_brand["bg_surface"] = theme["card_background"]

    # Case 2: File path input
    elif project_input is not None:
        p_path = Path(project_input)
        if p_path.exists():
            try:
                with open(p_path, "r", encoding="utf-8") as f:
                    file_data = json.load(f)
                return load_brand_config(file_data)
            except Exception:
                pass

    return BrandConfig(**raw_brand)
