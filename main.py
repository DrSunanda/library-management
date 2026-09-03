import streamlit as st

from database import initialize_database
from books import add_book, view_books, search_book
from members import add_member, view_members
from transactions import issue_book, return_book, view_transactions


st.set_page_config(
    page_title="Library Management System",
    page_icon="📚",
    layout="wide"
)

initialize_database()

st.title("📚 Library Management System")
st.write("Welcome to the Library Management System!")

choice = st.sidebar.selectbox(
    "Menu",
    [
        "Add Book",
        "View Books",
        "Search Book",
        "Add Member",
        "View Members",
        "Issue Book",
        "Return Book",
        "View Transactions"
    ]
)

if choice == "Add Book":
    add_book()

elif choice == "View Books":
    view_books()

elif choice == "Search Book":
    search_book()

elif choice == "Add Member":
    add_member()

elif choice == "View Members":
    view_members()

elif choice == "Issue Book":
    issue_book()

elif choice == "Return Book":
    return_book()

elif choice == "View Transactions":
    view_transactions()