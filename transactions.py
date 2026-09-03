from datetime import datetime
import streamlit as st
from database import get_connection


def issue_book():
    st.subheader("Issue Book")

    connection = None

    try:
        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("""
            SELECT id, title, author, available
            FROM books
            WHERE available > 0
            ORDER BY title
        """)

        books = cursor.fetchall()

        cursor.execute("""
            SELECT id, name, email
            FROM members
            ORDER BY name
        """)

        members = cursor.fetchall()

        if not books:
            st.warning("No books are currently available.")
            return

        if not members:
            st.warning("No members found. Please add a member first.")
            return

        book_options = {
            f"{book[1]} - {book[2]} (Available: {book[3]})": book[0]
            for book in books
        }

        member_options = {
            f"{member[1]} - {member[2]}": member[0]
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

            cursor.execute("""
                SELECT id, title, available
                FROM books
                WHERE id = ?
            """, (book_id,))

            book = cursor.fetchone()

            if not book:
                st.error("Book not found.")
                return

            if book[2] <= 0:
                st.error("This book is currently unavailable.")
                return

            cursor.execute("""
                SELECT id, name
                FROM members
                WHERE id = ?
            """, (member_id,))

            member = cursor.fetchone()

            if not member:
                st.error("Member not found.")
                return

            cursor.execute("""
                SELECT id
                FROM transactions
                WHERE book_id = ?
                AND member_id = ?
                AND status = 'Issued'
            """, (book_id, member_id))

            existing_transaction = cursor.fetchone()

            if existing_transaction:
                st.warning(
                    "This member has already issued this book."
                )
                return

            issue_date = datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )

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

            st.success(
                f"Book '{book[1]}' issued to {member[1]} successfully!"
            )

    except Exception as e:
        if connection:
            connection.rollback()

        st.error(f"Error issuing book: {e}")

    finally:
        if connection:
            connection.close()


def return_book():
    st.subheader("Return Book")

    connection = None

    try:
        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                transactions.id,
                books.title,
                members.name,
                transactions.issue_date
            FROM transactions
            JOIN books
                ON transactions.book_id = books.id
            JOIN members
                ON transactions.member_id = members.id
            WHERE transactions.status = 'Issued'
            ORDER BY transactions.id DESC
        """)

        transactions = cursor.fetchall()

        if not transactions:
            st.info("No currently issued books to return.")
            return

        transaction_options = {
            f"Transaction #{transaction[0]} - "
            f"{transaction[1]} - "
            f"{transaction[2]} - "
            f"Issued: {transaction[3]}": transaction[0]
            for transaction in transactions
        }

        selected_transaction = st.selectbox(
            "Select Transaction",
            list(transaction_options.keys())
        )

        if st.button("Return Book", type="primary"):
            transaction_id = transaction_options[selected_transaction]

            cursor.execute("""
                SELECT book_id, member_id, status
                FROM transactions
                WHERE id = ?
            """, (transaction_id,))

            transaction = cursor.fetchone()

            if not transaction:
                st.error("Transaction not found.")
                return

            if transaction[2] == "Returned":
                st.warning("This book has already been returned.")
                return

            return_date = datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )

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

            st.success("Book returned successfully!")

    except Exception as e:
        if connection:
            connection.rollback()

        st.error(f"Error returning book: {e}")

    finally:
        if connection:
            connection.close()


def view_transactions():
    st.subheader("Transactions")

    connection = None

    try:
        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                transactions.id,
                books.title,
                members.name,
                transactions.issue_date,
                transactions.return_date,
                transactions.status
            FROM transactions
            JOIN books
                ON transactions.book_id = books.id
            JOIN members
                ON transactions.member_id = members.id
            ORDER BY transactions.id DESC
        """)

        transactions = cursor.fetchall()

        if not transactions:
            st.info("No transactions found.")
            return

        data = []

        for transaction in transactions:
            data.append({
                "Transaction ID": transaction[0],
                "Book": transaction[1],
                "Member": transaction[2],
                "Issue Date": transaction[3],
                "Return Date": transaction[4] or "Not returned",
                "Status": transaction[5]
            })

        st.dataframe(
            data,
            use_container_width=True,
            hide_index=True
        )

    except Exception as e:
        st.error(f"Error loading transactions: {e}")

    finally:
        if connection:
            connection.close()
