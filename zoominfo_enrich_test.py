from backend.zoominfo.client import ZoomInfoClient


client = ZoomInfoClient()

person_id = "521615345"

payload = {
    "data": {
        "type": "ContactEnrich",
        "attributes": {
            "matchPersonInput": [
                {
                    "personId": person_id
                }
            ],
            "outputFields": [
                "id",
                "firstName",
                "lastName",
                "jobTitle",
                "email",
                "phone",
                "mobilePhone",
                "managementLevel"
            ]
        }
    }
}

response = client.post(
    "/contacts/enrich",
    payload
)

print("Enrichment successful")

data = response.get("data", [])

for contact in data:
    attributes = contact.get(
        "attributes",
        {}
    )

    print(
        "Name:",
        attributes.get("firstName"),
        attributes.get("lastName")
    )

    print(
        "Title:",
        attributes.get("jobTitle")
    )

    print(
        "Email available:",
        bool(attributes.get("email"))
    )

    print(
        "Phone available:",
        bool(attributes.get("phone"))
    )

    print(
        "Mobile available:",
        bool(attributes.get("mobilePhone"))
    )

    print(
        "Management Level:",
        attributes.get("managementLevel")
    )