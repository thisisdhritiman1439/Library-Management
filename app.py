# Library Management System Using Streamlit

import streamlit as st
import pandas as pd
import json
import datetime
from PIL import Image

# File paths
USERS_FILE = "users.json"
BOOKS_FILE = "books.json"
ISSUED_FILE = "issued.json"
FAVORITES_FILE = "favorites.json"

# Utility functions
def load_json(file):
    try:
        with open(file, 'r') as f:
            return json.load(f)
    except:
        return []

def save_json(file, data):
    with open(file, 'w') as f:
        json.dump(data, f, indent=4)

def generate_id(data_list):
    return max([item.get("id", 0) for item in data_list], default=0) + 1

if 'user' not in st.session_state:
    st.session_state.user = None

# Sign up function
def signup():
    st.subheader("Sign Up")
    name = st.text_input("Full Name")
    email = st.text_input("Email")
    mobile = st.text_input("Mobile Number")
    password = st.text_input("Password", type="password")
    role = st.selectbox("Select Role", ["Student", "Librarian", "Other"])
    if st.button("Create Account"):
        users = load_json(USERS_FILE)
        if any(u['email'] == email for u in users):
            st.error("User already exists.")
        else:
            users.append({"name": name, "email": email, "mobile": mobile, "password": password, "role": role})
            save_json(USERS_FILE, users)
            st.success("Account created. Please login.")

# Login function
def login():
    st.subheader("Login")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        users = load_json(USERS_FILE)
        user = next((u for u in users if u['email'] == email and u['password'] == password), None)
        if user:
            st.session_state.user = user
            st.success(f"Welcome {user['name']} ({user['role']})")
        else:
            st.error("Invalid login details.")

# View books
def view_books():
    st.subheader("Library Books")
    books = load_json(BOOKS_FILE)
    for book in books:
        with st.expander(f"{book['title']} by {book['author']}"):
            st.image(book['cover'], width=120)
            st.write(f"**Description**: {book['description']}")
            st.write(f"**Index**: {book['index']}")
            st.write(f"**Availability**: {'Available' if book['available'] else 'Issued'}")
            if st.session_state.user and st.session_state.user['role'] != 'Librarian':
                if st.button(f"Add to My List - {book['id']}"):
                    favorites = load_json(FAVORITES_FILE)
                    favorites.append({"email": st.session_state.user['email'], "book_id": book['id']})
                    save_json(FAVORITES_FILE, favorites)
                    st.success("Book added to your list.")

# Add book (librarian only)
def add_book():
    if st.session_state.user['role'] != 'Librarian':
        st.warning("Only librarians can add books.")
        return
    st.subheader("Add New Book")
    title = st.text_input("Title")
    author = st.text_input("Author")
    description = st.text_area("Description")
    index = st.text_area("Index Page")
    cover = st.text_input("Cover Image URL")
    if st.button("Add Book"):
        books = load_json(BOOKS_FILE)
        books.append({"id": generate_id(books), "title": title, "author": author,
                      "description": description, "index": index,
                      "cover": cover, "available": True})
        save_json(BOOKS_FILE, books)
        st.success("Book added.")

# Issue book
def issue_books():
    st.subheader("Issue Books from My List")
    favorites = load_json(FAVORITES_FILE)
    books = load_json(BOOKS_FILE)
    issued = load_json(ISSUED_FILE)
    email = st.session_state.user['email']
    my_list = [f for f in favorites if f['email'] == email]
    for fav in my_list:
        book = next((b for b in books if b['id'] == fav['book_id']), None)
        if book and book['available']:
            if st.button(f"Issue {book['title']}"):
                book['available'] = False
                deadline = (datetime.date.today() + datetime.timedelta(days=7)).isoformat()
                issued.append({"email": email, "book_id": book['id'],
                               "issued_on": str(datetime.date.today()), "return_by": deadline})
                save_json(BOOKS_FILE, books)
                save_json(ISSUED_FILE, issued)
                favorites.remove(fav)
                save_json(FAVORITES_FILE, favorites)
                st.success(f"Book issued until {deadline}.")

# Return book
def return_books():
    st.subheader("Return Issued Books")
    issued = load_json(ISSUED_FILE)
    books = load_json(BOOKS_FILE)
    email = st.session_state.user['email']
    my_issues = [i for i in issued if i['email'] == email]
    for item in my_issues:
        book = next((b for b in books if b['id'] == item['book_id']), None)
        if book:
            if st.button(f"Return {book['title']}"):
                book['available'] = True
                issued.remove(item)
                save_json(BOOKS_FILE, books)
                save_json(ISSUED_FILE, issued)
                st.success("Book returned successfully.")

# View issued books
def view_issued():
    st.subheader("My Issued Books")
    issued = load_json(ISSUED_FILE)
    books = load_json(BOOKS_FILE)
    email = st.session_state.user['email']
    for item in issued:
        if item['email'] == email:
            book = next((b for b in books if b['id'] == item['book_id']), None)
            if book:
                days_left = (datetime.date.fromisoformat(item['return_by']) - datetime.date.today()).days
                st.write(f"**{book['title']}** | Due: {item['return_by']} (in {days_left} days)")

# Delete book (librarian only)
def delete_book():
    if st.session_state.user['role'] != 'Librarian':
        st.warning("Only librarians can delete books.")
        return
    st.subheader("Delete Books")
    books = load_json(BOOKS_FILE)
    for book in books:
        if st.button(f"Delete {book['title']}"):
            books.remove(book)
            save_json(BOOKS_FILE, books)
            st.success("Book deleted.")
            st.experimental_rerun()

# Book recommendations
def recommend_books():
    st.subheader("Book Recommendations")
    issued = load_json(ISSUED_FILE)
    books = load_json(BOOKS_FILE)
    email = st.session_state.user['email']
    last_issued = next((i for i in reversed(issued) if i['email'] == email), None)
    if not last_issued:
        st.info("Issue books to get recommendations.")
        return
    last_book = next((b for b in books if b['id'] == last_issued['book_id']), None)
    if last_book:
        st.write(f"Because you read {last_book['title']}:")
        suggestions = [b for b in books if b['author'] == last_book['author'] and b['id'] != last_book['id']]
        for s in suggestions:
            st.write(f"- {s['title']} by {s['author']}")

# Main interface
st.title("📚 Library Management System")
if not st.session_state.user:
    tab1, tab2 = st.tabs(["Login", "Sign Up"])
    with tab1:
        login()
    with tab2:
        signup()
else:
    menu = ["View Books", "Add Book", "Issue Book", "Return Book", "My Issued Books", "Delete Book", "Recommendations"]
    choice = st.sidebar.selectbox("Menu", menu)

    if choice == "View Books":
        view_books()
    elif choice == "Add Book":
        add_book()
    elif choice == "Issue Book":
        issue_books()
    elif choice == "Return Book":
        return_books()
    elif choice == "My Issued Books":
        view_issued()
    elif choice == "Delete Book":
        delete_book()
    elif choice == "Recommendations":
        recommend_books()
