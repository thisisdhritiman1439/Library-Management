# Replace `st.experimental_rerun()` with `st.rerun()` in Streamlit 1.25+
# Streamlit deprecated `st.experimental_rerun()`
# Here is the corrected final version of your login system

import streamlit as st
import pandas as pd
import os
import json
import hashlib
import datetime

# ------------------- Paths -------------------
BOOKS_FILE = "books_data.json"
USERS_FILE = "users.json"

# ------------------- Utility Functions -------------------
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

def load_users():
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, "r") as f:
                data = f.read().strip()
                if not data:
                    return []
                return json.loads(data)
        except json.JSONDecodeError:
            return []
    return []

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=4)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def login(username, password):
    users = load_users()
    hashed = hash_password(password)
    for user in users:
        if user["username"] == username and user["password"] == hashed:
            return user["role"]
    return None

def signup(username, password, role):
    users = load_users()
    for user in users:
        if user["username"] == username:
            return False
    users.append({"username": username, "password": hash_password(password), "role": role})
    save_users(users)
    return True

# ------------------- Streamlit App -------------------
st.set_page_config(page_title="Library System", page_icon="📚", layout="wide")

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "role" not in st.session_state:
    st.session_state.role = ""

if not st.session_state.logged_in:
    st.title("📚 Library Management System")
    st.subheader("Login as Student or Admin")
    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🔐 Login")
        login_user = st.text_input("Username", key="login_user")
        login_pass = st.text_input("Password", type="password", key="login_pass")
        if st.button("Login"):
            role = login(login_user, login_pass)
            if role:
                st.session_state.logged_in = True
                st.session_state.username = login_user
                st.session_state.role = role
                st.rerun()  # ✅ REPLACED experimental_rerun
            else:
                st.error("Invalid credentials.")

    with col2:
        st.subheader("📝 Sign Up")
        new_user = st.text_input("New Username", key="signup_user")
        new_pass = st.text_input("New Password", type="password", key="signup_pass")
        role = st.selectbox("Role", ["student", "admin"])
        if st.button("Sign Up"):
            if signup(new_user, new_pass, role):
                st.success("Account created! Please log in.")
            else:
                st.warning("Username already exists.")

# ------------------- Main Interface -------------------
if st.session_state.logged_in:
    books_df = load_books()

    menu = ["View Books", "Issue Book", "Return Book", "View Issued Books", "Logout"]
    if st.session_state.role == "admin":
        menu.insert(1, "Add Book")
        menu.insert(2, "Delete Book")

    choice = st.sidebar.radio("Menu", menu)

    if choice == "View Books":
        st.header("📘 All Books")
        st.dataframe(books_df)

    elif choice == "Add Book":
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
                    new = pd.DataFrame([{
                        "bid": bid, "title": title, "author": author, "category": category,
                        "status": "available", "issued_to": "", "issue_date": "", "due_date": ""
                    }])
                    books_df = pd.concat([books_df, new], ignore_index=True)
                    save_books(books_df)
                    st.success("Book added.")

    elif choice == "Delete Book":
        st.header("❌ Delete Book")
        bid = st.selectbox("Select Book ID", books_df["bid"])
        if st.button("Delete"):
            books_df = books_df[books_df["bid"] != bid]
            save_books(books_df)
            st.success("Book deleted.")

    elif choice == "Issue Book":
        st.header("📤 Issue Book")
        available = books_df[books_df["status"] == "available"]
        if available.empty:
            st.info("No books available.")
        else:
            bid = st.selectbox("Select Book", available["bid"], format_func=lambda x: f"{x} - {available[available['bid'] == x]['title'].values[0]}")
            student = st.session_state.username if st.session_state.role == "student" else st.text_input("Student Name")
            if st.button("Issue Book"):
                idx = books_df[books_df["bid"] == bid].index[0]
                today = datetime.date.today()
                due = today + datetime.timedelta(days=7)
                books_df.at[idx, "status"] = "issued"
                books_df.at[idx, "issued_to"] = student
                books_df.at[idx, "issue_date"] = str(today)
                books_df.at[idx, "due_date"] = str(due)
                save_books(books_df)
                st.success(f"Book issued to {student} (Due: {due})")

    elif choice == "Return Book":
        st.header("📥 Return Book")
        if st.session_state.role == "admin":
            issued = books_df[books_df["status"] == "issued"]
        else:
            issued = books_df[(books_df["status"] == "issued") & (books_df["issued_to"] == st.session_state.username)]

        if issued.empty:
            st.info("No issued books.")
        else:
            bid = st.selectbox("Select Book to Return", issued["bid"], format_func=lambda x: f"{x} - {issued[issued['bid'] == x]['title'].values[0]}")
            if st.button("Return Book"):
                idx = books_df[books_df["bid"] == bid].index[0]
                today = datetime.date.today()
                due = datetime.date.fromisoformat(books_df.at[idx, "due_date"])
                fine = max(0, (today - due).days * 5)
                books_df.at[idx, "status"] = "available"
                books_df.at[idx, "issued_to"] = ""
                books_df.at[idx, "issue_date"] = ""
                books_df.at[idx, "due_date"] = ""
                save_books(books_df)
                st.success("Book returned." if fine == 0 else f"Returned late! Fine ₹{fine}")

    elif choice == "View Issued Books":
        st.header("📋 Issued Books")
        issued = books_df[books_df["status"] == "issued"]
        if st.session_state.role != "admin":
            issued = issued[issued["issued_to"] == st.session_state.username]
        st.dataframe(issued)

    elif choice == "Logout":
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.session_state.role = ""
        st.success("Logged out.")
        st.rerun()  # ✅ Updated
