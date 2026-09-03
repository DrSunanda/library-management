import streamlit as st
from database import get_connection


def add_member():
    st.subheader("Add Member")

    name = st.text_input(
        "Member Name",
        placeholder="Enter member name"
    )

    email = st.text_input(
        "Member Email",
        placeholder="Enter email address"
    )

    if st.button("Add Member", type="primary"):
        if not name.strip():
            st.error("Member name cannot be empty.")
            return

        if not email.strip():
            st.error("Member email cannot be empty.")
            return

        connection = None

        try:
            connection = get_connection()
            cursor = connection.cursor()

            cursor.execute(
                """
                INSERT INTO members (name, email)
                VALUES (?, ?)
                """,
                (
                    name.strip(),
                    email.strip()
                )
            )

            connection.commit()
            connection.close()

            st.success("Member added successfully!")

        except Exception as e:
            if connection:
                connection.rollback()

            st.error(f"Error adding member: {e}")

        finally:
            if connection:
                connection.close()


def view_members():
    st.subheader("All Members")

    connection = None

    try:
        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT id, name, email
            FROM members
            ORDER BY id
            """
        )

        members = cursor.fetchall()

        if not members:
            st.info("No members found.")
            return

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

    except Exception as e:
        st.error(f"Error loading members: {e}")

    finally:
        if connection:
            connection.close()
