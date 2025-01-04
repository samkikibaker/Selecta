## Selecta

Selecta is a tool designed to help DJs and music enthusiasts easily categorize their music and create playlists. This version of the tool uses a Docker container to process your music files and provides an interactive interface through a Streamlit app.

> **Note**: You don’t need any coding knowledge to use this tool! While there are a couple of prerequisites to install, these tools are free, widely trusted, and commonly used by software developers. Rest assured, future versions of Selecta aim to simplify the setup even further for a smoother experience.

## Prerequisites

To use Selecta, you will need:

1. **Git** 🛠️: To clone the repository. Download and install from [git-scm.com](https://git-scm.com/).
2. **Docker** 🐳: To run the application. Download and install from [docker.com](https://www.docker.com/).

## Step-by-Step Guide

### 1. Clone the Repository
- 🖥️ Open a terminal (Command Prompt, PowerShell, or Terminal).
- 📋 Copy and paste the following command:
   ```bash
   git clone https://github.com/samkikibaker/Selecta.git
   ```
- 📂 Navigate into the repository folder:
   ```bash
   cd Selecta
   ```

### 2. Add Your Music

- 🎵 Locate the Selecta folder on your computer.
- 📁 Copy your music files (.mp3 only) into the `songs` directory within the repository folder. Note songs can be within subfolders.

### 3. Ensure Docker is Running

- 🐳 Open Docker Desktop and ensure it is running.
- ⚙️ Adjust the Docker settings to allocate more CPU and RAM 
  - Select the gear icon and go to the resources tab
  - Adjust the CPU limit, Memory limit and Swap (set to maximum for  fastest performance).
- 🔄 Restart Docker to apply the changes.

### 4. Run the Application

- 🖥️ In the terminal, make sure you are in the Selecta folder.
- 🖥️ Run the following command to start the application:
   ```bash
   bash run.sh
   ```
- 🐳 Docker will run the necessary processing to understand which songs within your library are most similar.

> **Note**: The first time this runs it may take some time depending on the number of songs as well as the compute power allocated (i.e. the number of CPUs and amount of memory set in Docker). For reference, during testing, 1688 songs, 8 CPUs, 14GB RAM took ~12mins. 

### 5. Access the Streamlit App

- 🌐 Once the processing is finished, your terminal will prompt you to go to the following URL in your web browser (e.g. Chrome):

   ```
   http://localhost:8501
   ```
- 🎛️ You can now use the Streamlit app to explore and categorize your music library!

## Troubleshooting

- **Docker not running:** 🐳 Ensure Docker Desktop is running before executing `bash run.sh`.
- **Browser not opening:** 🌐 If the app doesn’t open automatically, manually enter `http://localhost:8501` into your browser's address bar.

If you encounter any issues, please create a GitHub issue or contact the repository maintainer.

## Feedback

We’d love to hear your feedback! 📝 Your suggestions will help us improve Selecta and work towards building a more intuitive web application for DJs.

Thank you for testing Selecta! 🎧

