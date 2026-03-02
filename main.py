import asyncio
import sys
from scraper import get_google_maps_data
from processor import save_data

async def main():
    """
    Main entry point for G-LANCE CLI.
    Example: python main.py "Real Estate Agents in London"
    """
    # Check if keyword is provided in the command line
    if len(sys.argv) < 2:
        print("\n❌ USAGE ERROR: Missing Search Keyword!")
        print("Command: python main.py \"Your Target Keyword\"")
        print("Example: python main.py \"Software House Singapore\"\n")
        return

    # Join multiple words if quotes are missing (e.g., python main.py Real Estate)
    search_keyword = " ".join(sys.argv[1:])
    
    print(f"\n--- G-LANCE PRO: STARTING SESSION ---")
    
    # Step 1: Run the Scraper
    raw_data = await get_google_maps_data(search_keyword)
    
    # Step 2: Process and Save to Excel
    if raw_data:
        save_data(raw_data, search_keyword)
    
    print("--- G-LANCE PRO: SESSION FINISHED ---\n")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Session interrupted by user.")