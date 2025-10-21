import numpy as np

def main() -> None:
  
    user_ids = np.array([1, 2, 1, 3, 2, 1])
    ages = np.array([25, 30, 25, 35, 30, 25])
    salaries = np.array([50000, 60000, 50000, 70000, 60000, 50000])
    emails = np.array(["alice@example.com", "bob@example.com", "charlie@example.com",
                       "None", "dave@example.com", "alex@example.com"])
    signup_dates = np.array(["2025-01-10", "2025-02-12", "2025-03-10",
                             "2025-04-15", "Invalid", "2025-01-10"])

    print("=== Original Data ===")
    for i in range(len(user_ids)):
        print(user_ids[i], ages[i], salaries[i], emails[i], signup_dates[i])

    # --- 2. Clean the data ---
    # Replace invalid emails with None
    emails_clean = np.where(emails == "None", None, emails)

    # Convert valid signup_dates to NumPy datetime64, invalid become NaT
    signup_dates_clean = np.array([
        np.datetime64(date) if date != "Invalid" else np.datetime64("NaT")
        for date in signup_dates
    ])

    print("\n=== Cleaned Data ===")
    for i in range(len(user_ids)):
        print(user_ids[i], ages[i], salaries[i], emails_clean[i], signup_dates_clean[i])

    # --- 3. Basic analysis ---
    print("\n=== Analysis ===")
    print("Average Age:", np.mean(ages))
    print("Average Salary:", np.mean(salaries))
    print("Max Salary:", np.max(salaries))
    print("Min Salary:", np.min(salaries))

    # --- 4. Derived computation: scale salaries ---
    salaries_scaled = (salaries - np.mean(salaries)) / np.std(salaries)
    print("\n=== Scaled Salaries ===")
    print(salaries_scaled)


if __name__ == "__main__":
    main()
