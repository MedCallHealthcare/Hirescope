from backend.zoominfo.enrichment import (
    ZoomInfoEnrichmentService
)


service = ZoomInfoEnrichmentService()

facility = {
    "company_name": "oak street health",
    "location": "peoria, il",
    "decision_maker_roles": "Emergency Department Director",
    "priority": "A",
}

result = service.enrich_facility(
    facility
)

print(
    "Status:",
    result.get("zoominfo_status")
)

print(
    "Company:",
    result.get("zoominfo_company_name")
)

print(
    "Contact:",
    result.get("zoominfo_contact_name")
)

print(
    "Title:",
    result.get("zoominfo_contact_title")
)

print(
    "Management level:",
    result.get("zoominfo_management_level")
)

print(
    "Email available:",
    bool(result.get("zoominfo_email"))
)

print(
    "Phone available:",
    bool(result.get("zoominfo_phone"))
)

print(
    "Mobile available:",
    bool(result.get("zoominfo_mobile_phone"))
)