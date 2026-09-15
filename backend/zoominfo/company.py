class ZoomInfoCompanyService:

    def __init__(self, client):
        self.client = client

    def search_company(
        self,
        company_name: str,
        page_size: int = 10,
    ):
        """
        Search ZoomInfo for companies
        matching a company name.
        """

        if not company_name:
            return []

        payload = {
            "data": {
                "type":
                    "CompanySearch",

                "attributes": {
                    "companyName":
                        company_name
                }
            }
        }

        response = self.client.post(
            "/companies/search",
            payload,
            params={
                "page[number]": 1,
                "page[size]":
                    page_size
            }
        )

        return response.get(
            "data",
            []
        )

    def get_best_company_match(
        self,
        company_name: str,
        location: str = "",
    ):
        """
        Search companies and choose
        the strongest basic match.
        """

        results = self.search_company(
            company_name
        )

        if not results:
            return None

        company_name_lower = (
            company_name.lower().strip()
        )

        location_lower = (
            location.lower().strip()
        )

        best_result = None
        best_score = -1

        for result in results:

            attributes = result.get(
                "attributes",
                {}
            )

            result_name = str(
                attributes.get(
                    "name",
                    ""
                )
            ).lower()

            score = 0

            # Exact name
            if (
                result_name
                == company_name_lower
            ):
                score += 100

            # Partial name
            elif (
                company_name_lower
                in result_name
                or result_name
                in company_name_lower
            ):
                score += 50

            # Optional location check
            result_location = " ".join(
                str(
                    attributes.get(
                        field,
                        ""
                    )
                ).lower()
                for field in [
                    "city",
                    "state",
                    "country"
                ]
            )

            if (
                location_lower
                and location_lower
                in result_location
            ):
                score += 20

            if score > best_score:

                best_score = score

                best_result = {
                    "id":
                        result.get("id"),

                    "attributes":
                        attributes,

                    "match_score":
                        score
                }

        return best_result