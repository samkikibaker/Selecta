import streamlit as st

from components import register, login, upload_music, analyse_music, manage_playlists, logout


# Main logic to control user flow
def main():
    st.title("Selecta")

    if "logged_in" not in st.session_state or not st.session_state.logged_in:
        # Using tabs to separate Login and Register
        login_tab, register_tab = st.tabs(["Login", "Register"])

        with login_tab:
            login()

        with register_tab:
            register()

    else:
        logout()

        upload_music_tab, analyse_music_tab, manage_playlists_tab = st.tabs(
            ["Upload Music", "Analyse Music", "Manage Playlists"]
        )

        with upload_music_tab:
            upload_music()

        with analyse_music_tab:
            analyse_music()

        with manage_playlists_tab:
            manage_playlists()


# Run the app
if __name__ == "__main__":
    main()
