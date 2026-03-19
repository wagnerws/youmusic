import spotipy
from spotipy.oauth2 import SpotifyOAuth, SpotifyClientCredentials
import os
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.getenv("SPOTIPY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET")
REDIRECT_URI = os.getenv("SPOTIPY_REDIRECT_URI", "http://127.0.0.1:8000/api/spotify/callback")

class SpotifyManager:
    def __init__(self):
        self.scope = "playlist-read-private user-library-read"
        self._sp_oauth = None

    @property
    def sp_oauth(self):
        if not CLIENT_ID or not CLIENT_SECRET:
            return None # Retorna None em vez de estourar erro interno
        if self._sp_oauth is None:
            self.sp_oauth = SpotifyOAuth(
                client_id=CLIENT_ID,
                client_secret=CLIENT_SECRET,
                redirect_uri=REDIRECT_URI,
                scope=self.scope
            )
        return self._sp_oauth

    @sp_oauth.setter
    def sp_oauth(self, value):
        self._sp_oauth = value

    def get_auth_url(self):
        return self.sp_oauth.get_authorize_url()

    def get_token(self, code):
        return self.sp_oauth.get_access_token(code)

    def get_client_credentials_sp(self):
        auth_manager = SpotifyClientCredentials(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET
        )
        return spotipy.Spotify(auth_manager=auth_manager)



    def get_user_playlists(self, token):
        sp = spotipy.Spotify(auth=token)
        return sp.current_user_playlists()

    def get_playlist_tracks(self, token, playlist_id):
        sp = spotipy.Spotify(auth=token)
        results = sp.playlist_tracks(playlist_id)
        tracks = results['items']
        while results['next']:
            results = sp.next(results)
            tracks.extend(results['items'])
        
        return [
            {
                'title': f"{item['track']['artists'][0]['name']} - {item['track']['name']}",
                'id': item['track']['id'],
                'uri': item['track']['uri']
            }
            for item in tracks if item['track']
        ]
