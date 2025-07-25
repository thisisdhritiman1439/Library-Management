import streamlit as st
import pandas as pd
import os
import json
import datetime

# ----------------------
# File Paths
# ----------------------
BOOKS_FILE = "books_data.json"
USERS_FILE = "users.json"

# ----------------------
# Load/Save Books
# ----------------------
def load_books():
    if os.path.exists(BOOKS_FILE):
        with open(BOOKS_FILE, "r") as f:
            data = json.load(f)
        df = pd.DataFrame(data)
        for col in ["issued_to", "issue_date", "due_date"]:
            if col not in df.columns:
                df[col] = ""
    else:
        df = pd.DataFrame(columns=["bid", "title", "author", "category", "status", "issued_to", "issue_date", "due_date"])
    return df

def save_books(df):
    with open(BOOKS_FILE, "w") as f:
        json.dump(df.to_dict(orient="records"), f, indent=4)

# ----------------------
# Load/Save Users
# ----------------------
def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    else:
        return []

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=4)

# ----------------------
# Authentication
# ----------------------
def login(username, password):
    users = load_users()
    for user in users:
        if user["username"] == username and user["password"] == password:
            return True
    return False

def signup(username, password):
    users = load_users()
    for user in users:
        if user["username"] == username:
            return False  # User exists
    users.append({"username": username, "password": password})
    save_users(users)
    return True

# ----------------------
# Main App Interface
# ----------------------
st.set_page_config(page_title="Library System", page_icon="📚", layout="wide")
st.title("📚 Library Management System (with Login)")

# ----------------------
# Session State: Auth
# ----------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""

# ----------------------
# Login / Signup Forms
# ----------------------
if not st.session_state.logged_in:
    option = st.radio("Login or Sign Up", ["Login", "Sign Up"])

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if option == "Login":
        if st.button("Login"):
            if login(username, password):
                st.session_state.logged_in = True
                st.session_state.username = username
                st.success("Logged in successfully!")
                st.experimental_rerun()
            else:
                st.error("Invalid credentials.")
    else:
        if st.button("Sign Up"):
            if signup(username, password):
                st.success("Account created. You can now log in.")
            else:
                st.warning("Username already exists.")

# ----------------------
# Main Library Dashboard
# ----------------------
if st.session_state.logged_in:

    books_df = load_books()
    menu = st.sidebar.radio("Menu", ["View Books", "Add Book", "Delete Book", "Issue Book", "Return Book", "View Issued Books", "Logout"])

    # View Books
    if menu == "View Books":
        st.header("📘 All Books")
        st.dataframe(books_df)

    # Add Book
    elif menu == "Add Book":
        st.header("➕ Add Book")
        bid = st.number_input("Book ID", min_value=1, step=1)
        title = st.text_input("Title")
        author = st.text_input("Author")
        category = st.text_input("Category")

        if st.button("Add Book"):
            if bid and title and author and category:
                if bid in books_df["bid"].values:
                    st.error("Book ID already exists.")
                else:
                    new_book = pd.DataFrame([{
                        "bid": bid,
                        "title": title,
                        "author": author,
                        "category": category,
                        "status": "available",
                        "issued_to": "",
                        "issue_date": "",
                        "due_date": ""
                    }])
                    books_df = pd.concat([books_df, new_book], ignore_index=True)
                    save_books(books_df)
                    st.success("Book added.")
            else:
                st.warning("Fill all fields.")

    # Delete Book
    elif menu == "Delete Book":
        st.header("❌ Delete Book")
        bid = st.selectbox("Select Book ID to Delete", options=books_df["bid"])

        if st.button("Delete"):
            books_df = books_df[books_df["bid"] != bid]
            save_books(books_df)
            st.success("Book deleted.")

    # Issue Book
    elif menu == "Issue Book":
        st.header("📤 Issue Book")
        available_books = books_df[books_df["status"] == "available"]

        if available_books.empty:
            st.info("No books available.")
        else:
            bid = st.selectbox(
                "Select Book",
                options=available_books["bid"],
                format_func=lambda x: f"{x} - {available_books[available_books['bid'] == x]['title'].values[0]}"
            )
            student = st.text_input("Student Name")

            if st.button("Issue Book"):
                idx = books_df[books_df["bid"] == bid].index[0]
                books_df.at[idx, "status"] = "issued"
                books_df.at[idx, "issued_to"] = student
                today = datetime.date.today()
                due = today + datetime.timedelta(days=7)
                books_df.at[idx, "issue_date"] = str(today)
                books_df.at[idx, "due_date"] = str(due)
                save_books(books_df)
                st.success(f"Issued to {student} (Due: {due})")

    # Return Book
    elif menu == "Return Book":
        st.header("📥 Return Book")
        issued_books = books_df[books_df["status"] == "issued"]

        if issued_books.empty:
            st.info("No issued books.")
        else:
            bid = st.selectbox(
                "Select Book",
                options=issued_books["bid"],
                format_func=lambda x: f"{x} - {issued_books[issued_books['bid'] == x]['title'].values[0]} (to {issued_books[issued_books['bid'] == x]['issued_to'].values[0]})"
            )

            if st.button("Return Book"):
                idx = books_df[books_df["bid"] == bid].index[0]
                today = datetime.date.today()
                due_date = datetime.date.fromisoformat(books_df.at[idx, "due_date"])
                days_late = (today - due_date).days
                fine = days_late * 5 if days_late > 0 else 0

                books_df.at[idx, "status"] = "available"
                books_df.at[idx, "issued_to"] = ""
                books_df.at[idx, "issue_date"] = ""
                books_df.at[idx, "due_date"] = ""
                save_books(books_df)

                if fine > 0:
                    st.warning(f"Returned late! Fine: ₹{fine}")
                else:
                    st.success("Book returned on time.")

    # View Issued Books
    elif menu == "View Issued Books":
        st.header("📋 Issued Books")
        issued = books_df[books_df["status"] == "issued"]
        if issued.empty:
            st.info("No books are issued.")
        else:
            st.dataframe(issued[["bid", "title", "author", "category", "issued_to", "issue_date", "due_date"]])

    # Logout
    elif menu == "Logout":
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.success("Logged out.")
        st.experimental_rerun()

