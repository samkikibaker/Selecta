import streamlit as st
import httpx
import os
import asyncio
import joblib
import pandas as pd
import json
import multiprocessing

from dotenv import load_dotenv
from datetime import datetime
from azure.storage.blob import BlobServiceClient
from azure.identity import DefaultAzureCredential
from azure.core.exceptions import ResourceNotFoundError
from stqdm import stqdm
from streamlit import session_state
from concurrent.futures import ThreadPoolExecutor, as_completed

from selecta.mongo_db import insert_documents
from selecta.logger import generate_logger

logger = generate_logger()
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


async def create_playlist(email, playlist_name, songs):
    async with httpx.AsyncClient() as client:
        json_data = {"email": email, "playlist_name": playlist_name, "songs": songs}
        response = await client.post(f"{API_URL}/create_playlist", json=json_data)
        return response


async def get_playlists(email):
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{API_URL}/get_playlists", json={"email": email})
        return response


def download_similarity_matrix() -> pd.DataFrame:
    # Create blob client
    blob_service_client = BlobServiceClient(
        account_url="https://saselecta.blob.core.windows.net", credential=DefaultAzureCredential()
    )
    container_client = blob_service_client.get_container_client("containerselecta")
    blob_client = container_client.get_blob_client(f"users/{session_state['email']}/cache/similarity_matrix.joblib")

    # Download file
    local_path = "similarity_matrix.joblib"
    try:
        with open(local_path, "wb") as file:
            file.write(blob_client.download_blob().readall())

        # Load and convert to pandas df
        similarity_matrix = joblib.load(local_path)
        similarity_matrix_df = pd.DataFrame(similarity_matrix)

        # Delete local file
        os.remove(local_path)

    except ResourceNotFoundError:
        similarity_matrix_df = pd.DataFrame()

    return similarity_matrix_df


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
        # Initialize BlobServiceClient with default credentials
        blob_service_client = BlobServiceClient(
            account_url="https://saselecta.blob.core.windows.net", credential=DefaultAzureCredential()
        )
        container_client = blob_service_client.get_container_client(container="containerselecta")

        # List existing songs in blob storage
        existing_blobs = set()
        prefix = f"users/{session_state['email']}/songs/"
        for blob in container_client.list_blobs(name_starts_with=prefix):
            existing_blobs.add(blob.name)

        new_files = [f for f in uploaded_files if f"{prefix}{f.name}" not in existing_blobs]

        # Upload only files that don't already exist
        for new_file in stqdm(new_files, desc="Uploading Songs..."):
            song_name = new_file.name
            blob_path = f"{prefix}{song_name}"

            # Upload the file if it doesn't already exist
            if blob_path not in existing_blobs:
                container_client.upload_blob(
                    name=blob_path, data=new_file, overwrite=False, max_concurrency=8
                )


def upload_music_as_zip():
    uploaded_file = st.file_uploader("Choose MP3 files", type=".zip", accept_multiple_files=False)

    if uploaded_file:
        # Initialize BlobServiceClient with default credentials
        blob_service_client = BlobServiceClient(
            account_url="https://saselecta.blob.core.windows.net", credential=DefaultAzureCredential()
        )
        container_client = blob_service_client.get_container_client(container="containerselecta")

        current_time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        blob_path = f"users/{session_state['email']}/songs/{current_time_str}"

        container_client.upload_blob(
            name=blob_path, data=uploaded_file, overwrite=False, max_concurrency=8
        )


def analyse_music():
    if st.button("Analyse Music"):
        response = asyncio.run(queue_analysis_job(st.session_state.email))

        if response.status_code == 200:
            st.success("Your music is being analysed. This may take a few minutes.")

        else:
            st.error("Error analysing music")


@st.dialog("New Playlist")
def new_playlist_pop_up(similarity_matrix_df: pd.DataFrame) -> None:
    song_names = similarity_matrix_df.columns

    with st.form(key="new_playlist_form"):
        new_playlist_name = st.text_input(
            label="Name",
            value="New Playlist",
            key="new_playlist_name",
        )

        new_playlist_root = st.selectbox("Select a song to base the playlist on", song_names, key="new_playlist_root")

        new_playlist_size = st.number_input(
            "Number of songs in playlist",
            min_value=1,
            max_value=len(song_names) - 1,
            value=1,
            key="new_playlist_size",
        )

        if st.form_submit_button("Submit"):
            similarity_row = similarity_matrix_df.loc[new_playlist_root]
            similarity_row = similarity_row.drop(new_playlist_root)
            most_similar_songs = similarity_row.nsmallest(new_playlist_size).index.tolist()

            # Save to session_state so we can use it later
            st.session_state["most_similar_songs"] = most_similar_songs

            st.markdown("### Songs:")
            song_list = "\n".join([f"- {song}" for song in most_similar_songs])
            st.markdown(song_list)

        if st.form_submit_button("Save Playlist"):
            if "most_similar_songs" not in st.session_state:
                st.error("Please generate the playlist first by clicking 'Submit'")
                return

            response = asyncio.run(
                create_playlist(
                    email=session_state["email"],
                    playlist_name=new_playlist_name,
                    songs=st.session_state["most_similar_songs"],
                )
            )

            if response.status_code == 200:
                st.success("Playlist saved successfully!")
            else:
                st.error(f"Failed to save playlist: {response.text}")


def manage_playlists():
    similarity_matrix_df = download_similarity_matrix()

    # Add a new playlist
    if st.button("New Playlist", key="new_playlist"):
        new_playlist_pop_up(similarity_matrix_df)

    st.subheader("My Playlists")

    response = asyncio.run(get_playlists(email=session_state["email"]))

    if response.status_code == 200:
        playlists = json.loads(response.text)["playlists"]
        for playlist in playlists:
            with st.expander(f"{playlist['playlist_name']}"):
                for song in playlist["songs"]:
                    st.markdown(f"- {song}")

    else:
        st.error(f"Error fetching playlists: {response.text}")
