"""
spotify_agent.py — JARVIS Spotify Voice Control
================================================
Control Spotify playback, search songs, manage playlists by voice.
Uses the Spotify Web API via the spotipy library.

SETUP REQUIRED (one-time):
  1. Go to https://developer.spotify.com/dashboard
  2. Create an app → Get Client ID and Client Secret
  3. Set Redirect URI to: http://localhost:8888/callback
  4. Add to .env:
       SPOTIFY_CLIENT_ID=your_client_id
       SPOTIFY_CLIENT_SECRET=your_client_secret
       SPOTIFY_REDIRECT_URI=http://localhost:8888/callback
  5. First run will open browser for auth

Voice commands:
  - "play [song name]" / "play [artist] on Spotify"
  - "pause Spotify" / "stop music"
  - "next song" / "skip song"
  - "previous song"
  - "volume up / down / set to 80"
  - "what song is playing" / "current song"
  - "play my [playlist name] playlist"
  - "shuffle on / off"
  - "repeat on / off"
"""

import os
import re

SPOTIFY_TRIGGERS = [
    "spotify", "play music", "pause music", "stop music", "next song", "skip song",
    "previous song", "skip to next", "volume up", "volume down", "what song",
    "current song", "what's playing", "whats playing", "now playing",
    "play on spotify", "shuffle", "repeat", "playlist", "play my playlist",
    "play artist", "play album",
]

def is_spotify_command(command: str) -> bool:
    cmd = command.lower()
    return any(t in cmd for t in SPOTIFY_TRIGGERS)


def _get_spotify_client():
    """Initialize and return authenticated Spotipy client."""
    try:
        import spotipy
        from spotipy.oauth2 import SpotifyOAuth

        client_id = os.getenv("SPOTIFY_CLIENT_ID", "")
        client_secret = os.getenv("SPOTIFY_CLIENT_SECRET", "")
        redirect_uri = os.getenv("SPOTIFY_REDIRECT_URI", "http://localhost:8888/callback")

        if not client_id or not client_secret:
            return None, (
                "Sir, Spotify credentials not configured. "
                "Add SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET to your .env file."
            )

        cache_path = os.path.join(
            os.path.dirname(__file__), "face_data", ".spotify_cache"
        )

        sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            scope="user-read-playback-state user-modify-playback-state user-read-currently-playing playlist-read-private",
            cache_path=cache_path,
            open_browser=True,
        ))
        return sp, None

    except ImportError:
        return None, "Sir, spotipy is not installed. Run: pip install spotipy"
    except Exception as e:
        return None, f"Spotify auth failed: {str(e)}"


def _get_active_device_id(sp) -> str:
    """Get the ID of the currently active Spotify device."""
    try:
        devices = sp.devices()
        device_list = devices.get("devices", [])
        if not device_list:
            return None
        active = next((d for d in device_list if d["is_active"]), None)
        return (active or device_list[0])["id"]
    except Exception:
        return None


def play_song(query: str) -> str:
    """Search and play a song on Spotify."""
    sp, error = _get_spotify_client()
    if error:
        return error
    try:
        results = sp.search(q=query, type="track", limit=1)
        tracks = results["tracks"]["items"]
        if not tracks:
            return f"Raj, I couldn't find '{query}' on Spotify."

        track = tracks[0]
        track_uri = track["uri"]
        track_name = track["name"]
        artist_name = track["artists"][0]["name"]

        device_id = _get_active_device_id(sp)
        sp.start_playback(device_id=device_id, uris=[track_uri])

        return f"🎵 Now playing: '{track_name}' by {artist_name}, Sir."
    except Exception as e:
        return f"Raj, Spotify playback failed: {str(e)}"


def play_playlist(playlist_name: str) -> str:
    """Search user's playlists and play by name."""
    sp, error = _get_spotify_client()
    if error:
        return error
    try:
        playlists = sp.current_user_playlists(limit=50)
        items = playlists.get("items", [])

        match = next(
            (p for p in items if playlist_name.lower() in p["name"].lower()),
            None
        )
        if not match:
            return f"Raj, I couldn't find a playlist matching '{playlist_name}'."

        device_id = _get_active_device_id(sp)
        sp.start_playback(device_id=device_id, context_uri=match["uri"])
        return f"🎵 Playing playlist: '{match['name']}', Sir."
    except Exception as e:
        return f"Spotify playlist error: {str(e)}"


