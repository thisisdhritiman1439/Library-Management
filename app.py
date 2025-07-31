import streamlit as st
import json
import os
from datetime import datetime, timedelta

# --------------------------- Utility Functions --------------------------- #

def load_data():
    try:
        with open("books.json") as f:
            books = json.load(f)
    except:
        books = []

    try:
        with open("users.json") as f:
            users = json.load(f)
    except:
        users = []

    try:
        with open("issued_books.json") as f:
            issued = json.load(f)
    except:
        issued = []

    return books, users, issued

def save_data(books, users, issued):
    with open("books.json", "w") as f:
        json.dump(books, f, indent=4)
    with open("users.json", "w") as f:
        json.dump(users, f, indent=4)
    with open("issued_books.json", "w") as f:
        json.dump(issued, f, indent=4)

# --------------------------- Main Application --------------------------- #

def login(users):
    st.subheader("🔐 Login")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        for user in users:
            if user["email"] == email and user["password"] == password:
                st.success(f"Welcome {user['name']} ({user['role']})!")
                return user
        st.error("Invalid credentials")
    return None

def signup(users):
    st.subheader("📝 Sign Up")
    name = st.text_input("Name")
    mobile = st.text_input("Mobile")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    role = st.selectbox("Role", ["Student", "Librarian", "Other"])
    if st.button("Sign Up"):
        for user in users:
            if user["email"] == email:
                st.error("User already exists")
                return None
        user = {"name": name, "mobile": mobile, "email": email, "password": password, "role": role, "booklist": []}
        users.append(user)
        st.success("Account created. Please login.")
        save_data(books, users, issued)
        return None
    return None

def view_books(books, user):
    st.subheader("📚 View All Books")
    for book in books:
        col1, col2 = st.columns([1, 3])
        with col1:
            st.image(book.get("cover", ""), width=100)
        with col2:
            st.markdown(f"### {book['title']}")
            st.write(f"**Author:** {book['author']}")
            st.write(f"**Available:** {'✅' if book['available'] else '❌'}")
            st.write(book['description'])
            with st.expander("📖 View Index"):
                st.code(book['index'])
            if user['role'] != "Librarian":
                if st.button(f"➕ Add to Booklist", key=f"add_{book['id']}"):
                    if book['id'] not in user['booklist']:
                        user['booklist'].append(book['id'])
                        st.success("Added to your booklist")

def add_book(books):
    st.subheader("➕ Add New Book (Librarian Only)")
    title = st.text_input("Title")
    author = st.text_input("Author")
    description = st.text_area("Description")
    index = st.text_area("Index")
    cover = st.text_input("Cover Image URL")
    if st.button("Add Book"):
        book_id = max([b['id'] for b in books], default=0) + 1
        books.append({"id": book_id, "title": title, "author": author, "description": description,
                      "index": index, "cover": cover, "available": True})
        st.success("Book added successfully")
        save_data(books, users, issued)

def delete_book(books):
    st.subheader("🗑 Delete Book (Librarian Only)")
    book_ids = [f"{b['id']} - {b['title']}" for b in books]
    book_select = st.selectbox("Select book to delete", book_ids)
    if st.button("Delete Book"):
        book_id = int(book_select.split(" - ")[0])
        books[:] = [b for b in books if b['id'] != book_id]
        st.success("Book deleted successfully")
        save_data(books, users, issued)

def issue_book(books, issued, user):
    st.subheader("📤 Issue Book")
    available_books = [b for b in books if b['available']]
    book_ids = [f"{b['id']} - {b['title']}" for b in available_books]
    book_select = st.selectbox("Select book to issue", book_ids)
    if st.button("Issue Book"):
        book_id = int(book_select.split(" - ")[0])
        for b in books:
            if b['id'] == book_id:
                b['available'] = False
        issued.append({"book_id": book_id, "user_email": user['email'], "issue_date": datetime.now().strftime("%Y-%m-%d"),
                       "return_by": (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d")})
        st.success("Book issued. Return within 14 days.")
        save_data(books, users, issued)

def return_book(books, issued, user):
    st.subheader("📥 Return Book")
    user_issued = [i for i in issued if i['user_email'] == user['email']]
    book_titles = [f"{i['book_id']} - {[b['title'] for b in books if b['id'] == i['book_id']][0]}" for i in user_issued]
    if not book_titles:
        st.info("No books to return.")
        return
    book_select = st.selectbox("Select book to return", book_titles)
    if st.button("Return Book"):
        book_id = int(book_select.split(" - ")[0])
        issued[:] = [i for i in issued if not (i['book_id'] == book_id and i['user_email'] == user['email'])]
        for b in books:
            if b['id'] == book_id:
                b['available'] = True
        st.success("Book returned.")
        save_data(books, users, issued)

def view_issued_books(books, issued):
    st.subheader("📖 Issued Books Overview")
    for i in issued:
        book = next((b for b in books if b['id'] == i['book_id']), None)
        if book:
            st.markdown(f"**{book['title']}** issued to `{i['user_email']}` | Return by: `{i['return_by']}`")

def recommend_books(user, books, issued):
    st.subheader("🔍 Book Recommendations")
    prev_ids = [i['book_id'] for i in issued if i['user_email'] == user['email']]
    prev_books = [b for b in books if b['id'] in prev_ids]
    if not prev_books:
        st.info("Issue some books to get recommendations.")
        return
    last_title = prev_books[-1]['title']
    st.write(f"Because you read **{last_title}**, you might also like:")
    for book in books:
        if book['id'] not in prev_ids:
            st.markdown(f"- {book['title']} by {book['author']}")

def main():
    global books, users, issued
    st.title("📚 Library Management System")

    books, users, issued = load_data()

    menu = ["Login", "Sign Up"]
    choice = st.sidebar.selectbox("Menu", menu)

    user = None
    if choice == "Login":
        user = login(users)
    elif choice == "Sign Up":
        user = signup(users)

    if user:
        tab = st.sidebar.selectbox("Features", ["View Books", "Issue Book", "Return Book",
                                                 "View Issued Books", "Book Recommendations"] +
                                                (["Add Book", "Delete Book"] if user['role'] == "Librarian" else []))

        if tab == "View Books":
            view_books(books, user)
        elif tab == "Add Book":
            add_book(books)
        elif tab == "Delete Book":
            delete_book(books)
        elif tab == "Issue Book":
            issue_book(books, issued, user)
        elif tab == "Return Book":
            return_book(books, issued, user)
        elif tab == "View Issued Books":
            view_issued_books(books, issued)
        elif tab == "Book Recommendations":
            recommend_books(user, books, issued)

if __name__ == '__main__':
    main()
