"""Synthetic HubSpot CRM payloads for connector tests (#1229).

Uses checksum-valid Brazilian CPF fixtures only — zero real customer /
prospect (e.g. Madruga) data. Safe to commit.
"""

from __future__ import annotations

from typing import Any

# Same synthetic CPF used across Data Boar unit tests (valid check digits).
SYNTHETIC_CPF_FORMATTED = "390.533.447-05"
SYNTHETIC_EMAIL = "audit.synthetic@example.com"
SYNTHETIC_COMPANY = "Synthetic Audit Co Ltda"
SYNTHETIC_DEAL = "Synthetic Pipeline Deal"


def properties_response(*names: str) -> dict[str, Any]:
    """HubSpot GET /crm/v3/properties/{objectType} shape."""
    return {
        "results": [
            {
                "name": n,
                "label": n.replace("_", " ").title(),
                "type": "string",
                "fieldType": "text",
                "groupName": "contactinformation",
            }
            for n in names
        ]
    }


def objects_page(
    rows: list[dict[str, Any]],
    *,
    after: str | None = None,
) -> dict[str, Any]:
    """HubSpot GET /crm/v3/objects/{objectType} page shape."""
    results = []
    for i, props in enumerate(rows, start=1):
        results.append({"id": str(i), "properties": props})
    payload: dict[str, Any] = {"results": results}
    if after:
        payload["paging"] = {"next": {"after": after}}
    return payload


def synthetic_contact_properties() -> dict[str, Any]:
    """Contact with CPF in a custom field (the #1166/#1229 detection gap)."""
    return {
        "email": SYNTHETIC_EMAIL,
        "firstname": "Synthetic",
        "lastname": "Contact",
        "cpf_custom": SYNTHETIC_CPF_FORMATTED,
    }


def synthetic_company_properties() -> dict[str, Any]:
    return {
        "name": SYNTHETIC_COMPANY,
        "domain": "example.com",
        "cnpj_custom": "11.222.333/0001-81",  # placeholder shape; detector may ignore
    }


def synthetic_deal_properties() -> dict[str, Any]:
    return {
        "dealname": SYNTHETIC_DEAL,
        "amount": "1000",
        "pipeline": "default",
    }


def contact_schema_and_pages() -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Full contact discovery + two object pages (for pagination tests)."""
    schema = properties_response("email", "firstname", "lastname", "cpf_custom")
    page1 = objects_page(
        [synthetic_contact_properties()],
        after="cursor-page-2",
    )
    page2 = objects_page(
        [
            {
                "email": "second.synthetic@example.com",
                "firstname": "Second",
                "lastname": "Synthetic",
                "cpf_custom": "",
            }
        ]
    )
    return schema, [page1, page2]
