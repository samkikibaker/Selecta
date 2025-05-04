import streamlit as st
import httpx
import os
import asyncio

# Set the backend FastAPI URL
API_URL = os.getenv("API_URL", "http://localhost:8080")

# Async function for making HTTP requests
async def register_user(email, password):
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{API_URL}/register", json={"email": email, "password": password})
        return response

async def login_user(email, password):
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{API_URL}/login", json={"email": email, "password": password})
        return response

def register():
    email = st.text_input("Email", placeholder="Enter your email", key="register_email_input")
    password = st.text_input("Password", type="password", placeholder="Choose a password", key="register_password_input")
    confirm_password = st.text_input("Confirm Password", type="password", placeholder="Confirm your password", key="register_confirm_password_input")

    if password != confirm_password:
        st.warning("Passwords do not match!")
    elif st.button("Register"):
        if email and password:
            response = asyncio.run(register_user(email, password))  # Using async request
            if response.status_code == 200:
                st.success("Registered successfully! You can now log in.")
            else:
                st.error(f"Registration failed: {response.json()['detail']}")
        else:
            st.warning("Please fill in all fields")

def login():
    email = st.text_input("Email", placeholder="Enter your email", key="login_email_input")
    password = st.text_input("Password", type="password", placeholder="Enter your password", key="login_password_input")

    if st.button("Login"):
        if email and password:
            response = asyncio.run(login_user(email, password))  # Using async request
            if response.status_code == 200:
                st.session_state.access_token = response.json()["access_token"]
                st.success("Login successful!")
                st.session_state.logged_in = True
                st.rerun()

            else:
                st.error("Invalid credentials")
        else:
            st.warning("Please fill in all fields")

def logout():
    if st.button("Logout"):
        st.session_state.clear()
        st.rerun()

def upload_music():

    st.file_uploader(label="Upload Songs", type=".mp3", accept_multiple_files=True)


def manage_playlists():
    pass
