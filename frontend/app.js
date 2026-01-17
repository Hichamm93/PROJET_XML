const API_URL = 'http://localhost:8000/api';
let currentUser = null;
let currentPage = 'home';

// Chargement initial
document.addEventListener('DOMContentLoaded', () => {
    loadFilmsALaUne();
    loadVilles();
    currentUser = JSON.parse(localStorage.getItem('user'));
    updateAuthUI();
});

// Navigation
function showHome() {
    hideAllPages();
    document.getElementById('home-page').style.display = 'block';
    currentPage = 'home';
    loadFilmsALaUne();
}

function showVilles() {
    hideAllPages();
    document.getElementById('ville-page').style.display = 'block';
    currentPage = 'ville';
}

function showLogin() {
    hideAllPages();
    document.getElementById('login-page').style.display = 'block';
}

function showRegister() {
    hideAllPages();
    document.getElementById('register-page').style.display = 'block';
}

function hideAllPages() {
    const pages = ['home-page', 'film-detail-page', 'ville-page', 'login-page', 'register-page',
                   'client-page', 'proprio-film-page', 'add-film-page', 'proprio-cinema-page', 'add-programmation-page'];
    pages.forEach(id => document.getElementById(id).style.display = 'none');
}

function updateAuthUI() {
    if (currentUser) {
        document.getElementById('auth-buttons').style.display = 'none';
        document.getElementById('user-menu').style.display = 'flex';
        document.getElementById('user-name').textContent = currentUser.email;
        
        // Rediriger selon le rôle
        if (currentUser.role === 'client') {
            showClientPage();
        } else if (currentUser.role === 'proprio_film') {
            showProprioFilmPage();
        } else if (currentUser.role === 'proprio_cinema') {
            showProprioCinemaPage();
        }
    } else {
        document.getElementById('auth-buttons').style.display = 'block';
        document.getElementById('user-menu').style.display = 'none';
    }
}

function logout() {
    currentUser = null;
    localStorage.removeItem('user');
    updateAuthUI();
    showHome();
}

// API Calls
async function apiCall(endpoint, options = {}) {
    try {
        const response = await fetch(`${API_URL}${endpoint}`, {
            ...options,
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            }
        });
        if (!response.ok) throw new Error(await response.text());
        return await response.json();
    } catch (error) {
        alert('Erreur: ' + error.message);
        throw error;
    }
}

// Films à la une
async function loadFilmsALaUne() {
    const films = await apiCall('/films-a-la-une');
    const container = document.getElementById('films-list');
    container.innerHTML = films.map(film => `
        <div class="film-card" onclick="showFilmDetail(${film.id})">
            <h3>${film.titre}</h3>
            <p>Réalisateur: ${film.realisateur}</p>
            <p>Durée: ${film.duree} min</p>
        </div>
    `).join('');
}

// Recherche
function handleSearch(event) {
    if (event.key === 'Enter') performSearch();
}

async function performSearch() {
    const q = document.getElementById('search-input').value;
    if (!q) return;
    const films = await apiCall(`/search?q=${encodeURIComponent(q)}`);
    const container = document.getElementById('films-list');
    container.innerHTML = films.map(film => `
        <div class="film-card" onclick="showFilmDetail(${film.id})">
            <h3>${film.titre}</h3>
            <p>Réalisateur: ${film.realisateur}</p>
            <p>Durée: ${film.duree} min</p>
        </div>
    `).join('');
}

// Détail film
async function showFilmDetail(filmId) {
    hideAllPages();
    document.getElementById('film-detail-page').style.display = 'block';
    const data = await apiCall(`/film/${filmId}`);
    const container = document.getElementById('film-detail');
    
    let html = `
        <h2>${data.film.titre}</h2>
        <p><strong>Réalisateur:</strong> ${data.film.realisateur}</p>
        <p><strong>Durée:</strong> ${data.film.duree} min</p>
        <p><strong>Langue:</strong> ${data.film.langue}</p>
        <p><strong>Sous-titre:</strong> ${data.film.sous_titre}</p>
        <p><strong>Âge minimum:</strong> ${data.film.age_min} ans</p>
    `;
    
    if (data.programmations.length > 0) {
        html += '<h3 style="margin-top: 2rem; color: #dc0000;">Programmations</h3>';
        
        // Grouper par ville
        const byVille = {};
        data.programmations.forEach(p => {
            if (!byVille[p.cinema.ville]) byVille[p.cinema.ville] = [];
            byVille[p.cinema.ville].push(p);
        });
        
        Object.keys(byVille).forEach(ville => {
            html += `<div class="programmation-group"><h3>${ville}</h3>`;
            byVille[ville].forEach(p => {
                html += `
                    <div class="cinema-info">
                        <strong>${p.cinema.nom}</strong> - ${p.cinema.adresse}<br>
                        Du ${p.date_deb} au ${p.date_fin}<br>
                        <div class="creneaux-list">
                            ${p.creneaux.map(c => `<span class="creneau">${c.jour_semaine} ${c.heure_debut}</span>`).join('')}
                        </div>
                        ${currentUser && currentUser.role === 'client' ? `
                            <button onclick="createReservation(${p.id}, '${p.date_deb}', '${p.creneaux[0].heure_debut}')" style="margin-top: 0.5rem;">Réserver</button>
                        ` : ''}
                    </div>
                `;
            });
            html += '</div>';
        });
    }
    
    container.innerHTML = html;
}

