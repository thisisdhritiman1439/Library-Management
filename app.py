# Library Management System Using Streamlit (Full Features, Improved UI)

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

st.set_page_config(page_title="Library Management System", layout="wide")

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
    with st.form(key="signup_form"):
        st.markdown("### 👤 Create Your Account")
        name = st.text_input("Full Name", key="signup_name")
        email = st.text_input("Email", key="signup_email")
        mobile = st.text_input("Mobile Number", key="signup_mobile")
        password = st.text_input("Password", type="password", key="signup_password")
        role = st.selectbox("Select Role", ["Student", "Librarian", "Other"], key="signup_role")
        submit = st.form_submit_button("Sign Up")
        if submit:
            users = load_json(USERS_FILE)
            if any(u['email'] == email for u in users):
                st.error("🚫 User already exists.")
            else:
                users.append({"name": name, "email": email, "mobile": mobile, "password": password, "role": role})
                save_json(USERS_FILE, users)
                st.success("✅ Account created. Please login.")

# Login function
def login():
    with st.form(key="login_form"):
        st.markdown("### 🔐 Login to Your Account")
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_password")
        submit = st.form_submit_button("Login")
        if submit:
            users = load_json(USERS_FILE)
            user = next((u for u in users if u['email'] == email and u['password'] == password), None)
            if user:
                st.session_state.user = user
                st.success(f"👋 Welcome {user['name']} ({user['role']})")
            else:
                st.error("❌ Invalid login details.")

# View books with search and layout
def view_books():
    st.markdown("## 📚 Browse All Books")
    books = load_json(BOOKS_FILE)
    search_term = st.text_input("🔎 Search Book by Title", key="search_book")
    if search_term:
        books = [book for book in books if search_term.lower() in book['title'].lower()]
        if not books:
            st.warning("No books found matching your search.")

    if not books:
        st.info("No books available in the library.")
        return

    for book in books:
        cols = st.columns([1, 3])
        with cols[0]:
            st.image(book['cover'], width=120)
        with cols[1]:
            st.markdown(f"### {book['title']} by {book['author']}")
            st.markdown(f"**Description:** {book['description']}")
            st.markdown(f"**Index:** {book['index']}")
            st.markdown(f"**Status:** {'🟢 Available' if book['available'] else '🔴 Issued'}")
            if st.session_state.user and st.session_state.user['role'] != 'Librarian':
                if st.button(f"➕ Add to My List - {book['id']}", key=f"fav_{book['id']}"):
                    favorites = load_json(FAVORITES_FILE)
                    if not any(f['email'] == st.session_state.user['email'] and f['book_id'] == book['id'] for f in favorites):
                        favorites.append({"email": st.session_state.user['email'], "book_id": book['id']})
                        save_json(FAVORITES_FILE, favorites)
                        st.success("Book added to your list.")
                    else:
                        st.warning("Already in your list.")

# Add book

def add_book():
    if st.session_state.user['role'] != 'Librarian':
        st.warning("Only librarians can add books.")
        return
    st.subheader("➕ Add New Book")
    title = st.text_input("Book Title")
    author = st.text_input("Author")
    description = st.text_area("Description")
    index = st.text_area("Index Page Content")
    cover = st.text_input("Cover Image URL")
    if st.button("Add Book"):
        books = load_json(BOOKS_FILE)
        books.append({"id": generate_id(books), "title": title, "author": author, "description": description,
                      "index": index, "cover": cover, "available": True})
        save_json(BOOKS_FILE, books)
        st.success("Book added successfully.")

