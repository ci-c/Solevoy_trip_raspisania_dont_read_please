"""Main script for API-based schedule processing."""

import logging
from schedule_processor.core import process_api_schedule

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    """Main function for getting, processing and exporting schedule."""
    # Example configuration - these would normally come from command line args or config
    schedule_config = {
        "speciality": ["32.05.01 медико-профилактическое дело"],
        "semester": ["весенний"],
        "course_number": ["2"],
        "academic_year": ["2024/2025"],
        "subgroup_name": "202б"
    }
    
    logger.info("Starting schedule processing...")
    
    success = process_api_schedule(**schedule_config)
    
    if success:
        logger.info("Schedule processing completed successfully!")
    else:
        logger.error("Schedule processing failed!")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())