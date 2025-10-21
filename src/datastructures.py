from typing import List, Dict, Any

def clean_users(users: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Cleans user data:
    - Replaces invalid emails with None
    - Ensures ages and salaries are integers
    """
    cleaned = []
    for user in users:
        # Ensure types
        user_id = int(user.get("user_id", 0))
        age = int(user.get("age", 0))
        salary = int(user.get("salary", 0))
        email = user.get("email")
        if email == "None":
            email = None
        signup_date = user.get("signup_date", "Invalid")
        
        cleaned.append({
            "user_id": user_id,
            "age": age,
            "salary": salary,
            "email": email,
            "signup_date": signup_date
        })
    return cleaned

def analyze_users(users: List[Dict[str, Any]]) -> None:
    """
    Performs simple analysis:
    - Total salary
    - Average age
    - Unique emails
    """
    total_salary = sum(u["salary"] for u in users)
    avg_age = sum(u["age"] for u in users) / len(users)
    
    # Collect unique emails (ignoring None)
    emails = set(u["email"] for u in users if u["email"] is not None)
    
    print("\n=== Analysis ===")
    print(f"Total Salary: {total_salary}")
    print(f"Average Age: {avg_age:.2f}")
    print(f"Unique Emails: {emails}")


def main() -> None:
    # --- 1. Sample messy user data ---
    users = [
        {"user_id": 1, "age": 25, "salary": 50000, "email": "alice@example.com", "signup_date": "2025-01-10"},
        {"user_id": 2, "age": 30, "salary": 60000, "email": "bob@example.com", "signup_date": "2025-02-12"},
        {"user_id": 1, "age": 25, "salary": 50000, "email": "charlie@example.com", "signup_date": "2025-03-10"},
        {"user_id": 3, "age": 35, "salary": 70000, "email": "None", "signup_date": "2025-04-15"},
        {"user_id": 2, "age": 30, "salary": 60000, "email": "dave@example.com", "signup_date": "Invalid"},
        {"user_id": 1, "age": 25, "salary": 50000, "email": "alex@example.com", "signup_date": "2025-01-10"}
    ]
    
    print("=== Original Users ===")
    for u in users:
        print(u)
    
    # --- 2. Clean the data ---
    cleaned_users = clean_users(users)
    
    print("\n=== Cleaned Users ===")
    for u in cleaned_users:
        print(u)
    
    # --- 3. Analyze the data ---
    analyze_users(cleaned_users)


if __name__ == "__main__":
    main()
