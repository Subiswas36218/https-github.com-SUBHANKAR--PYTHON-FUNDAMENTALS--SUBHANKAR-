from typing import Any
import pandas as pd
import numpy as np


def create_data() -> pd.DataFrame:
  
    data = pd.DataFrame({
        "user_id": [1, 2, 1, 3, 2, 1],
        "age": [25, 30, 25, 35, 30, 25],
        "salary": [50000, 60000, 50000, 70000, 60000, 50000],
        "email": [
            "alice@example.com",
            "bob@example.com",
            "charlie@example.com",
            "None",
            "dave@example.com",
            "alex@example.com"
        ],
        "signup_date": [
            "2025-01-10",
            "2025-02-12",
            "2025-03-10",
            "2025-04-15",
            "Invalid",
            "2025-01-10"
        ]
    })
    return data


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
   
    # Replace 'None' emails with NaN
    df["email"].replace("None", np.nan, inplace=True)

    # Convert signup_date to datetime, invalid entries become NaT
    df["signup_date"] = pd.to_datetime(df["signup_date"], errors="coerce")
    
    return df


def analyze_data(df: pd.DataFrame) -> None:
   
    print("\n=== Analysis ===")
    print(f"Average Age: {df['age'].mean():.2f}")
    print(f"Average Salary: {df['salary'].mean():.2f}")
    print(f"Max Salary: {df['salary'].max()}")
    print(f"Min Salary: {df['salary'].min()}")

    # Derived column: scaled salary (z-score)
    df["salary_scaled"] = (df["salary"] - df["salary"].mean()) / df["salary"].std()
    print("\n=== DataFrame with Scaled Salary ===")
    print(df)


def main() -> None:
    # 1. Create data
    df = create_data()
    print("=== Original Data ===")
    print(df)

    # 2. Clean data
    df = clean_data(df)
    print("\n=== Cleaned Data ===")
    print(df)

    # 3. Analyze data
    analyze_data(df)


if __name__ == "__main__":
    main()