// Villes
async function loadVilles() {
    const villes = await apiCall('/villes');
    const container = document.getElementById('villes-list');
    container.innerHTML = villes.map(ville => `
        <button onclick="loadProgrammationsVille('${ville}')">${ville}</button>
    `).join(' ');
}

async function loadProgrammationsVille(ville) {
    const progs = await apiCall(`/ville/${encodeURIComponent(ville)}/programmations`);
    const container = document.getElementById('programmations-ville');
    container.innerHTML = `<h3>Programmations à ${ville}</h3>` + 
        progs.map(p => `
            <div class="programmation-card">
                <h4>${p.film.titre}</h4>
                <p>Cinéma: ${p.cinema.nom} - ${p.cinema.adresse}</p>
                <p>Du ${p.date_deb} au ${p.date_fin}</p>
                <div class="creneaux-list">
                    ${p.creneaux.map(c => `<span class="creneau">${c.jour_semaine} ${c.heure_debut}</span>`).join('')}
                </div>
                <button onclick="showFilmDetail(${p.film.id})">Voir détails</button>
            </div>
        `).join('');
}

// Authentification
async function handleLogin(event) {
    event.preventDefault();
    const email = document.getElementById('login-email').value;
    const password = document.getElementById('login-password').value;
    
    try {
        currentUser = await apiCall('/login', {
            method: 'POST',
            body: JSON.stringify({ email, mdp: password })
        });
        localStorage.setItem('user', JSON.stringify(currentUser));
        updateAuthUI();
    } catch (error) {
        // Erreur déjà gérée par apiCall
    }
}

async function handleRegister(event) {
    event.preventDefault();
    const email = document.getElementById('register-email').value;
    const password = document.getElementById('register-password').value;
    
    try {
        currentUser = await apiCall('/register', {
            method: 'POST',
            body: JSON.stringify({ email, mdp: password })
        });
        localStorage.setItem('user', JSON.stringify(currentUser));
        updateAuthUI();
    } catch (error) {
        // Erreur déjà gérée
    }
}

// Client
function showClientPage() {
    hideAllPages();
    document.getElementById('client-page').style.display = 'block';
    loadReservations();
}

async function loadReservations() {
    const reservations = await apiCall(`/client/${currentUser.id}/reservations`);
    const container = document.getElementById('reservations-list');
    container.innerHTML = reservations.map(r => `
        <div class="reservation-card">
            <h4>${r.titre}</h4>
            <p>Cinéma: ${r.cinema_nom} - ${r.ville}</p>
            <p>Date: ${r.date_seance} à ${r.heure_seance}</p>
        </div>
    `).join('');
}

async function createReservation(progId, dateSeance, heureSeance) {
    if (!currentUser || currentUser.role !== 'client') {
        alert('Vous devez être connecté en tant que client');
        return;
    }
    
    try {
        await apiCall('/reservation', {
            method: 'POST',
            body: JSON.stringify({
                id_utilisateur: currentUser.id,
                id_programmation: progId,
                date_seance: dateSeance,
                heure_seance: heureSeance
            })
        });
        alert('Réservation créée!');
        showClientPage();
    } catch (error) {
        // Erreur déjà gérée
    }
}

// Proprio Film
function showProprioFilmPage() {
    hideAllPages();
    document.getElementById('proprio-film-page').style.display = 'block';
    loadMesFilms();
}

async function loadMesFilms() {
    const films = await apiCall(`/proprio-film/${currentUser.id}/films`);
    const container = document.getElementById('mes-films-list');
    container.innerHTML = films.map(f => `
        <div class="film-card">
            <h3>${f.titre}</h3>
            <p>Réalisateur: ${f.realisateur} | Durée: ${f.duree} min</p>
            <p>${f.nb_programmations} programmation(s)</p>
            <button onclick="deleteFilm(${f.id})">Supprimer</button>
        </div>
    `).join('');
}

