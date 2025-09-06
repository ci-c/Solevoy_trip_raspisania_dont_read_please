"""API client for working with SZGMU faculties and specialities."""

import contextlib
import json
import requests
from loguru import logger


class FacultyAPIClient:
    """API client for SZGMU faculty and speciality data."""

    def __init__(self) -> None:
        """Initialize the API client."""
        self.base_url = "https://frsview.szgmu.ru/api"
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "User-Agent": "SZGMU-Schedule-Bot/1.0",
        })

    def get_faculties(self) -> list[dict]:
        """Get list of all faculties.
        
        Returns:
            List of faculty dictionaries with id and name.
        """
        url = f"{self.base_url}/faculties"

        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            data = response.json()

            if isinstance(data, list):
                logger.info(f"Retrieved {len(data)} faculties")
                return data
            
            logger.warning("API response is not a list")
            return []

        except requests.exceptions.Timeout:
            logger.error("Faculties request timed out")
            return []
        except requests.exceptions.RequestException as e:
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
        if faculty_id:
            url += f"?facultyId={faculty_id}"

        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            data = response.json()

            if isinstance(data, list):
                logger.info(f"Retrieved {len(data)} specialities")
                return data
            
            logger.warning("API response is not a list")
            return []

        except requests.exceptions.Timeout:
            logger.error("Specialities request timed out")
            return []
        except requests.exceptions.RequestException as e:
            logger.error(f"HTTP request error: {e}")
            return []
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            return []

    def close(self) -> None:
        """Close the session."""
        if self.session:
            self.session.close()

    def __del__(self) -> None:
        """Clean up resources on deletion."""
        with contextlib.suppress(Exception):
            self.close()
