# Library Management System Using Streamlit (Final Complete Version)

import streamlit as st
import pandas as pd
import os
import json
import hashlib
import random
import datetime

# ------------------ File paths ------------------
BOOKS_FILE = "books.json"
USERS_FILE = "users.json"
FAVORITES_FILE = "favorites.json"

# ------------------ Helper functions ------------------
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def load_json(file, default):
    if os.path.exists(file):
        try:
            return json.load(open(file, "r", encoding="utf-8"))
        except json.JSONDecodeError:
            return default
    return default

def save_json(file, data):
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

# ------------------ Authentication ------------------
def signup(username, password, role, email, phone):
    users = load_json(USERS_FILE, [])
    if any(u["username"] == username for u in users):
        return False
    users.append({"username": username, "password": hash_password(password), "role": role, "email": email, "phone": phone})
    save_json(USERS_FILE, users)
    return True

def check_credentials(username, password):
    users = load_json(USERS_FILE, [])
    for u in users:
        if u["username"] == username and u["password"] == hash_password(password):
            return u
    return None

def update_password(username, new_password):
    users = load_json(USERS_FILE, [])
    for u in users:
        if u["username"] == username:
            u["password"] = hash_password(new_password)
            save_json(USERS_FILE, users)
            return True
    return False

def generate_otp():
    return str(random.randint(100000, 999999))

def send_otp_simulated(contact, otp):
    st.info(f"(Simulation) OTP sent to {contact}: **{otp}**")

# ------------------ App Config ------------------
st.set_page_config(page_title="Library Management System", page_icon="📚", layout="wide")

if "auth_stage" not in st.session_state:
    st.session_state.auth_stage = "login"
if "pending_user" not in st.session_state:
    st.session_state.pending_user = None
if "otp" not in st.session_state:
    st.session_state.otp = None
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "role" not in st.session_state:
    st.session_state.role = ""

st.title("📚 Library Management System")

# ------------------ Sign Up ------------------
with st.expander("📝 Sign Up (New User)"):
    su_user = st.text_input("Username", key="su_user")
    su_pass = st.text_input("Password", type="password", key="su_pass")
    su_email = st.text_input("Email", key="su_email")
    su_phone = st.text_input("Phone Number", key="su_phone")
    su_role = st.selectbox("Role", ["student", "admin"], key="su_role")
    if st.button("Create Account"):
        if signup(su_user, su_pass, su_role, su_email, su_phone):
            st.success("✅ Account created. You can now log in.")
        else:
            st.error("⚠️ Username already exists.")

# ------------------ Forgot Password ------------------
with st.expander("🔑 Forgot Password?"):
    if st.session_state.auth_stage == "forgot":
        otp_input = st.text_input("Enter OTP")
        if st.button("Verify OTP"):
            if otp_input == st.session_state.otp:
                st.session_state.auth_stage = "reset"
                st.success("✅ OTP verified! Set a new password.")
            else:
                st.error("Invalid OTP.")
    elif st.session_state.auth_stage == "reset":
        new_pass = st.text_input("New Password", type="password")
        if st.button("Reset Password"):
            if update_password(st.session_state.pending_user, new_pass):
                st.success("✅ Password reset! You can now log in.")
                st.session_state.auth_stage = "login"
                st.session_state.pending_user = None
            else:
                st.error("Error resetting password.")
    else:
        forgot_user = st.text_input("Username", key="fp_user")
        if st.button("Send OTP"):
            user = next((u for u in load_json(USERS_FILE, []) if u["username"] == forgot_user), None)
            if user:
                otp = generate_otp()
                st.session_state.otp = otp
                st.session_state.pending_user = forgot_user
                send_otp_simulated(user["email"] or user["phone"], otp)
                st.session_state.auth_stage = "forgot"
            else:
                st.error("Username not found.")

# ------------------ Login ------------------
if st.session_state.auth_stage == "login":
    login_user = st.text_input("Username")
    login_pass = st.text_input("Password", type="password")
    if st.button("Login"):
        user = check_credentials(login_user, login_pass)
        if user:
            otp = generate_otp()
            st.session_state.otp = otp
            st.session_state.pending_user = login_user
            send_otp_simulated(user["email"] or user["phone"], otp)
            st.session_state.auth_stage = "otp"
        else:
            st.error("Invalid credentials.")

# ------------------ OTP Verification ------------------
if st.session_state.auth_stage == "otp":
    otp_input = st.text_input("Enter OTP sent to your email/phone")
    if st.button("Verify and Login"):
        if otp_input == st.session_state.otp:
            st.success(f"✅ Logged in as {st.session_state.pending_user}")
            st.session_state.logged_in = True
            st.session_state.username = st.session_state.pending_user
            u = next((x for x in load_json(USERS_FILE, []) if x["username"] == st.session_state.username), None)
            st.session_state.role = u["role"]
            st.session_state.auth_stage = "loggedin"
        else:
            st.error("Incorrect OTP.")

