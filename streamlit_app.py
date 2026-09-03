import streamlit as st
import sqlite3
from datetime import datetime

DATABASE_NAME = "library.db"


# ---------------- DATABASE ----------------

def get_connection():
    return sqlite3.connect(DATABASE_NAME)


def initialize_database():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            author TEXT NOT NULL,
            quantity INTEGER NOT NULL DEFAULT 1,
            available INTEGER NOT NULL DEFAULT 1
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            book_id INTEGER NOT NULL,
            member_id INTEGER NOT NULL,
            issue_date TEXT NOT NULL,
            return_date TEXT,
            status TEXT NOT NULL DEFAULT 'Issued',
            FOREIGN KEY (book_id) REFERENCES books(id),
            FOREIGN KEY (member_id) REFERENCES members(id)
        )
    """)

    connection.commit()
    connection.close()


# ---------------- BOOK FUNCTIONS ----------------

def add_book(title, author, quantity):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO books (title, author, quantity, available)
        VALUES (?, ?, ?, ?)
    """, (title, author, quantity, quantity))

    connection.commit()
    connection.close()


def get_books():
    connection = get_connection()

    books = connection.execute("""
        SELECT id, title, author, quantity, available
        FROM books
        ORDER BY id DESC
    """).fetchall()

    connection.close()

    return books


def search_books(keyword):
    connection = get_connection()

    books = connection.execute("""
        SELECT id, title, author, quantity, available
        FROM books
        WHERE title LIKE ? OR author LIKE ?
        ORDER BY id DESC
    """, (f"%{keyword}%", f"%{keyword}%")).fetchall()

    connection.close()

    return books


# ---------------- MEMBER FUNCTIONS ----------------

