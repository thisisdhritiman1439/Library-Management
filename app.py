# 📚 Library Management System with Streamlit

import streamlit as st
import json
import os
from datetime import datetime, timedelta

# ===================== JSON FILE PATHS =====================
BOOKS_FILE = 'books.json'
USERS_FILE = 'users.json'
ISSUED_FILE = 'issued_books.json'

# ===================== LOAD & SAVE =====================
def load_json(file):
    try:
        with open(file, 'r') as f:
            return json.load(f)
    except (json.decoder.JSONDecodeError, FileNotFoundError):
        return []

def save_json(file, data):
    with open(file, 'w') as f:
        json.dump(data, f, indent=4)

# ===================== INITIAL DATA =====================
def load_data():
    return load_json(BOOKS_FILE), load_json(USERS_FILE), load_json(ISSUED_FILE)

def save_data(books, users, issued):
    save_json(BOOKS_FILE, books)
    save_json(USERS_FILE, users)
    save_json(ISSUED_FILE, issued)

# ===================== USER AUTH =====================
def signup(users):
    st.subheader("Create a New Account")
    name = st.text_input("Full Name")
    mobile = st.text_input("Mobile Number")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    role = st.selectbox("Select Role", ["Student", "Librarian", "Other"])
    if st.button("Sign Up"):
        if any(u['email'] == email for u in users):
            st.error("Email already exists.")
        else:
            users.append({"name": name, "mobile": mobile, "email": email, "password": password, "role": role, "book_list": []})
            save_json(USERS_FILE, users)
            st.success("Account created! Please login.")


# ===================== LOGIN =====================
def login(users):
    st.subheader("Login")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        for u in users:
            if u['email'] == email and u['password'] == password:
                st.session_state['user'] = u
                st.success(f"Welcome {u['name']} ({u['role']})")
                return True
        st.error("Invalid credentials")
    return False

# ===================== BOOK VIEW =====================
def view_books(books, current_user):
    st.subheader("📚 All Books")
    for book in books:
        with st.expander(f"{book['title']} by {book['author']}"):
            st.image(book['cover'], width=150)
            st.write(f"**Description**: {book['description']}")
            st.write(f"**Availability**: {'Available' if book['status'] == 'available' else 'Issued'}")
            st.write(f"**Index**: {book.get('index', 'N/A')}")
            if current_user:
                if book['status'] == 'available':
                    if st.button(f"Add to My Booklist - {book['id']}"):
                        if book['id'] not in current_user['book_list']:
                            current_user['book_list'].append(book['id'])
                            save_json(USERS_FILE, users)
                            st.success("Book added to your list!")

# ===================== ADD NEW BOOK =====================
def add_book(books):
    st.subheader("➕ Add New Book")
    title = st.text_input("Book Title")
    author = st.text_input("Author")
    description = st.text_area("Book Description")
    index = st.text_area("Index Page Content")
    cover = st.text_input("Cover Image URL")
    if st.button("Add Book"):
        bid = max([b['id'] for b in books], default=0) + 1
        books.append({"id": bid, "title": title, "author": author, "description": description, "cover": cover, "index": index, "status": "available"})
        save_json(BOOKS_FILE, books)
        st.success("Book added successfully!")

# ===================== DELETE BOOK =====================
def delete_book(books):
    st.subheader("🗑 Delete Book")
    book_titles = [f"{b['id']}: {b['title']}" for b in books]
    selected = st.selectbox("Select a Book to Delete", book_titles)
    if st.button("Delete"):
        bid = int(selected.split(':')[0])
        books = [b for b in books if b['id'] != bid]
        save_json(BOOKS_FILE, books)
        st.success("Book deleted.")

# ===================== ISSUE BOOK =====================
def issue_book(current_user, books, issued):
    st.subheader("📦 Issue a Book from Your List")
    available_books = [b for b in books if b['id'] in current_user['book_list'] and b['status'] == 'available']
    if not available_books:
        st.info("No available books in your book list.")
        return
    book_titles = [f"{b['id']}: {b['title']}" for b in available_books]
    selected = st.selectbox("Select Book to Issue", book_titles)
    if st.button("Issue Book"):
        bid = int(selected.split(':')[0])
        for b in books:
            if b['id'] == bid:
                b['status'] = 'issued'
        due_date = (datetime.now() + timedelta(days=14)).strftime('%Y-%m-%d')
        issued.append({"email": current_user['email'], "book_id": bid, "issue_date": datetime.now().strftime('%Y-%m-%d'), "due_date": due_date})
        current_user['book_list'].remove(bid)
        save_data(books, users, issued)
        st.success(f"Book issued! Return by {due_date}.")

# ===================== RETURN BOOK =====================
def return_book(current_user, books, issued):
    st.subheader("📥 Return a Book")
    my_issued = [i for i in issued if i['email'] == current_user['email']]
    if not my_issued:
        st.info("You have no issued books.")
        return
    book_titles = [f"{i['book_id']}: {[b['title'] for b in books if b['id']==i['book_id']][0]}" for i in my_issued]
    selected = st.selectbox("Select Book to Return", book_titles)
    if st.button("Return Book"):
        bid = int(selected.split(':')[0])
        issued[:] = [i for i in issued if not (i['email'] == current_user['email'] and i['book_id'] == bid)]
        for b in books:
            if b['id'] == bid:
                b['status'] = 'available'
        save_data(books, users, issued)
        st.success("Book returned.")

# ===================== VIEW ISSUED BOOKS =====================
def view_issued_books(current_user, books, issued):
    st.subheader("📋 Your Issued Books")
    my_issued = [i for i in issued if i['email'] == current_user['email']]
    for entry in my_issued:
        book = next((b for b in books if b['id'] == entry['book_id']), None)
        if book:
            st.markdown(f"**{book['title']}** - Due on `{entry['due_date']}`")

# ===================== BOOK RECOMMENDATION =====================
def recommend_books(current_user, books, issued):
    st.subheader("🤖 Recommended Books")
    last_issued = [i for i in issued if i['email'] == current_user['email']]
    if not last_issued:
        st.info("No past history found.")
        return
    last_book_id = last_issued[-1]['book_id']
    last_book = next((b for b in books if b['id'] == last_book_id), None)
    if last_book:
        recs = [b for b in books if last_book['author'] == b['author'] and b['id'] != last_book_id and b['status'] == 'available']
        for r in recs:
            st.markdown(f"**{r['title']}** by {r['author']}")

# ===================== MAIN APP =====================
def main():
    st.title("📚 Library Management System")
    global books, users, issued
    books, users, issued = load_data()

    if 'user' not in st.session_state:
        menu = st.sidebar.radio("Menu", ["Login", "Sign Up"])
        if menu == "Sign Up":
            signup(users)
        else:
            login(users)
    else:
        user = st.session_state['user']
        menu = st.sidebar.radio("Navigate", ["View Books", "My Book List", "Issue Book", "Return Book", "Issued Books", "Recommendations"] + (["Add Book", "Delete Book"] if user['role'] == "Librarian" else []))

        if menu == "View Books":
            view_books(books, user)
        elif menu == "Add Book":
            add_book(books)
        elif menu == "Delete Book":
            delete_book(books)
        elif menu == "My Book List":
            st.json(user['book_list'])
        elif menu == "Issue Book":
            issue_book(user, books, issued)
        elif menu == "Return Book":
            return_book(user, books, issued)
        elif menu == "Issued Books":
            view_issued_books(user, books, issued)
        elif menu == "Recommendations":
            recommend_books(user, books, issued)

main()
