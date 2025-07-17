import re 
import json
import pandas as pd


def get_total_items(total_text: str) -> int:
    """
    Extracts the total number of items from the pagination text.
    """
    match = re.search(r"of\s+(\d+)", total_text)
    if not match:
        raise ValueError("Couldn't extract total product count.")
    total_items = int(match.group(1))

    return total_items


def products_to_df(products:list) -> pd.DataFrame:
    """
    Converts a list of product dictionaries to a pandas DataFrame.
    """
    df = pd.DataFrame(products)
    df["price"] = df["price"].apply(_parse_price_column)
    df["sale_price"] = df["sale_price"].apply(_parse_price_column)
    df.sort_values(by="price", inplace=True, ignore_index=True)

    for _, row in df.head(5).iterrows():
        print(f"{row['title']} - ${row['price']:.2f} - {row['brand']}")

    df.to_csv("./data/products.csv", index=False)
    return df


def details_to_df(products: list[dict]) -> pd.DataFrame:
    """
    Converts a list of product dictionaries to a pandas DataFrame
    and saves it as a clean CSV with flattened structures.
    """
    records = []
    for product in products:
        record = {
            "brand": product.get("brand"),
            "title": product.get("title"),
            "price": product.get("price"),
            "image": product.get("images", [None])[0],
            "stock": product.get("stock", ""),
            "description": product.get("description", "").replace("\n", " ").strip(),
            "specifications": json.dumps(product.get("specifications", {}), ensure_ascii=False),
            "reviews": json.dumps(product.get("reviews", {}), ensure_ascii=False),
            "questions": json.dumps(product.get("questions", []), ensure_ascii=False),
            "questions_count": len(product.get("questions", [])),
        }

        details = product.get("details", {})
        for k, v in details.items():
            record[f"details_{k.lower()}"] = v

        records.append(record)

    df = pd.DataFrame(records)
    df.to_csv("./data/product_details.csv", sep=';', index=False, encoding="utf-8")


def _parse_price_column(price: str) -> float:
    """
    Converts a price string like '$399.95' to a float.
    Returns 0.0 if the string is empty or invalid.
    """
    if not price or not isinstance(price, str):
        return 0.0
    price = price.replace("$", "").replace(",", "").strip()
    try:
        return float(price)
    except ValueError:
        return 0.0
