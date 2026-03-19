const API_BASE = window.location.origin + "/api";

document.getElementById('search-btn').addEventListener('click', async () => {
    const url = document.getElementById('url-input').value;
    if (!url) return;

    showLoading(true);
    try {
        const response = await fetch(`${API_BASE}/info`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url })
        });
        const data = await response.json();
        
        if (data.error) throw new Error(data.error);
        
        displayResults(data);
    } catch (err) {
        alert("Erro ao buscar informações: " + err.message);
    } finally {
        showLoading(false);
    }
});

function displayResults(data) {
    const resultsDiv = document.getElementById('results');
    const trackList = document.getElementById('track-list');
    const title = document.getElementById('result-title');
    
    resultsDiv.style.display = 'block';
    trackList.innerHTML = '';
    title.innerText = data.title || "Resultado";

    if (data.type === 'playlist') {
        data.entries.forEach(track => {
            const item = document.createElement('div');
            item.className = 'track-item';
            item.innerHTML = `
                <input type="checkbox" checked data-url="${track.url}">
                <span>${track.title}</span>
            `;
            trackList.appendChild(item);
        });
    } else {
        const item = document.createElement('div');
        item.className = 'track-item';
        item.innerHTML = `
            <input type="checkbox" checked data-url="${data.url}">
            <span>${data.title}</span>
        `;
        trackList.appendChild(item);
    }
}

document.getElementById('download-all-btn').addEventListener('click', async () => {
    const checkboxes = document.querySelectorAll('#track-list input[type="checkbox"]:checked');
    if (checkboxes.length === 0) return;

    for (const cb of checkboxes) {
        const url = cb.getAttribute('data-url');
        const title = cb.nextElementSibling.innerText;
        await downloadTrack(url, title, cb.parentElement);
    }
});

async function downloadTrack(url, title, element) {
    element.classList.add('processing');
    element.classList.remove('done', 'fail');
    try {
        const isSpotify = !url.includes('youtube.com') && !url.includes('youtu.be');
        const endpoint = isSpotify ? `${API_BASE}/download/search` : `${API_BASE}/download`;
        const body = isSpotify ? { query: title } : { url: url };

        const response = await fetch(endpoint, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body)
        });
        
        if (!response.ok) throw new Error("Falha no download");
        
        const blob = await response.blob();
        const downloadUrl = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = downloadUrl;
        a.download = `${title}.mp3`;
        document.body.appendChild(a);
        a.click();
        a.remove();
        element.classList.remove('processing');
        element.classList.add('done');
    } catch (err) {
        console.error(err);
        element.classList.remove('processing');
        element.classList.add('fail');
    }
}

// Lógica para detectar token do Spotify na URL após o callback
window.addEventListener('load', () => {
    const params = new URLSearchParams(window.location.search);
    const token = params.get('access_token');
    if (token) {
        sessionStorage.setItem('spotify_token', token);
        loadSpotifyPlaylists(token);
    }
});

async function loadSpotifyPlaylists(token) {
    const response = await fetch(`${API_BASE}/spotify/playlists?token=${token}`);
    const data = await response.json();
    displayPlaylists(data);
}

function displayPlaylists(data) {
    const resultsDiv = document.getElementById('results');
    const trackList = document.getElementById('track-list');
    const title = document.getElementById('result-title');
    
    resultsDiv.style.display = 'block';
    trackList.innerHTML = '';
    title.innerText = "Suas Playlists do Spotify";

    data.items.forEach(pl => {
        const item = document.createElement('div');
        item.className = 'track-item';
        item.style.cursor = 'pointer';
        item.innerHTML = `<span>📁 ${pl.name}</span>`;
        item.onclick = () => loadPlaylistTracks(pl.id);
        trackList.appendChild(item);
    });
}

// async function loadPlaylistTracks(playlistId) {
//     const token = sessionStorage.getItem('spotify_token');
//     showLoading(true);
//     const response = await fetch(`${API_BASE}/spotify/playlist-tracks?token=${token}&playlist_id=${playlistId}`);
//     const tracks = await response.json();
//     displayResults({ type: 'playlist', title: 'Músicas da Playlist', entries: tracks });
//     showLoading(false);
// }

document.getElementById('select-all-checkbox').addEventListener('change', (e) => {
    const isChecked = e.target.checked;
    const checkboxes = document.querySelectorAll('#track-list input[type="checkbox"]');
    checkboxes.forEach(cb => cb.checked = isChecked);
});

function showLoading(isLoading) {

    const btn = document.getElementById('search-btn');
    if (btn) {
        btn.disabled = isLoading;
        btn.innerText = isLoading ? "Processando..." : "Analisar";
    }
}

// document.getElementById('spotify-btn').addEventListener('click', async () => {
//     const response = await fetch(`${API_BASE}/spotify/login`);
//     const data = await response.json();
//     window.location.href = data.url;
// });