# Issue book
def issue_books():
    st.subheader("📦 Issue Books")
    favorites = load_json(FAVORITES_FILE)
    books = load_json(BOOKS_FILE)
    issued = load_json(ISSUED_FILE)
    email = st.session_state.user['email']
    user_favs = [f for f in favorites if f['email'] == email]
    for fav in user_favs:
        book = next((b for b in books if b['id'] == fav['book_id']), None)
        if book and book['available']:
            if st.button(f"📥 Issue {book['title']}", key=f"issue_{book['id']}"):
                book['available'] = False
                deadline = (datetime.date.today() + datetime.timedelta(days=7)).isoformat()
                issued.append({"email": email, "book_id": book['id'], "issued_on": str(datetime.date.today()), "return_by": deadline})
                save_json(BOOKS_FILE, books)
                save_json(ISSUED_FILE, issued)
                favorites.remove(fav)
                save_json(FAVORITES_FILE, favorites)
                st.success(f"Book issued. Return by {deadline}.")

# Return book
def return_books():
    st.subheader("🔁 Return Book")
    issued = load_json(ISSUED_FILE)
    books = load_json(BOOKS_FILE)
    email = st.session_state.user['email']
    my_books = [i for i in issued if i['email'] == email]
    for item in my_books:
        book = next((b for b in books if b['id'] == item['book_id']), None)
        if book:
            if st.button(f"🔄 Return {book['title']}", key=f"return_{book['id']}"):
                book['available'] = True
                issued.remove(item)
                save_json(ISSUED_FILE, issued)
                save_json(BOOKS_FILE, books)
                st.success("Book returned successfully.")

# View issued books
def view_issued():
    st.subheader("📋 My Issued Books")
    issued = load_json(ISSUED_FILE)
    books = load_json(BOOKS_FILE)
    email = st.session_state.user['email']
    for item in issued:
        if item['email'] == email:
            book = next((b for b in books if b['id'] == item['book_id']), None)
            if book:
                days_left = (datetime.date.fromisoformat(item['return_by']) - datetime.date.today()).days
                st.write(f"**{book['title']}** - Return by: {item['return_by']} ({days_left} days left)")

# Delete book (Librarian only)
def delete_book():
    if st.session_state.user['role'] != 'Librarian':
        st.warning("Only librarians can delete books.")
        return
    st.subheader("🗑 Delete Book")
    books = load_json(BOOKS_FILE)
    for book in books:
        if st.button(f"❌ Delete {book['title']}", key=f"del_{book['id']}"):
            books.remove(book)
            save_json(BOOKS_FILE, books)
            st.success("Book deleted.")
            st.experimental_rerun()

# Book recommendations
def recommend_books():
    st.subheader("✨ Recommended For You")
    issued = load_json(ISSUED_FILE)
    books = load_json(BOOKS_FILE)
    email = st.session_state.user['email']
    history = [i for i in issued if i['email'] == email]
    if not history:
        st.info("Issue some books to get recommendations.")
        return
    last_book = next((b for b in books if b['id'] == history[-1]['book_id']), None)
    if last_book:
        st.write(f"Because you read **{last_book['title']}**, you might also like:")
        suggestions = [b for b in books if b['author'] == last_book['author'] and b['id'] != last_book['id']]
        for book in suggestions:
            st.write(f"- {book['title']} by {book['author']}")

# Main interface
st.title("📖 Library Management System")
if not st.session_state.user:
    tab1, tab2 = st.tabs(["🔐 Login", "🆕 Sign Up"])
    with tab1:
        login()
    with tab2:
        signup()
else:
    menu = ["📚 View Books", "➕ Add Book", "📦 Issue Book", "🔁 Return Book", "📋 My Issued Books", "🗑 Delete Book", "✨ Recommendations"]
    choice = st.sidebar.selectbox("📂 Menu", menu)

    if choice == "📚 View Books":
        view_books()
    elif choice == "➕ Add Book":
        add_book()
    elif choice == "📦 Issue Book":
        issue_books()
    elif choice == "🔁 Return Book":
        return_books()
    elif choice == "📋 My Issued Books":
        view_issued()
    elif choice == "🗑 Delete Book":
        delete_book()
    elif choice == "✨ Recommendations":
        recommend_books()