def get_now_playing() -> str:
    """Return what's currently playing."""
    sp, error = _get_spotify_client()
    if error:
        return error
    try:
        current = sp.current_playback()
        if not current or not current.get("item"):
            return "Nothing is currently playing on Spotify, Sir."

        item = current["item"]
        name = item["name"]
        artist = item["artists"][0]["name"]
        album = item["album"]["name"]
        progress_ms = current.get("progress_ms", 0)
        duration_ms = item.get("duration_ms", 1)
        progress_pct = int((progress_ms / duration_ms) * 100)
        is_playing = "▶ Playing" if current.get("is_playing") else "⏸ Paused"

        return (
            f"🎵 {is_playing}: '{name}' by {artist}\n"
            f"   Album: {album} | Progress: {progress_pct}%"
        )
    except Exception as e:
        return f"Couldn't get playback info: {str(e)}"


def pause_playback() -> str:
    sp, error = _get_spotify_client()
    if error:
        return error
    try:
        sp.pause_playback()
        return "⏸ Music paused, Sir."
    except Exception as e:
        return f"Pause failed: {str(e)}"


def resume_playback() -> str:
    sp, error = _get_spotify_client()
    if error:
        return error
    try:
        sp.start_playback()
        return "▶ Music resumed, Sir."
    except Exception as e:
        return f"Resume failed: {str(e)}"


def next_track() -> str:
    sp, error = _get_spotify_client()
    if error:
        return error
    try:
        sp.next_track()
        return "⏭ Skipped to next track, Sir."
    except Exception as e:
        return f"Skip failed: {str(e)}"


def previous_track() -> str:
    sp, error = _get_spotify_client()
    if error:
        return error
    try:
        sp.previous_track()
        return "⏮ Going back to previous track, Sir."
    except Exception as e:
        return f"Previous failed: {str(e)}"


def set_volume(percent: int) -> str:
    sp, error = _get_spotify_client()
    if error:
        return error
    try:
        percent = max(0, min(100, percent))
        device_id = _get_active_device_id(sp)
        sp.volume(percent, device_id=device_id)
        return f"🔊 Volume set to {percent}%, Sir."
    except Exception as e:
        return f"Volume failed: {str(e)}"


def toggle_shuffle(state: bool) -> str:
    sp, error = _get_spotify_client()
    if error:
        return error
    try:
        sp.shuffle(state)
        return f"🔀 Shuffle {'enabled' if state else 'disabled'}, Sir."
    except Exception as e:
        return f"Shuffle failed: {str(e)}"


def handle_spotify_command(command: str) -> str:
    """Main Spotify command dispatcher."""
    cmd = command.lower().strip()

    if any(w in cmd for w in ["pause", "stop music", "stop spotify"]):
        return pause_playback()

    if any(w in cmd for w in ["resume", "continue", "unpause"]):
        return resume_playback()

    if any(w in cmd for w in ["next", "skip", "next song", "next track"]):
        return next_track()

    if any(w in cmd for w in ["previous", "back", "last song", "prev"]):
        return previous_track()

    if any(w in cmd for w in ["what song", "what's playing", "now playing", "current song"]):
        return get_now_playing()

    if "shuffle on" in cmd:
        return toggle_shuffle(True)
    if "shuffle off" in cmd:
        return toggle_shuffle(False)

    # Volume parsing
    vol_match = re.search(r"volume\s*(up|down|to|at)?\s*(\d+)?", cmd)
    if vol_match:
        direction = vol_match.group(1)
        amount = int(vol_match.group(2)) if vol_match.group(2) else 10
        if direction == "up":
            return set_volume(70)  # simple: set to 70 (real impl would get current + delta)
        elif direction == "down":
            return set_volume(30)
        elif direction in ("to", "at") and amount:
            return set_volume(amount)

    # Playlist check
    if "playlist" in cmd:
        for keyword in ["play", "playlist"]:
            if keyword in cmd:
                name = cmd.split(keyword)[-1].replace("playlist", "").strip()
                if name:
                    return play_playlist(name)

    # Song search — extract query
    query = cmd
    for noise in ["play", "on spotify", "spotify", "song", "music", "listen to",
                  "put on", "queue", "add to queue"]:
        query = query.replace(noise, "").strip()

    if query:
        return play_song(query)

    return "Raj, what would you like to play on Spotify?"
