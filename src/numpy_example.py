from __future__ import annotations

import numpy as np


def main() -> None:
    user_ids = np.array([1, 2, 1, 3, 2, 1])
    ages = np.array([25, 30, 25, 35, 30, 25])
    salaries = np.array([50000, 60000, 50000, 70000, 60000, 50000])

    emails = np.array(
        [
            "alice@example.com",
            "bob@example.com",
            "charlie@example.com",
            "None",
            "dave@example.com",
            "alex@example.com",
        ],
        dtype=object,
    )

    signup_dates = np.array(
        [
            "2025-01-10",
            "2025-02-12",
            "2025-03-10",
            "2025-04-15",
            "Invalid",
            "2025-01-10",
        ],
        dtype=object,
    )

    print("=== Original Data ===")
    for i in range(len(user_ids)):
        print(user_ids[i], ages[i], salaries[i], emails[i], signup_dates[i])

    # -----------------------------
    # 2. Clean the data
    # -----------------------------

    # Replace invalid emails with None (requires dtype=object)
    none_array = np.array([None] * len(emails), dtype=object)
    emails_clean = np.where(emails == "None", none_array, emails)

    # Convert signup_dates → datetime64, invalid → NaT
    signup_dates_clean = np.array(
        [
            np.datetime64(date) if date != "Invalid" else np.datetime64("NaT")
            for date in signup_dates
        ],
        dtype="datetime64[ns]",
    )

    print("\n=== Cleaned Data ===")
    for i in range(len(user_ids)):
        print(
            user_ids[i],
            ages[i],
            salaries[i],
            emails_clean[i],
            signup_dates_clean[i],
        )

    # -----------------------------
    # 3. Basic analysis
    # -----------------------------
    print("\n=== Analysis ===")
    print("Average Age:", float(np.mean(ages)))
    print("Average Salary:", float(np.mean(salaries)))
    print("Max Salary:", int(np.max(salaries)))
    print("Min Salary:", int(np.min(salaries)))

    # -----------------------------
    # 4. Scale salaries
    # -----------------------------
    salaries_scaled = (salaries - np.mean(salaries)) / np.std(salaries)

    print("\n=== Scaled Salaries ===")
    print(salaries_scaled)


if __name__ == "__main__":
    main()
