import zipfile
import streamlit as st
import os

from selecta.SongCategoriser import SongCategoriser

# Streamlit app title
app_title = st.title("Selecta - Find Similar Songs")

# Path to music
music_path_input = st.text_input(
    label="Enter music path", key="music_path_input", help="Enter the location path of your music"
)

# Analyse Music Button
analyse_music_button = st.button(label="Analyse Music", key="analyse_music_button", disabled=music_path_input == "")
if analyse_music_button:
    with st.spinner("Analysing Music..."):
        song_categoriser = SongCategoriser(dir_path=music_path_input)

    st.session_state["songs_analysed"] = True
    st.session_state["song_categoriser"] = song_categoriser

if st.session_state.get("songs_analysed"):
    song_categoriser = st.session_state.get("song_categoriser")
    song_names = sorted(list(song_categoriser.similarity_matrix.index))

    # Initialize session state for dynamic playlists and generated flag
    if "playlists" not in st.session_state:
        st.session_state["playlists"] = [
            {
                "song": "",
                "num_songs": 10,
                "playlist_name": "Playlist 1",
                "songs": [],
            }
        ]

    # Add a new playlist
    if st.button("Add Playlist", key="add_playlist"):
        new_playlist = {
            "song": "",
            "num_songs": 10,
            "playlist_name": f"Playlist {len(st.session_state['playlists']) + 1}",
            "songs": [],
        }
        st.session_state["playlists"].append(new_playlist)

    # Dynamic playlist input management
    for idx, playlist in enumerate(st.session_state["playlists"]):
        # Set the expander title dynamically
        playlist_title = f"Playlist {idx + 1}" if not playlist["playlist_name"] else playlist["playlist_name"]

        with st.expander(playlist_title, expanded=True):
            # Text input for playlist name
            st.session_state["playlists"][idx]["playlist_name"] = st.text_input(
                label="Name",
                value=st.session_state["playlists"][idx]["playlist_name"],
                key=f"playlist_name_{idx}",
            )

            # Dropdown for song selection
            st.session_state["playlists"][idx]["song"] = st.selectbox(
                "Select a song to base the playlist on", song_names, key=f"song_{idx}"
            )

            # Number input for similar songs
            st.session_state["playlists"][idx]["num_songs"] = st.number_input(
                "Number of songs in playlist",
                min_value=1,
                max_value=len(song_names) - 1,
                value=st.session_state["playlists"][idx]["num_songs"],
                key=f"num_songs_{idx}",
            )

            # Conditional display of generated songs
            if playlist["songs"]:
                st.markdown("### Songs:")
                song_list = "\n".join([f"- {song}" for song in playlist["songs"]])
                st.markdown(song_list)

            # Remove playlist button
            if st.button("Remove Playlist", key=f"remove_playlist_{idx}"):
                del st.session_state["playlists"][idx]
                st.session_state["playlists_generated"] = False  # Reset playlists generated flag
                st.rerun()  # Force rerun to update the UI after removal

    # Process all playlists
    if st.button(
        "Generate Playlists",
        key="generate_playlists",
        disabled=len(st.session_state["playlists"]) == 0,
    ):
        # Enable download playlists button
        st.session_state["playlists_generated"] = True

        for playlist in st.session_state["playlists"]:
            song = playlist["song"]
            num_songs = playlist["num_songs"]
            playlist_name = playlist["playlist_name"]

            try:
                # Get the similarity row corresponding to the selected song
                similarity_row = song_categoriser.similarity_matrix.loc[song]
                similarity_row = similarity_row.drop(song)  # Exclude the selected song itself
                most_similar_songs = similarity_row.nsmallest(num_songs).index.tolist()
                playlist["songs"] = most_similar_songs

            except Exception as e:
                st.error(f"Error processing playlist '{playlist_name}': {e}")

        # Force a rerun after generating playlists
        st.rerun()

    # Create a single zip file containing all playlists
    if st.session_state.get("playlists_generated"):
        zip_filename = "playlists.zip"
        with zipfile.ZipFile(zip_filename, "w") as zipf:
            for playlist in st.session_state["playlists"]:
                playlist_name = playlist["playlist_name"]
                songs = playlist["songs"]

                for similar_song in songs:
                    source_file = next(
                        (song_obj.path for song_obj in song_categoriser.song_objects if song_obj.name == similar_song),
                        None,
                    )
                    if source_file and os.path.exists(source_file):
                        # Add the song to the playlist's folder within the zip file
                        zipf.write(
                            source_file,
                            os.path.join(playlist_name, os.path.basename(similar_song)),
                        )

        # Provide the zip file for download
        with open(zip_filename, "rb") as zip_file:
            st.download_button(
                label="Download All Playlists",
                data=zip_file,
                file_name=zip_filename,
                mime="application/zip",
            )

        # Clean up the generated zip file after download
        os.remove(zip_filename)
