import os
import time
import requests

from dotenv import load_dotenv


load_dotenv()


class ZoomInfoClient:

    TOKEN_URL = (
        "https://api.zoominfo.com/"
        "gtm/oauth/v1/token"
    )

    BASE_URL = (
        "https://api.zoominfo.com/"
        "gtm/data/v1"
    )

    def __init__(self):

        self.client_id = os.getenv(
            "ZOOMINFO_CLIENT_ID"
        )

        self.client_secret = os.getenv(
            "ZOOMINFO_CLIENT_SECRET"
        )

        if not self.client_id:
            raise ValueError(
                "ZOOMINFO_CLIENT_ID "
                "is missing from .env"
            )

        if not self.client_secret:
            raise ValueError(
                "ZOOMINFO_CLIENT_SECRET "
                "is missing from .env"
            )

        self._access_token = None
        self._token_expires_at = 0

    # ==========================
    # AUTHENTICATION
    # ==========================

    def get_access_token(self):

        # Reuse existing token
        if (
            self._access_token
            and time.time()
            < self._token_expires_at
        ):
            return self._access_token

        response = requests.post(
            self.TOKEN_URL,
            auth=(
                self.client_id,
                self.client_secret
            ),
            headers={
                "Accept": "application/json",
                "Content-Type":
                    "application/x-www-form-urlencoded",
            },
            data={
                "grant_type":
                    "client_credentials"
            },
            timeout=30,
        )

        response.raise_for_status()

        data = response.json()

        access_token = data.get(
            "access_token"
        )

        if not access_token:
            raise RuntimeError(
                "ZoomInfo did not return "
                "an access token."
            )

        expires_in = data.get(
            "expires_in",
            3600
        )

        self._access_token = (
            access_token
        )

        # Refresh a little early
        self._token_expires_at = (
            time.time()
            + expires_in
            - 60
        )

        return self._access_token

    # ==========================
    # GENERAL API REQUEST
    # ==========================

    def post(
        self,
        endpoint: str,
        payload: dict,
        params: dict | None = None,
    ):

        token = self.get_access_token()

        url = (
            f"{self.BASE_URL}"
            f"{endpoint}"
        )

        response = requests.post(
            url,
            headers={
                "Authorization":
                    f"Bearer {token}",
                "Accept":
                    "application/vnd.api+json",
                "Content-Type":
                    "application/vnd.api+json",
            },
            json=payload,
            params=params,
            timeout=45,
        )

        if not response.ok:

            print(
                "ZoomInfo API request failed"
            )

            print(
                "Endpoint:",
                endpoint
            )

            print(
                "Status:",
                response.status_code
            )

            print(
                "Response:",
                response.text
            )

            response.raise_for_status()

        return response.json()