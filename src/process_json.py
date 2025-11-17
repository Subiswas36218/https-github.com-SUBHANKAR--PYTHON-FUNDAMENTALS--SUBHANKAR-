import json
from typing import Any

import numpy as np
import pandas as pd


def main() -> None:
    """
    Demonstrates JSON → DataFrame → cleaning → analysis.
    """

    json_data = """
    [
        {
            "user_id": 1,
            "age": 25,
            "salary": 50000,
            "email": "alice@example.com",
            "signup_date": "2025-01-10"
        },
        {
            "user_id": 2,
            "age": 30,
            "salary": 60000,
            "email": "bob@example.com",
            "signup_date": "2025-02-12"
        },
        {
            "user_id": 1,
            "age": 25,
            "salary": 50000,
            "email": "charlie@example.com",
            "signup_date": "2025-03-10"
        },
        {
            "user_id": 3,
            "age": 35,
            "salary": 70000,
            "email": "None",
            "signup_date": "2025-04-15"
        },
        {
            "user_id": 2,
            "age": 30,
            "salary": 60000,
            "email": "dave@example.com",
            "signup_date": "Invalid"
        },
        {
            "user_id": 1,
            "age": 25,
            "salary": 50000,
            "email": "alex@example.com",
            "signup_date": "2025-01-10"
        }
    ]
    """

    # Load JSON data
    raw: Any = json.loads(json_data)
    df = pd.DataFrame(raw)

    print("=== Original DataFrame ===")
    print(df)

    # Convert signup_date → datetime, invalid → NaT
    df["signup_date"] = pd.to_datetime(df["signup_date"], errors="coerce")

    # Replace "None" email entries with NaN
    df["email"].replace("None", np.nan, inplace=True)

    print("\n=== Cleaned DataFrame ===")
    print(df)

    # Basic analysis

    print("\n=== Analysis ===")
    print("Average Age:", float(df["age"].mean()))
    print("Average Salary:", float(df["salary"].mean()))

    # Derived column: scaled salary
    df["salary_scaled"] = (df["salary"] - df["salary"].mean()) / df["salary"].std()

    print("\n=== DataFrame with Scaled Salary ===")
    print(df)


if __name__ == "__main__":
    main()
