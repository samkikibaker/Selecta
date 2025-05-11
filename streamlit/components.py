import streamlit as st
import httpx
import os
import asyncio

from dotenv import load_dotenv
from azure.storage.blob import BlobServiceClient
from azure.identity import DefaultAzureCredential
from stqdm import stqdm

from streamlit import session_state

load_dotenv()

# Set the backend FastAPI URL
API_URL = os.getenv("API_URL")


# Async function for making HTTP requests
async def register_user(email, password):
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{API_URL}/register", json={"email": email, "password": password})
        return response


async def login_user(email, password):
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{API_URL}/login", json={"email": email, "password": password})
        return response


async def queue_analysis_job(email):
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{API_URL}/queue_analysis_job", json={"email": email})
        return response


def register():
    email = st.text_input("Email", placeholder="Enter your email", key="register_email_input")
    password = st.text_input(
        "Password", type="password", placeholder="Choose a password", key="register_password_input"
    )
    confirm_password = st.text_input(
        "Confirm Password", type="password", placeholder="Confirm your password", key="register_confirm_password_input"
    )

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
                st.session_state.email = email
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
    uploaded_files = st.file_uploader("Choose MP3 files", type=".mp3", accept_multiple_files=True)

    if uploaded_files:
        if len(uploaded_files) > 1000:
            st.error("Maximum 1000 songs can be uploaded.")
        else:
            # Initialize BlobServiceClient with default credentials
            blob_service_client = BlobServiceClient(
                account_url="https://saselecta.blob.core.windows.net", credential=DefaultAzureCredential()
            )
            container_client = blob_service_client.get_container_client(container="containerselecta")

            # List existing blobs in the path users/{session_state['email']}/songs/
            existing_blobs = set()
            prefix = f"users/{session_state['email']}/songs/"
            for blob in container_client.list_blobs(name_starts_with=prefix):
                existing_blobs.add(blob.name)

            # Upload only files that don't already exist
            for uploaded_file in stqdm(uploaded_files, desc="Uploading Songs..."):
                song_name = uploaded_file.name
                blob_path = f"{prefix}{song_name}"

                if blob_path not in existing_blobs:
                    # Upload the file if it doesn't already exist
                    container_client.upload_blob(name=blob_path, data=uploaded_file, overwrite=False)


def analyse_music():
    if st.button("Analyse Music"):
        response = asyncio.run(queue_analysis_job(st.session_state.email))

        if response.status_code == 200:
            st.success("Your music is being analysed. This may take a few minutes.")


def manage_playlists():
    pass
