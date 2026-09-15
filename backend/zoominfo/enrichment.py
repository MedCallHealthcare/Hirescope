import pandas as pd

from backend.zoominfo.client import (
    ZoomInfoClient
)

from backend.zoominfo.company import (
    ZoomInfoCompanyService
)

from backend.zoominfo.contact import (
    ZoomInfoContactService
)


DEFAULT_CONTACT_FIELDS = [
    "id",
    "firstName",
    "lastName",
    "jobTitle",
    "email",
    "phone",
    "mobilePhone",
    "managementLevel",
]


class ZoomInfoEnrichmentService:

    def __init__(self):

        self.client = (
            ZoomInfoClient()
        )

        self.companies = (
            ZoomInfoCompanyService(
                self.client
            )
        )

        self.contacts = (
            ZoomInfoContactService(
                self.client
            )
        )

    def _initialize_zoominfo_fields(
        self,
        facility: dict,
    ):
        result = facility.copy()

        result.setdefault(
            "zoominfo_status",
            ""
        )

        result.setdefault(
            "zoominfo_company_id",
            ""
        )

        result.setdefault(
            "zoominfo_company_name",
            ""
        )

        result.setdefault(
            "zoominfo_contact_id",
            ""
        )

        result.setdefault(
            "zoominfo_contact_name",
            ""
        )

        result.setdefault(
            "zoominfo_contact_title",
            ""
        )

        result.setdefault(
            "zoominfo_email",
            ""
        )

        result.setdefault(
            "zoominfo_phone",
            ""
        )

        result.setdefault(
            "zoominfo_mobile_phone",
            ""
        )

        result.setdefault(
            "zoominfo_management_level",
            ""
        )

        return result
    
    # =========================
    # ENRICH CONTACT
    # =========================

    def enrich_contact(
        self,
        person_id: str,
        output_fields=None,
    ):

        if not person_id:
            return None

        if output_fields is None:
            output_fields = (
                DEFAULT_CONTACT_FIELDS
            )

        payload = {
            "data": {
                "type":
                    "ContactEnrich",

                "attributes": {

                    "matchPersonInput": [
                        {
                            "personId":
                                str(
                                    person_id
                                )
                        }
                    ],

                    "outputFields":
                        output_fields
                }
            }
        }

        response = (
            self.client.post(
                "/contacts/enrich",
                payload
            )
        )

        data = response.get(
            "data",
            []
        )

        if not data:
            return None

        return data[0]

    # =========================
    # SINGLE FACILITY
    # =========================

    def enrich_facility(
        self,
        facility: dict,
    ):

        company_name = str(
            facility.get(
                "company_name",
                ""
            )
        ).strip()

        location = str(
            facility.get(
                "location",
                ""
            )
        ).strip()

        target_roles = str(
            facility.get(
                "decision_maker_roles",
                ""
            )
        ).strip()

        result = facility.copy()

        result.update({

            "zoominfo_status":
                "pending",

            "zoominfo_company_id":
                "",

            "zoominfo_company_name":
                "",

            "zoominfo_contact_id":
                "",

            "zoominfo_contact_name":
                "",

            "zoominfo_contact_title":
                "",

            "zoominfo_email":
                "",

            "zoominfo_phone":
                "",

            "zoominfo_mobile_phone":
                "",
            "zoominfo_management_level": "",
        })

        if not company_name:

            result[
                "zoominfo_status"
            ] = "missing_company_name"

            return result

        # ---------------------
        # COMPANY SEARCH
        # ---------------------

        company = (
            self.companies
            .get_best_company_match(
                company_name,
                location
            )
        )

        if not company:

            result[
                "zoominfo_status"
            ] = "company_not_found"

            return result

        company_attributes = (
            company.get(
                "attributes",
                {}
            )
        )

        result[
            "zoominfo_company_id"
        ] = company.get(
            "id",
            ""
        )

        result[
            "zoominfo_company_name"
        ] = company_attributes.get(
            "name",
            ""
        )

        # ---------------------
        # CONTACT SEARCH
        # ---------------------

        contacts = (
            self.contacts
            .get_best_contacts(
                company_name=
                    result[
                        "zoominfo_company_name"
                    ]
                    or company_name,

                target_roles=
                    target_roles,

                limit=3
            )
        )

        if not contacts:

            result[
                "zoominfo_status"
            ] = "contacts_not_found"

            return result

        # Choose highest ranked
        best_contact = contacts[0]

        if (
            best_contact.get(
                "ranking_score",
                0
            ) < 50
        ):
            result[
                "zoominfo_status"
            ] = "no_relevant_contact"

            return result

        person_id = (
            best_contact.get(
                "id"
            )
        )

        result[
            "zoominfo_contact_id"
        ] = person_id or ""

        result[
            "zoominfo_contact_name"
        ] = (
            f"{best_contact.get('first_name', '')} "
            f"{best_contact.get('last_name', '')}"
        ).strip()

        result[
            "zoominfo_contact_title"
        ] = best_contact.get(
            "job_title",
            ""
        )

        # ---------------------
        # CONTACT ENRICHMENT
        # ---------------------

        enriched = (
            self.enrich_contact(
                person_id
            )
        )

        if not enriched:

            result[
                "zoominfo_status"
            ] = (
                "contact_enrichment_failed"
            )

            return result

        attributes = enriched.get(
            "attributes",
            {}
        )

        result[
            "zoominfo_contact_name"
        ] = (
            f"{attributes.get('firstName', '')} "
            f"{attributes.get('lastName', '')}"
        ).strip()

        result[
            "zoominfo_contact_title"
        ] = attributes.get(
            "jobTitle",
            result[
                "zoominfo_contact_title"
            ]
        )

        result[
            "zoominfo_email"
        ] = attributes.get(
            "email",
            ""
        )

        result[
            "zoominfo_phone"
        ] = attributes.get(
            "phone",
            ""
        )

        result[
            "zoominfo_mobile_phone"
        ] = attributes.get(
            "mobilePhone",
            ""
        )

        result[
            "zoominfo_management_level"
        ] = attributes.get(
            "managementLevel",
            []
        )

        result[
            "zoominfo_status"
        ] = "enriched"

        return result

    # =========================
    # FACILITY DATAFRAME
    # =========================

    def enrich_facilities(
        self,
        facility_df:
            pd.DataFrame,

        priorities=(
            "A",
            "B"
        ),

        max_facilities=None,
    ) -> pd.DataFrame:

        if facility_df.empty:
            return facility_df

        rows = []

        enriched_count = 0

        for _, row in (
            facility_df.iterrows()
        ):

            facility = self._initialize_zoominfo_fields(
                row.to_dict()
            )

            priority = facility.get(
                "priority"
            )

            # Only enrich selected priorities
            if (
                priorities
                and priority
                not in priorities
            ):

                facility[
                    "zoominfo_status"
                ] = (
                    "skipped_priority"
                )

                rows.append(
                    facility
                )

                continue

            if (
                max_facilities
                is not None
                and enriched_count
                >= max_facilities
            ):

                facility[
                    "zoominfo_status"
                ] = (
                    "skipped_limit"
                )

                rows.append(
                    facility
                )

                continue

            try:

                enriched = (
                    self.enrich_facility(
                        facility
                    )
                )

                rows.append(
                    enriched
                )

                enriched_count += 1

            except Exception as exc:

                print(
                    "ZoomInfo enrichment "
                    "error for",
                    facility.get(
                        "company_name"
                    ),
                    ":",
                    exc
                )

                facility[
                    "zoominfo_status"
                ] = "api_error"

                facility[
                    "zoominfo_error"
                ] = str(exc)

                rows.append(
                    facility
                )

        return pd.DataFrame(
            rows
        )

    