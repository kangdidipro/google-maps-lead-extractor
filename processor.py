import pandas as pd
from datetime import datetime
import re

def save_data(data_list, keyword):
    """
    Processes the raw list into a cleaned Excel file.
    """
    if not data_list:
        print("⚠️ Warning: No data extracted to save.")
        return

    # Create DataFrame
    df = pd.DataFrame(data_list)
    
    # Drop duplicates based on Business Name
    df.drop_duplicates(subset=['Name'], inplace=True)
    
    # Create a safe filename based on the search keyword
    clean_keyword = re.sub(r'[^\w\s-]', '', keyword).strip().replace(" ", "_")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    filename = f"GLANCE_{clean_keyword}_{timestamp}.xlsx"
    
    try:
        # Exporting to Excel format
        df.to_excel(filename, index=False)
        print(f"\n💾 EXPORT SUCCESS: Data saved to '{filename}'")
    except Exception as e:
        print(f"❌ EXPORT ERROR: Could not save file due to: {e}")