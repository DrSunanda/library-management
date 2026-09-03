import streamlit as st
from database import get_connection


def add_book():
    st.subheader("Add Book")

    title = st.text_input("Book Title")
    author = st.text_input("Author Name")
    quantity = st.number_input("Quantity", min_value=1, step=1)

    if st.button("Add Book"):
        if not title.strip():
            st.error("Book title cannot be empty.")
            return

        if not author.strip():
            st.error("Author name cannot be empty.")
            return

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO books (title, author, quantity, available)
            VALUES (?, ?, ?, ?)
            """,
            (title.strip(), author.strip(), quantity, quantity)
        )

        connection.commit()
        connection.close()

        st.success("Book added successfully!")


def view_books():
    st.subheader("All Books")

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT id, title, author, quantity, available
        FROM books
        ORDER BY id
        """
    )

    books = cursor.fetchall()
    connection.close()

    if not books:
        st.info("No books found.")
        return

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


def search_book():
    st.subheader("Search Book")

    keyword = st.text_input("Enter title or author")

    if st.button("Search"):
        if not keyword.strip():
            st.warning("Please enter a title or author.")
            return

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT id, title, author, quantity, available
            FROM books
            WHERE title LIKE ? OR author LIKE ?
            ORDER BY id
            """,
            (
                "%" + keyword.strip() + "%",
                "%" + keyword.strip() + "%"
            )
        )

        books = cursor.fetchall()
        connection.close()

        if not books:
            st.info("No books found.")
            return

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
