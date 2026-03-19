import os
import yt_dlp
import uuid
import subprocess
from spotify_manager import SpotifyManager

class Downloader:
    def __init__(self):
        self.download_path = os.path.join(os.path.dirname(__file__), "..", "downloads")
        if not os.path.exists(self.download_path):
            os.makedirs(self.download_path)
        self.sp_manager = SpotifyManager()
        self.ydl_opts_base = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': f'{self.download_path}/%(title)s.%(ext)s',
            'quiet': True,
            'no_warnings': True,
            'noplaylist': False,
        }

    def get_info(self, url):
        """Obtém informações do vídeo ou playlist."""
        # Verificar se é link do Spotify
        if "spotify.com" in url:
            return self._get_spotify_info(url)

        # Normalizar URL: se for um vídeo dentro de playlist, focar na playlist
        if "list=" in url and "playlist?list=" not in url:
            import urllib.parse as urlparse
            parsed = urlparse.urlparse(url)
            params = urlparse.parse_qs(parsed.query)
            if 'list' in params:
                url = f"https://www.youtube.com/playlist?list={params['list'][0]}"

        opts = {'quiet': True, 'noplaylist': False, 'extract_flat': True}
        with yt_dlp.YoutubeDL(opts) as ydl:
            try:
                info = ydl.extract_info(url, download=False)
                
                if 'entries' in info:
                    # É uma playlist
                    return {
                        'type': 'playlist',
                        'title': info.get('title'),
                        'entries': [
                            {'title': e.get('title'), 'url': e.get('url') or e.get('webpage_url'), 'duration': e.get('duration')}
                            for e in info.get('entries') if e
                        ]
                    }
                else:
                    # É um vídeo único (ou yt-dlp não expandiu a lista)
                    return {
                        'type': 'video',
                        'title': info.get('title'),
                        'url': info.get('webpage_url'),
                        'duration': info.get('duration'),
                        'thumbnail': info.get('thumbnail')
                    }
            except Exception as e:
                return {'error': str(e)}

    def _get_spotify_info(self, url):
        """Obtém info de playlist ou track do Spotify."""
        try:
            sp = self.sp_manager.get_client_credentials_sp()
            if "playlist" in url:
                playlist_id = url.split("playlist/")[1].split("?")[0]
                playlist = sp.playlist(playlist_id)
                tracks = []
                results = playlist['tracks']
                while results:
                    for item in results['items']:
                        if item['track']:
                            tracks.append({
                                'title': f"{item['track']['artists'][0]['name']} - {item['track']['name']}",
                                'url': item['track']['external_urls']['spotify'],
                                'duration': item['track']['duration_ms'] // 1000
                            })
                    if results['next']:
                        results = sp.next(results)
                    else:
                        results = None
                
                return {
                    'type': 'playlist',
                    'title': playlist['name'],
                    'entries': tracks
                }
            elif "track" in url:
                track_id = url.split("track/")[1].split("?")[0]
                track = sp.track(track_id)
                return {
                    'type': 'video',
                    'title': f"{track['artists'][0]['name']} - {track['name']}",
                    'url': track['external_urls']['spotify'],
                    'duration': track['duration_ms'] // 1000
                }
        except Exception as e:
            return {'error': f"Erro Spotify: {str(e)}"}

    def download_by_search(self, query):
        """Busca no YouTube e baixa a melhor correspondência."""
        search_query = f"ytsearch1:{query}"
        return self.download(search_query)

    def download(self, url):
        """Baixa o áudio e retorna o caminho do arquivo."""
        unique_id = str(uuid.uuid4())
        opts = self.ydl_opts_base.copy()
        opts['outtmpl'] = f'{self.download_path}/{unique_id}_%(title)s.%(ext)s'
        
        with yt_dlp.YoutubeDL(opts) as ydl:
            try:
                info = ydl.extract_info(url, download=True)
                if 'entries' in info:
                    info = info['entries'][0]
                
                filename = ydl.prepare_filename(info)
                # O yt-dlp substitui a extensão por .mp3 no postprocessor
                filename = os.path.splitext(filename)[0] + ".mp3"
                return filename
            except Exception as e:
                print(f"Erro no download: {e}")
                return None
