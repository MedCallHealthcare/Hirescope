from backend.zoominfo.client import (
    ZoomInfoClient
)

from backend.zoominfo.contact import (
    ZoomInfoContactService
)


client = ZoomInfoClient()

service = (
    ZoomInfoContactService(
        client
    )
)

contacts = (
    service.get_best_contacts(
        company_name=
            "Mayo Clinic",

        target_roles=
            "Human Resources Director",

        limit=10
    )
)

for contact in contacts:

    print(
        contact["id"],
        contact["first_name"],
        contact["last_name"],
        "-",
        contact["job_title"],
        "- score:",
        contact[
            "ranking_score"
        ],
        "- email available:",
        contact[
            "has_email"
        ]
    )