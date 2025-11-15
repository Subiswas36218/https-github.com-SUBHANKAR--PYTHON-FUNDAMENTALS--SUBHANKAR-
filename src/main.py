from src.utils.add import add

from src.usecases.export_articles import export_from_db
from src.usecases.import_articles import load_data_from_csv
from src.usecases.search_text import search_articles
from src.pymongo_example import list_users, get_user_by_username

from pathlib import Path


def main() -> None:
    print("\n=== PythonDE Project Launcher ===")
    print("1. Export SQL → MongoDB")
    print("2. Load CSV into SQL")
    print("3. Search text inside MongoDB articles")
    print("4. List Mongo users (pymongo_example)")
    print("5. Test utils.add()")
    print("0. Exit")

    choice = input("\nSelect an option: ")

    if choice == "1":
        print("\nRunning SQL → Mongo Export...\n")
        export_from_db()

    elif choice == "2":
        print("\nLoading CSV into MariaDB...")
        load_data_from_csv(Path("data/articles.csv"))

    elif choice == "3":
        query = input("Enter search text: ")
        print("\nSearching MongoDB articles...\n")
        results = search_articles(query)
        for r in results:
            print(f"Match → {r.arxiv_id}: {r.title}")

    elif choice == "4":
        print("\nListing Mongo Users:")
        users = list_users()
        for u in users:
            print(f"- {u.username} ({u.email})")

    elif choice == "5":
        print("\nTesting utils.add():")
        print("add(5, 10) →", add(5, 10))

    elif choice == "0":
        print("Exiting.")
        return

    else:
        print("Invalid choice.")

    print("\nDone.\n")


if __name__ == "__main__":
    main()