function showAddFilm() {
    hideAllPages();
    document.getElementById('add-film-page').style.display = 'block';
}

async function handleAddFilm(event) {
    event.preventDefault();
    const film = {
        titre: document.getElementById('film-titre').value,
        duree: parseInt(document.getElementById('film-duree').value),
        langue: document.getElementById('film-langue').value,
        realisateur: document.getElementById('film-realisateur').value,
        age_min: parseInt(document.getElementById('film-age').value),
        sous_titre: document.getElementById('film-sous-titre').value
    };
    
    try {
        await apiCall(`/proprio-film/${currentUser.id}/film`, {
            method: 'POST',
            body: JSON.stringify(film)
        });
        alert('Film ajouté!');
        showProprioFilmPage();
    } catch (error) {
        // Erreur déjà gérée
    }
}

async function deleteFilm(filmId) {
    if (!confirm('Supprimer ce film?')) return;
    try {
        await apiCall(`/proprio-film/${currentUser.id}/film/${filmId}`, {
            method: 'DELETE'
        });
        loadMesFilms();
    } catch (error) {
        // Erreur déjà gérée
    }
}

// Proprio Cinema
function showProprioCinemaPage() {
    hideAllPages();
    document.getElementById('proprio-cinema-page').style.display = 'block';
    loadMesProgrammations();
}

async function loadMesProgrammations() {
    const progs = await apiCall(`/proprio-cinema/${currentUser.id}/programmations`);
    const container = document.getElementById('mes-programmations-list');
    container.innerHTML = progs.map(p => `
        <div class="programmation-card">
            <h4>${p.film.titre}</h4>
            <p>Du ${p.date_deb} au ${p.date_fin}</p>
            <div class="creneaux-list">
                ${p.creneaux.map(c => `<span class="creneau">${c.jour_semaine} ${c.heure_debut}</span>`).join('')}
            </div>
            <button onclick="deleteProgrammation(${p.id})">Supprimer</button>
        </div>
    `).join('');
}

async function showAddProgrammation() {
    hideAllPages();
    document.getElementById('add-programmation-page').style.display = 'block';
    
    const films = await apiCall(`/proprio-cinema/${currentUser.id}/films-disponibles`);
    const select = document.getElementById('prog-film');
    select.innerHTML = films.map(f => `<option value="${f.id}">${f.titre}</option>`).join('');
}

async function handleAddProgrammation(event) {
    event.preventDefault();
    
    const creneaux = Array.from(document.querySelectorAll('.creneau-item')).map(item => ({
        jour_semaine: item.querySelector('.creneau-jour').value,
        heure_debut: item.querySelector('.creneau-heure').value
    }));
    
    const prog = {
        id_film: parseInt(document.getElementById('prog-film').value),
        date_deb: document.getElementById('prog-date-deb').value,
        date_fin: document.getElementById('prog-date-fin').value,
        creneaux: creneaux
    };
    
    try {
        await apiCall(`/proprio-cinema/${currentUser.id}/programmation`, {
            method: 'POST',
            body: JSON.stringify(prog)
        });
        alert('Programmation créée!');
        showProprioCinemaPage();
    } catch (error) {
        // Erreur déjà gérée
    }
}

function addCreneau() {
    const container = document.getElementById('creneaux-container');
    const div = document.createElement('div');
    div.className = 'creneau-item';
    div.innerHTML = `
        <select class="creneau-jour">
            <option value="LUN">Lundi</option>
            <option value="MAR">Mardi</option>
            <option value="MER">Mercredi</option>
            <option value="JEU">Jeudi</option>
            <option value="VEN">Vendredi</option>
            <option value="SAM">Samedi</option>
            <option value="DIM">Dimanche</option>
        </select>
        <input type="time" class="creneau-heure" required>
        <button type="button" onclick="removeCreneau(this)">-</button>
    `;
    container.appendChild(div);
}

function removeCreneau(button) {
    button.parentElement.remove();
}

async function deleteProgrammation(progId) {
    if (!confirm('Supprimer cette programmation?')) return;
    try {
        await apiCall(`/proprio-cinema/${currentUser.id}/programmation/${progId}`, {
            method: 'DELETE'
        });
        loadMesProgrammations();
    } catch (error) {
        // Erreur déjà gérée
    }
}