def add_member(name, email):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO members (name, email)
        VALUES (?, ?)
    """, (name, email))

    connection.commit()
    connection.close()


def get_members():
    connection = get_connection()

    members = connection.execute("""
        SELECT id, name, email
        FROM members
        ORDER BY id DESC
    """).fetchall()

    connection.close()

    return members


# ---------------- TRANSACTION FUNCTIONS ----------------

def issue_book(book_id, member_id):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT id, title, available
        FROM books
        WHERE id = ?
    """, (book_id,))

    book = cursor.fetchone()

    if not book:
        connection.close()
        return False, "Book not found."

    if book[2] <= 0:
        connection.close()
        return False, "This book is currently unavailable."

    cursor.execute("""
        SELECT id
        FROM members
        WHERE id = ?
    """, (member_id,))

    member = cursor.fetchone()

    if not member:
        connection.close()
        return False, "Member not found."

    cursor.execute("""
        SELECT id
        FROM transactions
        WHERE book_id = ?
        AND member_id = ?
        AND status = 'Issued'
    """, (book_id, member_id))

    existing = cursor.fetchone()

    if existing:
        connection.close()
        return False, "This member already has this book."

    issue_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
        INSERT INTO transactions
        (book_id, member_id, issue_date, status)
        VALUES (?, ?, ?, 'Issued')
    """, (book_id, member_id, issue_date))

    cursor.execute("""
        UPDATE books
        SET available = available - 1
        WHERE id = ?
    """, (book_id,))

    connection.commit()
    connection.close()

    return True, f"'{book[1]}' issued successfully."


def return_book(transaction_id):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT book_id, status
        FROM transactions
        WHERE id = ?
    """, (transaction_id,))

    transaction = cursor.fetchone()

    if not transaction:
        connection.close()
        return False, "Transaction not found."

    if transaction[1] == "Returned":
        connection.close()
        return False, "This book has already been returned."

    return_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
        UPDATE transactions
        SET return_date = ?, status = 'Returned'
        WHERE id = ?
    """, (return_date, transaction_id))

    cursor.execute("""
        UPDATE books
        SET available = available + 1
        WHERE id = ?
    """, (transaction[0],))

    connection.commit()
    connection.close()

    return True, "Book returned successfully."


def get_transactions():
    connection = get_connection()

    transactions = connection.execute("""
        SELECT
            transactions.id,
            books.title,
            members.name,
            transactions.issue_date,
            transactions.return_date,
            transactions.status
        FROM transactions
        JOIN books ON transactions.book_id = books.id
        JOIN members ON transactions.member_id = members.id
        ORDER BY transactions.id DESC
    """).fetchall()

    connection.close()

    return transactions


# ---------------- STREAMLIT APP ----------------

initialize_database()

st.set_page_config(
    page_title="Library Management System",
    page_icon="📚",
    layout="wide"
)

st.title("📚 Library Management System")
st.write("Manage books, members, and book transactions.")

# Sidebar
st.sidebar.title("Navigation")

menu = st.sidebar.radio(
    "Select an option",
    [
        "Dashboard",
        "Add Book",
        "View Books",
        "Search Book",
        "Add Member",
        "View Members",
        "Issue Book",
        "Return Book",
        "Transactions"
    ]
)


# ---------------- DASHBOARD ----------------

if menu == "Dashboard":

    st.header("📊 Dashboard")

    books = get_books()
    members = get_members()
    transactions = get_transactions()

    total_books = sum(book[3] for book in books)
    available_books = sum(book[4] for book in books)
    issued_books = total_books - available_books
    total_members = len(members)

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("📚 Total Books", total_books)
    col2.metric("✅ Available Books", available_books)
    col3.metric("📕 Issued Books", issued_books)
    col4.metric("👥 Members", total_members)

    st.divider()

    st.subheader("Recent Transactions")

    if transactions:
        for transaction in transactions[:5]:
            st.write(
                f"**{transaction[1]}** → "
                f"{transaction[2]} | "
                f"{transaction[5]}"
            )
    else:
        st.info("No transactions yet.")


# ---------------- ADD BOOK ----------------

elif menu == "Add Book":

    st.header("➕ Add Book")

    title = st.text_input("Book Title")
    author = st.text_input("Author")
    quantity = st.number_input(
        "Quantity",
        min_value=1,
        value=1,
        step=1
    )

    if st.button("Add Book", type="primary"):

        if not title or not author:
            st.error("Please enter both title and author.")

        else:
            add_book(title, author, quantity)
            st.success("Book added successfully!")


# ---------------- VIEW BOOKS ----------------

elif menu == "View Books":

    st.header("📚 All Books")

    books = get_books()

    if books:

        data = []

        for book in books:
            data.append({
                "ID": book[0],
                "Title": book[1],
                "Author": book[2],
                "Quantity": book[3],
                "Available": book[4]
            })

        st.dataframe(
            data,
            use_container_width=True,
            hide_index=True
        )

    else:
        st.info("No books available.")


# ---------------- SEARCH BOOK ----------------

elif menu == "Search Book":

    st.header("🔍 Search Book")

    keyword = st.text_input(
        "Search by title or author"
    )

    if keyword:

        books = search_books(keyword)

        if books:

            data = []

            for book in books:
                data.append({
                    "ID": book[0],
                    "Title": book[1],
                    "Author": book[2],
                    "Quantity": book[3],
                    "Available": book[4]
                })

            st.dataframe(
                data,
                use_container_width=True,
                hide_index=True
            )

        else:
            st.warning("No books found.")


# ---------------- ADD MEMBER ----------------

elif menu == "Add Member":

    st.header("👤 Add Member")

    name = st.text_input("Member Name")
    email = st.text_input("Email")

    if st.button("Add Member", type="primary"):

        if not name or not email:
            st.error("Please enter name and email.")

        else:
            add_member(name, email)
            st.success("Member added successfully!")


# ---------------- VIEW MEMBERS ----------------

elif menu == "View Members":

    st.header("👥 All Members")

    members = get_members()

    if members:

        data = []

        for member in members:
            data.append({
                "ID": member[0],
                "Name": member[1],
                "Email": member[2]
            })

        st.dataframe(
            data,
            use_container_width=True,
            hide_index=True
        )

    else:
        st.info("No members found.")


# ---------------- ISSUE BOOK ----------------

elif menu == "Issue Book":

    st.header("📕 Issue Book")

    books = get_books()
    members = get_members()

    available_books = [
        book for book in books if book[4] > 0
    ]

    if not available_books:
        st.warning("No books are currently available.")

    elif not members:
        st.warning("Please add a member first.")

    else:

        book_options = {
            f"{book[1]} — {book[2]} (Available: {book[4]})": book[0]
            for book in available_books
        }

        member_options = {
            f"{member[1]} — {member[2]}": member[0]
            for member in members
        }

        selected_book = st.selectbox(
            "Select Book",
            list(book_options.keys())
        )

        selected_member = st.selectbox(
            "Select Member",
            list(member_options.keys())
        )

        if st.button("Issue Book", type="primary"):

            book_id = book_options[selected_book]
            member_id = member_options[selected_member]

            success, message = issue_book(
                book_id,
                member_id
            )

            if success:
                st.success(message)
            else:
                st.error(message)


# ---------------- RETURN BOOK ----------------

elif menu == "Return Book":

    st.header("↩️ Return Book")

    transactions = get_transactions()

    issued_transactions = [
        transaction
        for transaction in transactions
        if transaction[5] == "Issued"
    ]

    if not issued_transactions:

        st.info("There are no issued books to return.")

    else:

        transaction_options = {
            f"#{transaction[0]} — {transaction[1]} — {transaction[2]}":
            transaction[0]
            for transaction in issued_transactions
        }

        selected_transaction = st.selectbox(
            "Select Transaction",
            list(transaction_options.keys())
        )

        if st.button("Return Book", type="primary"):

            transaction_id = transaction_options[
                selected_transaction
            ]

            success, message = return_book(
                transaction_id
            )

            if success:
                st.success(message)
            else:
                st.error(message)


# ---------------- TRANSACTIONS ----------------

elif menu == "Transactions":

    st.header("📋 All Transactions")

    transactions = get_transactions()

    if transactions:

        data = []

        for transaction in transactions:

            data.append({
                "ID": transaction[0],
                "Book": transaction[1],
                "Member": transaction[2],
                "Issue Date": transaction[3],
                "Return Date": transaction[4] or "Not Returned",
                "Status": transaction[5]
            })

        st.dataframe(
            data,
            use_container_width=True,
            hide_index=True
        )

    else:
        st.info("No transactions found."