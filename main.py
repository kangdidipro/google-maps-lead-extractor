import argparse
import asyncio
import sys
from scraper import get_google_maps_data
from processor import save_data

def positive_int(val):
    """Validator ensuring an argument is a positive integer greater than zero."""
    try:
        ival = int(val)
        if ival <= 0:
            raise argparse.ArgumentTypeError(f"Value must be a positive integer > 0, got {val}")
        return ival
    except ValueError:
        raise argparse.ArgumentTypeError(f"Invalid integer: '{val}'")

def parse_args():
    """
    Parses CLI parameters with support for both modern named flags and legacy multi-word keywords.
    """
    parser = argparse.ArgumentParser(
        prog="python main.py",
        description="G-LANCE PRO — Google Maps B2B Lead Extractor CLI",
        epilog="Examples:\n"
               "  python main.py \"Coffee Shop New York\"\n"
               "  python main.py \"Coffee Shop New York\" --limit 50\n"
               "  python main.py \"Restaurant Jakarta\" --limit 100 --scrolls 15\n"
               "  python main.py \"Real Estate London\" --limit 50 --headless\n"
               "  python main.py newyork caffee\n",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        "keyword",
        nargs="+",
        help="Business search keyword (e.g. 'Coffee Shop New York', 'Dentist Surabaya')"
    )
    parser.add_argument(
        "--limit",
        type=positive_int,
        default=20,
        help="Maximum number of business leads to process (default: 20, positive integer)"
    )
    parser.add_argument(
        "--scrolls",
        type=positive_int,
        default=5,
        help="Number of scrolling operations to load results (default: 5, positive integer)"
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        default=False,
        help="Run browser in headless background mode (default: False)"
    )

    return parser.parse_args()

async def main():
    """
    Main entry point for G-LANCE CLI.
    """
    args = parse_args()
    search_keyword = " ".join(args.keyword)

    print("\n========================================================")
    print("           G-LANCE PRO — LEAD EXTRACTOR                 ")
    print("========================================================")
    print(f"🎯 Target Keyword : {search_keyword}")
    print(f"📊 Target Limit   : {args.limit}")
    print(f"📜 Scroll Count   : {args.scrolls}")
    print(f"🖥️  Headless Mode  : {args.headless}")
    print("========================================================\n")

    # Step 1: Run the Scraper
    raw_data = await get_google_maps_data(
        keyword=search_keyword,
        limit=args.limit,
        scrolls=args.scrolls,
        headless=args.headless
    )

    # Step 2: Process and Save to Excel
    if raw_data:
        save_data(raw_data, search_keyword)
    else:
        print("ℹ️  No data extracted to export.")

    print("\n--- G-LANCE PRO: SESSION FINISHED ---\n")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Session interrupted by user.")
        sys.exit(0)
