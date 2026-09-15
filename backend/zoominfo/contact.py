

class ZoomInfoContactService:

    def __init__(self, client):
        self.client = client

    # Higher number = stronger target
    TITLE_PRIORITY = {
    # HR leadership
        "chief human resources officer": 120,
        "chief people officer": 118,

        "vice president of human resources": 115,
        "vice president human resources": 115,
        "vp human resources": 115,

        "human resources director": 110,
        "director of human resources": 110,
        "hr director": 110,
        "human resources manager": 105,
        "hr manager": 105,

        # Talent acquisition
        "director of talent acquisition": 108,
        "talent acquisition director": 108,
        "talent acquisition manager": 105,

        # Recruiting
        "director of recruiting": 102,
        "recruiting director": 102,
        "recruiting manager": 98,
        "senior recruiter": 95,
        "recruiter": 90,

        # Staffing
        "staffing manager": 88,
        "staffing coordinator": 85,

        # Nursing leadership
        "chief nursing officer": 70,
        "director of nursing": 65,

        # Facility leadership
        "executive director": 60,
        "administrator": 55,
    }

    def search_contacts(
        self,
        company_name: str,
        page_size: int = 100,
    ):
        """
        Search contacts at a company.
        """

        if not company_name:
            return []

        payload = {
            "data": {
                "type":
                    "ContactSearch",

                "attributes": {
                    "companyName":
                        company_name
                }
            }
        }

        response = self.client.post(
            "/contacts/search",
            payload,
            params={
                "page[number]": 1,
                "page[size]":
                    page_size,

                "sort":
                    "-relevance"
            }
        )

        return response.get(
            "data",
            []
        )

    def _title_score(
        self,
        job_title: str
    ):

        if not job_title:
            return 0

        title = job_title.lower()

        best_score = 0

        for keyword, score in (
            self.TITLE_PRIORITY.items()
        ):

            if keyword in title:

                best_score = max(
                    best_score,
                    score
                )

        return best_score

    def rank_contacts(
        self,
        contacts: list,
        target_roles: str = "",
    ):
        """
        Rank contacts based on:
        1. HR / recruiting fallback priority
        2. HireScope target role relevance
        3. ZoomInfo contact accuracy
        """

        ranked = []

        target_roles_lower = (
            target_roles.lower().strip()
            if target_roles
            else ""
        )

        target_is_unknown = target_roles_lower in {
            "",
            "unknown",
            "none",
            "n/a",
        }

        generic_words = {
            "director",
            "manager",
            "officer",
            "chief",
            "vice",
            "president",
            "senior",
            "head",
        }

        for contact in contacts:

            attributes = contact.get(
                "attributes",
                {}
            )

            title = attributes.get(
                "jobTitle",
                ""
            )

            title_lower = (
                title.lower().strip()
                if title
                else ""
            )

            # Base score from our preferred
            # decision-maker hierarchy.
            score = self._title_score(
                title
            )

            # =========================
            # TARGET ROLE MATCHING
            # =========================

            if (
                not target_is_unknown
                and title_lower
            ):

                important_words = [
                    word
                    for word in
                    target_roles_lower.split()
                    if (
                        len(word) > 3
                        and word
                        not in generic_words
                    )
                ]

                matched_words = sum(
                    1
                    for word
                    in important_words
                    if word in title_lower
                )

                score += (
                    matched_words * 30
                )

            # =========================
            # UNKNOWN ROLE FALLBACK
            # =========================

            if target_is_unknown:

                # Strongly prefer HR / People
                if (
                    "human resources"
                    in title_lower
                    or " hr "
                    in f" {title_lower} "
                    or title_lower.startswith("hr ")
                ):
                    score += 80

                # Then Talent Acquisition
                elif (
                    "talent acquisition"
                    in title_lower
                ):
                    score += 75

                # Then Recruiting
                elif (
                    "recruit"
                    in title_lower
                ):
                    score += 70

                # Then Staffing
                elif (
                    "staffing"
                    in title_lower
                ):
                    score += 65

                # Nursing leadership is
                # acceptable but lower priority.
                elif (
                    "nursing"
                    in title_lower
                ):
                    score += 5

                # Operations should not beat
                # HR / recruiting contacts.
                elif (
                    "operations"
                    in title_lower
                ):
                    score -= 20

            # =========================
            # CONTACT DATA BONUS
            # =========================

            if attributes.get(
                "hasEmail",
                False
            ):
                score += 5

            if attributes.get(
                "hasMobilePhone",
                False
            ):
                score += 3

            # =========================
            # ZOOMINFO ACCURACY
            # =========================

            accuracy = (
                attributes.get(
                    "contactAccuracyScore"
                )
                or 0
            )

            try:
                score += (
                    float(accuracy)
                    / 10
                )
            except (
                TypeError,
                ValueError
            ):
                pass

            ranked.append({
                "id":
                    contact.get("id"),

                "first_name":
                    attributes.get(
                        "firstName",
                        ""
                    ),

                "last_name":
                    attributes.get(
                        "lastName",
                        ""
                    ),

                "job_title":
                    title,

                "company":
                    attributes.get(
                        "company",
                        {}
                    ),

                "contact_accuracy":
                    accuracy,

                "has_email":
                    attributes.get(
                        "hasEmail",
                        False
                    ),

                "has_direct_phone":
                    attributes.get(
                        "hasDirectPhone",
                        False
                    ),

                "has_mobile_phone":
                    attributes.get(
                        "hasMobilePhone",
                        False
                    ),

                "ranking_score":
                    round(
                        score,
                        2
                    )
            })

        return sorted(
            ranked,
            key=lambda x:
                x["ranking_score"],
            reverse=True
        )

    def get_best_contacts(
        self,
        company_name: str,
        target_roles: str = "",
        limit: int = 3,
    ):

        contacts = self.search_contacts(
            company_name
        )

        ranked = self.rank_contacts(
            contacts,
            target_roles
        )

        return ranked[:limit]