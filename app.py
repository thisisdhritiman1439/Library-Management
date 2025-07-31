import streamlit as st
import json
import pandas as pd
from datetime import datetime, timedelta

# ------------------------------
# Utility Functions
# ------------------------------
def load_data():
    try:
        with open("books.json") as f:
            books = json.load(f)
    except FileNotFoundError:
        books = []

    try:
        with open("users.json") as f:
            users = json.load(f)
    except FileNotFoundError:
        users = {}

    try:
        with open("issued_books.json") as f:
            issued = json.load(f)
    except FileNotFoundError:
        issued = []

    return books, users, issued

def save_data(books, users, issued):
    with open("books.json", "w") as f:
        json.dump(books, f, indent=4)
    with open("users.json", "w") as f:
        json.dump(users, f, indent=4)
    with open("issued_books.json", "w") as f:
        json.dump(issued, f, indent=4)

# ------------------------------
# Authentication Functions
# ------------------------------
def signup(users):
    st.subheader("Sign Up")
    name = st.text_input("Name")
    email = st.text_input("Email")
    phone = st.text_input("Mobile Number")
    password = st.text_input("Password", type="password")
    role = st.selectbox("Role", ["Student", "Librarian"])
    if st.button("Create Account"):
        if email in users:
            st.error("User already exists.")
        else:
            users[email] = {"name": name, "phone": phone, "password": password, "role": role}
            st.success("Account created! Please login.")
    return users

def login(users):
    st.subheader("Login")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        user = users.get(email)
        if user and user["password"] == password:
            st.session_state["user"] = {"email": email, **user}
            st.success(f"Welcome {user['name']} ({user['role']})")
        else:
            st.error("Invalid credentials.")

# ------------------------------
# Book Management
# ------------------------------
def view_books(books):
    st.subheader("📚 Available Books")
    for book in books:
        with st.expander(f"{book['title']} by {book['author']}"):
            st.image(book.get("cover", ""), width=150)
            st.write(book.get("description", ""))
            st.markdown(f"**Category:** {book['category']}")
            st.markdown(f"**Status:** {'Available ✅' if book['status'] == 'YES' else 'Issued ❌'}")

def add_book(books):
    st.subheader("➕ Add New Book")
    bid = st.number_input("Book ID", step=1)
    title = st.text_input("Title")
    author = st.text_input("Author")
    category = st.text_input("Category")
    cover = st.text_input("Cover Image URL")
    description = st.text_area("Description")
    if st.button("Add Book"):
        books.append({"bid": bid, "title": title, "author": author, "category": category, "cover": cover, "description": description, "status": "YES"})
        st.success("✅ Book added.")
    return books

def delete_book(books):
    st.subheader("🗑️ Delete Book")
    bid = st.number_input("Enter Book ID to Delete", step=1)
    if st.button("Delete"):
        books = [b for b in books if b['bid'] != bid]
        st.success("✅ Book deleted.")
    return books

# ------------------------------
# Book Issuing / Returning
# ------------------------------
def issue_book(books, issued):
    st.subheader("📤 Issue Book")
    student = st.text_input("Student Email")
    bid = st.number_input("Book ID", step=1)
    if st.button("Issue"):
        for book in books:
            if book['bid'] == bid and book['status'] == 'YES':
                book['status'] = 'NO'
                issued.append({"email": student, "bid": bid, "issue_date": str(datetime.now().date()), "due_date": str((datetime.now() + timedelta(days=7)).date())})
                st.success("✅ Book issued.")
                return books, issued
        st.error("Book is not available or already issued.")
    return books, issued

def return_book(books, issued):
    st.subheader("📥 Return Book")
    bid = st.number_input("Enter Book ID to Return", step=1)
    if st.button("Return"):
        for book in books:
            if book['bid'] == bid:
                book['status'] = 'YES'
        issued = [record for record in issued if record['bid'] != bid]
        st.success("✅ Book returned.")
    return books, issued

def view_issued(issued):
    st.subheader("📄 Issued Book Records")
    if issued:
        st.dataframe(pd.DataFrame(issued))
    else:
        st.info("No books issued yet.")

# ------------------------------
# AI-like Book Recommendations
# ------------------------------
def recommend_books(books, issued):
    st.subheader("🤖 Book Recommendations")
    if issued:
        last = issued[-1]
        bid = last['bid']
        last_category = next((book['category'] for book in books if book['bid'] == bid), None)
        if last_category:
            recs = [b for b in books if b['category'] == last_category and b['status'] == 'YES']
            st.write(f"📚 Based on your last issue, here are books from '{last_category}' category:")
            for r in recs:
                st.markdown(f"- **{r['title']}** by {r['author']}")
        else:
            st.info("No recommendations available.")
    else:
        st.info("No issued book history found.")

# ------------------------------
# Main Streamlit App
# ------------------------------
def main():
    st.set_page_config(page_title="Library Management", layout="wide")
    st.title("📚 Library Management System")

    books, users, issued = load_data()

    if "user" not in st.session_state:
        login_tab, signup_tab = st.tabs(["🔑 Login", "📝 Sign Up"])
        with login_tab:
            login(users)
        with signup_tab:
            users = signup(users)
        save_data(books, users, issued)
        return

    user = st.session_state["user"]
    st.sidebar.markdown(f"**Logged in as:** {user['name']} ({user['role']})")
    menu = ["View Books", "Issued Books", "Return Book", "Recommend"]
    if user["role"] == "Librarian":
        menu.extend(["Add Book", "Delete Book", "Issue Book"])

    choice = st.sidebar.radio("📂 Menu", menu)

    if choice == "View Books":
        view_books(books)
    elif choice == "Issued Books":
        view_issued(issued)
    elif choice == "Return Book":
        books, issued = return_book(books, issued)
    elif choice == "Add Book":
        books = add_book(books)
    elif choice == "Delete Book":
        books = delete_book(books)
    elif choice == "Issue Book":
        books, issued = issue_book(books, issued)
    elif choice == "Recommend":
        recommend_books(books, issued)

    save_data(books, users, issued)

if __name__ == "__main__":
    main()
