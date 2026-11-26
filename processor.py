import pandas as pd
from datetime import datetime
import re
from utils import normalize_text, normalize_url

def save_data(data_list, keyword):
    """
    Processes the raw list into a cleaned Excel file.
    Deduplicates records with high integrity:
    1. Primary identity: Normalized Google Maps URL.
    2. Fallback identity: Normalized Name + Address (only when BOTH are present).
    3. Missing identity: Records missing URL AND missing (Name or Address) receive
       unique individual identities so they are not falsely collapsed together.
    Preserves multiple branches of businesses with the same name.
    """
    if not data_list:
        print("⚠️ Warning: No data extracted to save.")
        return

    # Create DataFrame
    df = pd.DataFrame(data_list)
    initial_count = len(df)

    # FIX 1 & FIX 3: Consistent high-integrity deduplication
    dedup_keys = []
    unidentified_count = 0

    for idx, row in df.iterrows():
        url_norm = normalize_url(row.get("Google Maps URL"))
        if url_norm:
            # 1. Primary identity: Normalized Google Maps URL
            dedup_keys.append(f"url:{url_norm}")
        else:
            name_norm = normalize_text(row.get("Name"))
            addr_norm = normalize_text(row.get("Address"))
            # 2. Fallback identity: only when BOTH Name and Address are valid
            if name_norm and addr_norm:
                dedup_keys.append(f"name_addr:{name_norm}|{addr_norm}")
            else:
                # 3. Insufficient identity info: assign unique key so it is NOT collapsed
                unidentified_count += 1
                dedup_keys.append(f"unique_unidentified:{idx}")

    if unidentified_count > 0:
        print(f"⚠️  DATA INTEGRITY NOTICE: {unidentified_count} record(s) have insufficient identity "
              f"(missing URL and Name/Address) and were preserved without deduplication.")

    df["_dedup_key"] = dedup_keys
    df.drop_duplicates(subset=["_dedup_key"], inplace=True)
    df.drop(columns=["_dedup_key"], inplace=True)

    # Re-index sequential numbering for 'No' column to match clean output rows
    df["No"] = range(1, len(df) + 1)

    # Create a safe filename based on the search keyword
    clean_keyword = re.sub(r'[^\w\s-]', '', keyword).strip().replace(" ", "_")
    if not clean_keyword:
        clean_keyword = "leads"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"GLANCE_{clean_keyword}_{timestamp}.xlsx"

    try:
        # Exporting to Excel format
        df.to_excel(filename, index=False)
        print(f"💾 EXPORT SUCCESS: {len(df)} records saved to '{filename}' (Original: {initial_count})")
    except Exception as e:
        print(f"❌ EXPORT ERROR: Could not save file due to: {e}")
