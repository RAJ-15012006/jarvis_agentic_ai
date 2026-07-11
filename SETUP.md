# JARVIS Setup Guide for Advanced Features

This guide explains how to get API credentials for Gmail, Google Calendar, and Spotify voice control.

---

## 📧 1. Google APIs (Gmail & Google Calendar)

Both agents reuse a single client credential to access Google APIs.

### Setup Steps:
1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Create a new project called **JARVIS-OS**.
3. Go to **APIs & Services > Library** and enable:
   - **Gmail API**
   - **Google Calendar API**
4. Go to **APIs & Services > OAuth consent screen**:
   - Set User Type to **External**.
   - Fill in the required developer email fields.
   - Under **Scopes**, add `.../auth/gmail.modify` and `.../auth/calendar`.
   - Add your own Google Account email as a **Test User** (highly important while the app is in testing).
5. Go to **APIs & Services > Credentials**:
   - Click **+ Create Credentials** > **OAuth client ID**.
   - Select **Desktop App** as the Application Type.
   - Name it `JARVIS Desktop Client`.
   - Click **Create** and download the client secrets JSON.
6. Rename this file to `gmail_credentials.json` and save it here:
   `backend/agents/face_data/gmail_credentials.json`
7. When you run a command like *"read my emails"* or *"what's on my calendar"* for the first time, a browser window will pop up asking you to authorize the application. Once authorized, JARVIS will create token files automatically and will not ask again.

---

## 🎵 2. Spotify Developer API

To enable full music search and control:

### Setup Steps:
1. Go to the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard).
2. Log in with your Spotify account and click **Create app**.
3. Enter the following details:
   - **App name**: `JARVIS OS`
   - **App description**: `Voice command dashboard`
   - **Redirect URIs**: `http://localhost:8888/callback` (MUST match this exactly!)
   - Check the boxes for **Web API** and **developer agreement**.
4. Once created, click on **Settings** to find your:
   - **Client ID**
   - **Client Secret**
5. Copy these values into your `backend/.env` file:
   ```env
   SPOTIFY_CLIENT_ID=your_client_id_here
   SPOTIFY_CLIENT_SECRET=your_client_secret_here
   SPOTIFY_REDIRECT_URI=http://localhost:8888/callback
   ```
6. Make sure Spotify is open on your desktop/phone and active when triggering voice commands. The first playback request will open a web browser to authorize access.

---

## 📊 3. GitHub API (Optional)

To enable GitHub integration:
1. No authentication is required for basic public stats.
2. If you want to check private repositories or commit/push to private ones via voice:
   - Go to **GitHub Settings > Developer Settings > Personal Access Tokens > Tokens (classic)**.
   - Generate a token with the `repo` scope.
   - Save it in your `backend/.env` as:
     ```env
     GITHUB_TOKEN=your_token_here
     ```

---

## 🚀 Running JARVIS

1. Make sure all python packages are installed:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```
2. Run the main server:
   ```bash
   python main.py
   ```
3. Start coding! Feel free to say *"how do I look"* or *"what is on my screen"* to test the vision/emotion engines immediately.
