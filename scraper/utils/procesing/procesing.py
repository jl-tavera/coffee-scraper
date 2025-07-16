import re 

def get_total_items(total_text: str) -> int:
    """
    Extracts the total number of items from the pagination text.
    """
    match = re.search(r"of\s+(\d+)", total_text)
    if not match:
        raise ValueError("Couldn't extract total product count.")
    total_items = int(match.group(1))

    return total_items