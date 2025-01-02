import os
import shutil
import streamlit as st
import joblib
from SongCategoriser import SongCategoriser, Song

# Load the SongCategoriser instance
try:
    song_categoriser = joblib.load('cache/song_categoriser')
except FileNotFoundError:
    st.error("The 'song_categoriser' file was not found. Please ensure it is in the 'cache' directory.")
    st.stop()

# Streamlit app title
st.title("Songr - Find Similar Songs")

# Dropdown for song name selection with alphabetical sorting
song_names = sorted(list(song_categoriser.similarity_matrix.index))
selected_song = st.selectbox("Select a song", song_names)

# Input for number of most similar songs to display
num_similar_songs = st.number_input(
    "Number of most similar songs",
    min_value=1,
    max_value=len(song_names) - 1,  # Exclude the selected song itself
    value=5
)

# Button to run the method and show results
if st.button("Run"):
    try:
        # Get the similarity row corresponding to the selected song
        similarity_row = song_categoriser.similarity_matrix.loc[selected_song]

        # Exclude the selected song itself
        similarity_row = similarity_row.drop(selected_song)

        # Get the names of the most similar songs by sorting by similarity value
        most_similar_songs = similarity_row.nsmallest(num_similar_songs).index.tolist()

        # Store results in session state
        st.session_state['most_similar_songs'] = most_similar_songs
        st.session_state['selected_song'] = selected_song

    except Exception as e:
        st.error(f"An error occurred while processing: {e}")

# Display the list of similar songs if available
if 'most_similar_songs' in st.session_state:
    st.write(f"Most similar songs to '{st.session_state['selected_song']}':")
    for idx, similar_song in enumerate(st.session_state['most_similar_songs'], 1):
        st.write(f"{idx}. {similar_song}")

    # Prompt for playlist name (folder name)
    playlist_name = st.text_input("Enter playlist name", "", key="playlist_name_input")

    # Copy songs to the target folder when the button is pressed
    if st.button("Copy Songs to Folder", key="copy_button"):
        if playlist_name:
            try:
                # Create a folder with the playlist name
                target_directory = os.path.join("playlists", playlist_name)

                if not os.path.exists(target_directory):
                    os.makedirs(target_directory)

                copied_songs = []
                for song_name in st.session_state['most_similar_songs']:
                    # Map song name to file path (assuming song files are named after the song names)
                    source_file = next(iter(song.path for song in song_categoriser.song_objects if song.name == song_name), None)
                    target_file = os.path.join(target_directory, song_name)

                    # Check if the source file exists
                    if source_file and os.path.exists(source_file):
                        shutil.copy(source_file, target_file)
                        copied_songs.append(song_name)
                    else:
                        st.warning(f"File for '{song_name}' not found in the source directory.")

                if copied_songs:
                    st.success(f"Successfully copied {len(copied_songs)} songs to the '{playlist_name}' folder.")
                else:
                    st.error("No songs were copied. Please check the file paths.")
            except Exception as e:
                st.error(f"An error occurred while copying songs: {e}")
        else:
            st.error("Please enter a valid playlist name.")