# ------------------ Main App ------------------
if st.session_state.get("logged_in", False):
    st.subheader(f"Welcome, {st.session_state.username} ({st.session_state.role})")
    books = load_json(BOOKS_FILE, [])
    favorites = load_json(FAVORITES_FILE, [])

    menu = ["📚 View Books", "📦 Issue Book", "🔁 Return Book", "📋 My Issued Books", "✨ Recommendations", "🚪 Logout"]
    if st.session_state.role == "admin":
        menu.insert(1, "➕ Add Book")
        menu.insert(2, "❌ Delete Book")

    choice = st.sidebar.radio("Menu", menu)

    if choice == "📚 View Books":
        st.header("All Books")
        search = st.text_input("Search Book Title")
        filtered = [b for b in books if search.lower() in b['title'].lower()] if search else books
        for book in filtered:
            st.markdown(f"**{book['title']}** by *{book['author']}* — {book.get('category', '')}")
            st.markdown(f"Status: {'✅ Available' if book.get('status','available')=='available' else '❌ Issued'}")
            if st.session_state.role == "student":
                if st.button(f"➕ Add to Favorites: {book['title']}"):
                    if not any(f["username"] == st.session_state.username and f["bid"] == book["bid"] for f in favorites):
                        favorites.append({"username": st.session_state.username, "bid": book["bid"]})
                        save_json(FAVORITES_FILE, favorites)
                        st.success("Added to your list")

    elif choice == "➕ Add Book" and st.session_state.role == "admin":
        st.header("Add New Book")
        bid = st.number_input("Book ID", step=1, min_value=1)
        title = st.text_input("Title")
        author = st.text_input("Author")
        category = st.text_input("Category")
        if st.button("Add Book"):
            if bid and title and author:
                books.append({"bid": bid, "title": title, "author": author, "category": category, "status": "available"})
                save_json(BOOKS_FILE, books)
                st.success("Book added successfully")

    elif choice == "❌ Delete Book" and st.session_state.role == "admin":
        st.header("Delete Book")
        book_ids = [b["bid"] for b in books]
        selected = st.selectbox("Select Book ID", book_ids)
        if st.button("Delete"):
            books = [b for b in books if b["bid"] != selected]
            save_json(BOOKS_FILE, books)
            st.success("Book deleted")

    elif choice == "📦 Issue Book":
        st.header("Issue Book")
        available = [b for b in books if b["status"] == "available"]
        options = {f"{b['bid']} - {b['title']}": b for b in available}
        selected = st.selectbox("Select Book", list(options.keys()))
        student = st.session_state.username if st.session_state.role == "student" else st.text_input("Student Username")
        if st.button("Issue"):
            book = options[selected]
            book["status"] = "issued"
            book["issued_to"] = student
            today = datetime.date.today()
            book["issue_date"] = str(today)
            book["due_date"] = str(today + datetime.timedelta(days=30))
            save_json(BOOKS_FILE, books)
            st.success(f"Book issued to {student}")

    elif choice == "🔁 Return Book":
        st.header("Return Book")
        issued = [b for b in books if b.get("status") == "issued" and (st.session_state.role == "admin" or b.get("issued_to") == st.session_state.username)]
        if issued:
            bid = st.selectbox("Select Book ID", [b["bid"] for b in issued])
            if st.button("Return"):
                for b in books:
                    if b["bid"] == bid:
                        today = datetime.date.today()
                        due = datetime.date.fromisoformat(b["due_date"])
                        fine = max(0, (today - due).days * 5)
                        b["status"] = "available"
                        b.pop("issued_to", None)
                        b.pop("issue_date", None)
                        b.pop("due_date", None)
                        save_json(BOOKS_FILE, books)
                        if fine > 0:
                            st.warning(f"Late return. Fine: ₹{fine}")
                        else:
                            st.success("Returned on time")
        else:
            st.info("No issued books")

    elif choice == "📋 My Issued Books":
        st.header("Issued Books")
        user_issued = [b for b in books if b.get("issued_to") == st.session_state.username]
        st.dataframe(user_issued)

    elif choice == "✨ Recommendations":
        st.header("Recommendations")
        history = [b for b in books if b.get("issued_to") == st.session_state.username]
        if history:
            last_category = history[-1].get("category")
            recs = [b for b in books if b.get("category") == last_category and b.get("status") == "available"]
            st.write("Books from your last borrowed category:")
            for b in recs:
                st.markdown(f"- **{b['title']}** by {b['author']}")
        else:
            st.info("No borrow history yet.")

    elif choice == "🚪 Logout":
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
