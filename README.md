# Selecta - Intelligent Playlist Generation

**Selecta** is a music analysis and playlist generation tool designed for DJs with large local music libraries. It 
allows the user to analyse their music and build playlists of similar songs. Unlike streaming platforms, whose 
algorithms are driven primarily by user behaviour, **Selecta** creates a mathematical representation for songs based 
on their **intrinsic audio characteristics** — analysing how songs actually sound. By building similarity relationships 
directly from the music itself, Selecta helps DJs quickly discover compatible tracks, generate cohesive playlists and 
rediscover forgotten music within extensive collections. Playlists can be downloaded as `.zip` files allowing easy 
porting into DJ software such as Rekordbox, Serato or Traktor. 

---

## Setup

Clone the repository and setup the project via:

```bash
make setup
```

This will create the required virtual environment and install all necessary dependencies.

---

## Quickstart Guide

1. Launch the **Selecta** interface via:

```bash
make run
```

2. Click **Add Songs** and choose a folder where you have `.mp3` files located

3. Click **Analyse Songs** - this will start the process of analysing your music library and computing the similarities 
between your songs. Note this may take a few minutes depending on the size of your library and compute power

4. Click **Create Playlists** - this will allow you to build a playlist of the most similar songs to a chosen song
   - Name your playlist
   - Select a root song to base your playlist on
   - Choose the number of songs (as well as the root song) you would like in your playlist
   - Hit **OK**

5. Inspect your playlist in the right pannel and hit **Download** to download the songs as a `.zip`

---

# Notes
- Currently only `.mp3` files are supported

# Future Development Ideas
- UI enhancements (it looks pretty terrible right now!)
- In built music player
- Ability to create and edit playlists manually
- Support for other music file types
