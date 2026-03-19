import os
import sys

# Adicionar o diretório atual ao path para garantir importações no Vercel
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from downloader import Downloader
from spotify_manager import SpotifyManager
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse

app = FastAPI(title="YouMusic API")
sp_manager = SpotifyManager()

# Calcular caminhos relativos ao arquivo main.py
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(BASE_DIR, "..", "frontend")

# Montar arquivos estáticos (CSS, JS)
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

# Configuração de CORS para o frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

dl = Downloader()

class InfoRequest(BaseModel):
    url: str

class DownloadRequest(BaseModel):
    url: str

@app.post("/api/info")
async def get_info(req: InfoRequest):
    try:
        info = dl.get_info(req.url)
        if 'error' in info:
            raise HTTPException(status_code=400, detail=info['error'])
        return info
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno ao processar URL: {str(e)}")

@app.post("/api/download")
async def start_download(req: DownloadRequest):
    result = dl.download(req.url)
    if not result['success']:
        raise HTTPException(status_code=500, detail=result['error'])
    
    # Retorna o arquivo e deleta depois (simplificado)
    # Em produção usaríamos um sistema de cache ou link temporário
    return FileResponse(
        path=result['file_path'],
        media_type='audio/mpeg',
        filename=f"{result['title']}.mp3"
    )

@app.get("/")
async def root():
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))

# @app.get("/api/spotify/login")
# async def spotify_login():
#     try:
#         if not sp_manager.sp_oauth:
#             raise HTTPException(status_code=400, detail="Configuração do Spotify incompleta no servidor (faltam CLIENT_ID/SECRET no .env)")
#         url = sp_manager.get_auth_url()
#         return {"url": url}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))
# 
# @app.get("/api/spotify/callback")
# async def spotify_callback(code: str):
#     token_info = sp_manager.get_token(code)
#     # Aqui poderíamos redirecionar para o frontend com o token na URL ou cookie
#     return {"token_info": token_info}
# 
# @app.get("/api/spotify/playlists")
# async def get_playlists(token: str):
#     playlists = sp_manager.get_user_playlists(token)
#     return playlists
# 
# @app.get("/api/spotify/playlist-tracks")
# async def get_tracks(token: str, playlist_id: str):
#     tracks = sp_manager.get_playlist_tracks(token, playlist_id)
#     return tracks

class SearchDownloadRequest(BaseModel):
    query: str

@app.post("/api/download/search")
async def download_search(req: SearchDownloadRequest):
    result = dl.download_by_search(req.query)
    if not result['success']:
        raise HTTPException(status_code=500, detail=result['error'])
    
    return FileResponse(
        path=result['file_path'],
        media_type='audio/mpeg',
        filename=f"{result['title']}.mp3"
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
