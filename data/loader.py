import pandas as pd


def load_tickets(filepath, limit=200):
    """
    Load and preprocess support tickets from a CSV file.

    Args:
        filepath (str): Path to the CSV file.
        limit (int): Maximum number of tickets to return.

    Returns:
        list[dict]: List of ticket dictionaries with:
            - id
            - subject
            - body
    """

    # Read CSV
    df = pd.read_csv(filepath)

    # Keep only English tickets
    df = df[df["language"] == "en"]

    # Drop rows where body is missing or empty
    df = df[df["body"].notna()]
    df = df[df["body"].str.strip() != ""]

    # Limit number of rows
    df = df.sample(n=limit, random_state=42)

    # Build output list
    tickets = [
        {
            "id": idx,
            "subject": row["subject"] if pd.notna(row["subject"]) else "",
            "body": row["body"],
        }
        for idx, row in df.iterrows()
    ]

    return tickets