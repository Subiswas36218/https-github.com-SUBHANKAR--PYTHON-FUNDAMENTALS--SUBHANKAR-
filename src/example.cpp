
#include <iostream>
#include <vector>
#include <string>
#include <algorithm> // for max, min
#include <numeric>   // for accumulate

struct User {
    int user_id;
    int age;
    int salary;
    std::string email;
    std::string signup_date;
};

int main() {
    // --- 1. Original messy data ---
    std::vector<User> users = {
        {1, 25, 50000, "alice@example.com", "2025-01-10"},
        {2, 30, 60000, "bob@example.com", "2025-02-12"},
        {1, 25, 50000, "charlie@example.com", "2025-03-10"},
        {3, 35, 70000, "None", "2025-04-15"},
        {2, 30, 60000, "dave@example.com", "Invalid"},
        {1, 25, 50000, "alex@example.com", "2025-01-10"}
    };

    std::cout << "=== Original Data ===\n";
    for (const auto& u : users) {
        std::cout << u.user_id << " " << u.age << " " << u.salary
                  << " " << u.email << " " << u.signup_date << "\n";
    }

    // --- 2. Clean data ---
    for (auto& u : users) {
        if (u.email == "None") {
            u.email = ""; // Replace "None" with empty string
        }
        if (u.signup_date == "Invalid") {
            u.signup_date = ""; // Replace invalid date with empty string
        }
    }

    std::cout << "\n=== Cleaned Data ===\n";
    for (const auto& u : users) {
        std::cout << u.user_id << " " << u.age << " " << u.salary
                  << " " << u.email << " " << u.signup_date << "\n";
    }

    // --- 3. Basic analysis ---
    double total_salary = 0;
    double total_age = 0;
    int n = users.size();
    int max_salary = users[0].salary;
    int min_salary = users[0].salary;

    for (const auto& u : users) {
        total_salary += u.salary;
        total_age += u.age;
        if (u.salary > max_salary) max_salary = u.salary;
        if (u.salary < min_salary) min_salary = u.salary;
    }

    double avg_age = total_age / n;
    double avg_salary = total_salary / n;

    std::cout << "\n=== Analysis ===\n";
    std::cout << "Total Salary: " << total_salary << "\n";
    std::cout << "Average Age: " << avg_age << "\n";
    std::cout << "Max Salary: " << max_salary << "\n";
    std::cout << "Min Salary: " << min_salary << "\n";

    // --- 4. Derived computation: scaled salary ---
    std::vector<double> salaries_scaled;
    double mean = avg_salary;
    double sum_sq_diff = 0;
    for (const auto& u : users) {
        sum_sq_diff += (u.salary - mean) * (u.salary - mean);
    }
    double std_dev = std::sqrt(sum_sq_diff / n);

    for (const auto& u : users) {
        salaries_scaled.push_back((u.salary - mean) / std_dev);
    }

    std::cout << "\n=== Scaled Salaries ===\n";
    for (double s : salaries_scaled) {
        std::cout << s << " ";
    }
    std::cout << "\n";

    return 0;
}
