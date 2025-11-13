import pandas as pd


def main() -> None:
    dates = pd.date_range("2025-01-01", periods=6, freq="D")

    messy_data = pd.DataFrame(
        {
            "user_id": [1, 2, 1, 3, 2, 1],
            "age": [25, 30, 25, 35, 30, 25],
            "salary": [50000, 60000, 50000, 70000, 60000, 50000],
            "email": [
                "alice@example.com",
                "bob@example.com",
                "charlie@example.com",
                "None",
                "dave@example.com",
                "alex@example.com",
            ],
            "signup_date": [
                "2025-01-10",
                "2025-02-12",
                "2025-03-10",
                "2025-04-15",
                "Invalid",
                "2025-01-10",
            ],
            "last_login": dates.tolist(),
        }
    )

    # Display the DataFrame
    print("=== Messy DataFrame ===")
    print(messy_data)

    # Show data info
    print("\n=== DataFrame Info ===")
    messy_data.info()

    # Try converting signup_date to datetime (to highlight issues)
    messy_data["signup_date"] = pd.to_datetime(
        messy_data["signup_date"], errors="coerce"
    )

    print("\n=== After Cleaning signup_date ===")
    print(messy_data)


if __name__ == "__main__":
    main()
