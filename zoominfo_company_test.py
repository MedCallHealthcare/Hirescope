from backend.zoominfo.client import (
    ZoomInfoClient
)

from backend.zoominfo.company import (
    ZoomInfoCompanyService
)


client = ZoomInfoClient()

companies = (
    ZoomInfoCompanyService(
        client
    )
)

results = (
    companies.search_company(
        "Mayo Clinic"
    )
)

print(
    "Found:",
    len(results),
    "companies"
)

for company in results[:5]:

    print(
        company.get("id"),
        company.get(
            "attributes",
            {}
        ).get(
            "name"
        )
    )