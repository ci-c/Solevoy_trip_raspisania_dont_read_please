"""API client for working with SZGMU faculties and specialities."""

import json
from typing import Optional

import httpx
from loguru import logger


class FacultyAPIClient:
    """API client for SZGMU faculty and speciality data."""

    def __init__(self) -> None:
        """Initialize the API client."""
        self.base_url = "https://frsview.szgmu.ru/api"
        self._headers = {
            "Content-Type": "application/json",
            "User-Agent": "SZGMU-Schedule-Bot/2.0",
        }
        self._timeout = httpx.Timeout(15.0)

    def get_faculties(self) -> list[dict]:
        """Get list of all faculties.

        Returns:
            List of faculty dictionaries with id and name.
        """
        url = f"{self.base_url}/faculties"

        try:
            with httpx.Client(timeout=self._timeout, headers=self._headers) as client:
                response = client.get(url)
                response.raise_for_status()
                data = response.json()

            if isinstance(data, list):
                logger.info(f"Retrieved {len(data)} faculties")
                return data

            logger.warning("API response is not a list")
            return []

        except httpx.HTTPStatusError as e:
            logger.error(
                "Faculties request failed with status %s",
                e.response.status_code,
            )
            return []
        except httpx.RequestError as e:
            logger.error(f"HTTP request error: {e}")
            return []
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            return []

    def get_specialities(self, faculty_id: int | None = None) -> list[dict]:
        """Get list of specialities, optionally filtered by faculty.

        Args:
            faculty_id: Optional ID of faculty to filter by.

        Returns:
            List of speciality dictionaries with code, name and faculty info.
        """
        url = f"{self.base_url}/specialities"
        if faculty_id is not None:
            url += f"?facultyId={faculty_id}"

        try:
            with httpx.Client(timeout=self._timeout, headers=self._headers) as client:
                response = client.get(url)
                response.raise_for_status()
                data = response.json()

            if isinstance(data, list):
                logger.info(f"Retrieved {len(data)} specialities")
                return data

            logger.warning("API response is not a list")
            return []

        except httpx.HTTPStatusError as e:
            logger.error(
                "Specialities request failed with status %s",
                e.response.status_code,
            )
            return []
        except httpx.RequestError as e:
            logger.error(f"HTTP request error: {e}")
            return []
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            return []
