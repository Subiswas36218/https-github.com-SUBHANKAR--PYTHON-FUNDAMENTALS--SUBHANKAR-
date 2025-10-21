from typing import List, Dict, Any, Union

def process_users(users: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Process a list of user dictionaries:
    - Ensure 'age' and 'salary' are ints
    - Replace invalid emails with None
    - Return a new list of cleaned users
    """
    cleaned_users: List[Dict[str, Any]] = []

    for user in users:
        # Type-safe extraction
        user_id: int = int(user.get("user_id", 0))
        age: int = int(user.get("age", 0))
        salary: int = int(user.get("salary", 0))
        email: Union[str, None] = user.get("email")
        if email == "None":
            email = None

        signup_date: str = user.get("signup_date", "Invalid")

        cleaned_users.append({
            "user_id": user_id,
            "age": age,
            "salary": salary,
            "email": email,
            "signup_date": signup_date
        })

    return cleaned_users


def main() -> None:
   
    users: List[Dict[str, Any]] = [
        {"user_id": 1, "age": 25, "salary": 50000, "email": "alice@example.com", "signup_date": "2025-01-10"},
        {"user_id": 2, "age": 30, "salary": 60000, "email": "bob@example.com", "signup_date": "2025-02-12"},
        {"user_id": 1, "age": 25, "salary": 50000, "email": "charlie@example.com", "signup_date": "2025-03-10"},
        {"user_id": 3, "age": 35, "salary": 70000, "email": "None", "signup_date": "2025-04-15"},
        {"user_id": 2, "age": 30, "salary": 60000, "email": "dave@example.com", "signup_date": "Invalid"},
        {"user_id": 1, "age": 25, "salary": 50000, "email": "alex@example.com", "signup_date": "2025-01-10"}
    ]

    print("=== Original Data ===")
    for u in users:
        print(u)

    cleaned_users = process_users(users)

    print("\n=== Cleaned Data ===")
    for u in cleaned_users:
        print(u)

    total_salary: int = sum(u["salary"] for u in cleaned_users)
    avg_age: float = sum(u["age"] for u in cleaned_users) / len(cleaned_users)

    print(f"\nTotal Salary: {total_salary}")
    print(f"Average Age: {avg_age:.2f}")


if __name__ == "__main__":
    main()
