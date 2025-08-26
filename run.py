#!/usr/bin/env python3
"""
Unified runner script for the Schedule Processor project.
"""

import argparse
import asyncio


def run_api_processor():
    """Run the API-based schedule processor."""
    from main_api import main
    return main()


def run_bot():
    """Run the Telegram bot."""
    from bot_main import main
    return asyncio.run(main())


def run_legacy_processor():
    """Run the legacy file-based processor."""
    from script import main
    main()
    return 0


def run_test():
    """Run bot API tests."""
    from test_bot import test_api_functions
    return asyncio.run(test_api_functions())


def main():
    parser = argparse.ArgumentParser(description="Schedule Processor Runner")
    parser.add_argument(
        "mode",
        choices=["api", "bot", "legacy", "test"],
        help="Choose what to run: api (API processor), bot (Telegram bot), legacy (file processor), test (API tests)"
    )
    
    args = parser.parse_args()
    
    print(f"🚀 Starting Schedule Processor in {args.mode} mode...\n")
    
    try:
        if args.mode == "api":
            return run_api_processor()
        elif args.mode == "bot":
            return run_bot()
        elif args.mode == "legacy":
            return run_legacy_processor()
        elif args.mode == "test":
            run_test()
            return 0
    except KeyboardInterrupt:
        print("\n⏹️ Interrupted by user")
        return 0
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1


if __name__ == "__main__":
    exit(main())