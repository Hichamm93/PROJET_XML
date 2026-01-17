from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from datetime import date, time
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from functools import wraps

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Connexion base de données
def get_db():
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST", "db"),
        database=os.getenv("DB_NAME", "cinema_db"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "postgres"),
        port=os.getenv("DB_PORT", "5432")
    )
    conn.set_session(autocommit=True)
    return conn

# Models
class FilmInfo(BaseModel):
    id: int
    titre: str
    duree: int
    langue: str
    realisateur: str
    age_min: int
    sous_titre: str

class CinemaInfo(BaseModel):
    id: int
    nom: str
    adresse: str
    ville: str

class CreneauInfo(BaseModel):
    jour_semaine: str
    heure_debut: str

class ProgrammationInfo(BaseModel):
    id: int
    cinema: CinemaInfo
    creneaux: List[CreneauInfo]
    date_deb: str
    date_fin: str

class FilmDetail(BaseModel):
    film: FilmInfo
    programmations: List[ProgrammationInfo]

class LoginRequest(BaseModel):
    email: str
    mdp: str

class UserCreate(BaseModel):
    email: str
    mdp: str

class FilmCreate(BaseModel):
    titre: str
    duree: int
    langue: str
    realisateur: str
    age_min: int
    sous_titre: str

class ProgrammationCreate(BaseModel):
    id_film: int
    date_deb: str
    date_fin: str
    creneaux: List[dict]

class ReservationCreate(BaseModel):
    id_utilisateur: int
    id_programmation: int
    date_seance: str
    heure_seance: str

# Routes publiques
@app.get("/")
def read_root():
    return {"message": "LouLa Ciné API"}

@app.get("/api/films-a-la-une")
def films_a_la_une():
    """Films à la une (premiers films avec programmation active)"""
    conn = get_db()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        SELECT DISTINCT f.id, f.titre, f.duree, f.langue, f.realisateur, f.age_min, f.sous_titre
        FROM cinema.film f
        JOIN cinema.programmation p ON f.id = p.id_film
        WHERE p.date_fin >= CURRENT_DATE
        ORDER BY f.id
        LIMIT 10
    """)
    films = cur.fetchall()
    cur.close()
    conn.close()
    return [dict(f) for f in films]

@app.get("/api/film/{film_id}")
def film_detail(film_id: int):
    """Détails d'un film avec programmations groupées par ville"""
    conn = get_db()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    # Info du film
    cur.execute("""
        SELECT id, titre, duree, langue, realisateur, age_min, sous_titre
        FROM cinema.film WHERE id = %s
    """, (film_id,))
    film = cur.fetchone()
    if not film:
        raise HTTPException(status_code=404, detail="Film non trouvé")
    
    # Programmations groupées par ville
    cur.execute("""
        SELECT p.id, p.date_deb, p.date_fin,
               c.id as cinema_id, c.nom, c.adresse, c.ville
        FROM cinema.programmation p
        JOIN cinema.cinema c ON p.id_cinema = c.id
        WHERE p.id_film = %s AND p.date_fin >= CURRENT_DATE
        ORDER BY c.ville, c.nom
    """, (film_id,))
    progs = cur.fetchall()
    
    # Créneaux pour chaque programmation
    result = {
        "film": dict(film),
        "programmations": []
    }
    
    for prog in progs:
        cur.execute("""
            SELECT jour_semaine, heure_debut::text
            FROM cinema.creneau_hebdo
            WHERE id_programmation = %s
        """, (prog['id'],))
        creneaux = cur.fetchall()
        
        result["programmations"].append({
            "id": prog['id'],
            "cinema": {
                "id": prog['cinema_id'],
                "nom": prog['nom'],
                "adresse": prog['adresse'],
                "ville": prog['ville']
            },
            "date_deb": str(prog['date_deb']),
            "date_fin": str(prog['date_fin']),
            "creneaux": [{"jour_semaine": c['jour_semaine'], "heure_debut": c['heure_debut']} for c in creneaux]
        })
    
    cur.close()
    conn.close()
    return result

@app.get("/api/search")
def search_films(q: str):
    """Recherche de films"""
    conn = get_db()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        SELECT id, titre, duree, langue, realisateur, age_min, sous_titre
        FROM cinema.film
        WHERE titre ILIKE %s OR realisateur ILIKE %s
        LIMIT 20
    """, (f"%{q}%", f"%{q}%"))
    films = cur.fetchall()
    cur.close()
    conn.close()
    return [dict(f) for f in films]

@app.get("/api/ville/{ville}/programmations")
def programmations_ville(ville: str):
    """Toutes les programmations à venir pour une ville"""
    conn = get_db()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        SELECT p.id, p.date_deb, p.date_fin,
               f.id as film_id, f.titre, f.duree, f.realisateur,
               c.id as cinema_id, c.nom, c.adresse
        FROM cinema.programmation p
        JOIN cinema.film f ON p.id_film = f.id
        JOIN cinema.cinema c ON p.id_cinema = c.id
        WHERE c.ville = %s AND p.date_fin >= CURRENT_DATE
        ORDER BY p.date_deb, f.titre
    """, (ville,))
    progs = cur.fetchall()
    
    result = []
    for prog in progs:
        cur.execute("""
            SELECT jour_semaine, heure_debut::text
            FROM cinema.creneau_hebdo
            WHERE id_programmation = %s
        """, (prog['id'],))
        creneaux = cur.fetchall()
        
        result.append({
            "id": prog['id'],
            "film": {
                "id": prog['film_id'],
                "titre": prog['titre'],
                "duree": prog['duree'],
                "realisateur": prog['realisateur']
            },
            "cinema": {
                "id": prog['cinema_id'],
                "nom": prog['nom'],
                "adresse": prog['adresse']
            },
            "date_deb": str(prog['date_deb']),
            "date_fin": str(prog['date_fin']),
            "creneaux": [{"jour_semaine": c['jour_semaine'], "heure_debut": c['heure_debut']} for c in creneaux]
        })
    
    cur.close()
    conn.close()
    return result

@app.get("/api/villes")
def liste_villes():
    """Liste des villes disponibles"""
    conn = get_db()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT DISTINCT ville FROM cinema.cinema ORDER BY ville")
    villes = cur.fetchall()
    cur.close()
    conn.close()
    return [v['ville'] for v in villes]

# Authentification
@app.post("/api/login")
def login(login_data: LoginRequest):
    """Connexion utilisateur"""
    conn = get_db()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        SELECT id, email, role FROM cinema.utilisateur
        WHERE email = %s AND mdp = %s
    """, (login_data.email, login_data.mdp))
    user = cur.fetchone()
    cur.close()
    conn.close()
    
    if not user:
        raise HTTPException(status_code=401, detail="Email ou mot de passe incorrect")
    
    return {"id": user['id'], "email": user['email'], "role": user['role']}

@app.post("/api/register")
def register(user_data: UserCreate):
    """Création compte client"""
    conn = get_db()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        cur.execute("""
            INSERT INTO cinema.utilisateur (email, mdp, role)
            VALUES (%s, %s, 'client')
            RETURNING id, email, role
        """, (user_data.email, user_data.mdp))
        user = cur.fetchone()
        conn.commit()
        return {"id": user['id'], "email": user['email'], "role": user['role']}
    except psycopg2.IntegrityError:
        raise HTTPException(status_code=400, detail="Email déjà utilisé")
    finally:
        cur.close()
        conn.close()

# Partie client
@app.post("/api/reservation")
def creer_reservation(reservation: ReservationCreate):
    """Créer une réservation"""
    conn = get_db()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    cur.execute("""
        INSERT INTO cinema.reservation (id_utilisateur, id_programmation, date_seance, heure_seance)
        VALUES (%s, %s, %s, %s)
        RETURNING id
    """, (reservation.id_utilisateur, reservation.id_programmation, reservation.date_seance, reservation.heure_seance))
    res = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    return {"id": res['id'], "message": "Réservation créée"}

@app.get("/api/client/{user_id}/reservations")
def mes_reservations(user_id: int):
    """Liste des réservations d'un client"""
    conn = get_db()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        SELECT r.id, r.date_seance, r.heure_seance,
               f.titre, f.duree, c.nom as cinema_nom, c.ville
        FROM cinema.reservation r
        JOIN cinema.programmation p ON r.id_programmation = p.id
        JOIN cinema.film f ON p.id_film = f.id
        JOIN cinema.cinema c ON p.id_cinema = c.id
        WHERE r.id_utilisateur = %s AND r.date_seance >= CURRENT_DATE
        ORDER BY r.date_seance, r.heure_seance
    """, (user_id,))
    reservations = cur.fetchall()
    cur.close()
    conn.close()
    return [dict(r) for r in reservations]

# Partie proprio_film
@app.post("/api/proprio-film/{user_id}/film")
def ajouter_film(user_id: int, film: FilmCreate):
    """Ajouter un film"""
    conn = get_db()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        INSERT INTO cinema.film (titre, duree, langue, realisateur, age_min, sous_titre, id_utilisateur)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        RETURNING id, titre
    """, (film.titre, film.duree, film.langue, film.realisateur, film.age_min, film.sous_titre, user_id))
    new_film = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    return {"id": new_film['id'], "titre": new_film['titre']}

@app.get("/api/proprio-film/{user_id}/films")
def mes_films(user_id: int):
    """Films du propriétaire avec leurs programmations"""
    conn = get_db()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        SELECT f.id, f.titre, f.duree, f.langue, f.realisateur, f.age_min, f.sous_titre,
               COUNT(DISTINCT p.id) as nb_programmations
        FROM cinema.film f
        LEFT JOIN cinema.programmation p ON f.id = p.id_film
        WHERE f.id_utilisateur = %s
        GROUP BY f.id
        ORDER BY f.titre
    """, (user_id,))
    films = cur.fetchall()
    cur.close()
    conn.close()
    return [dict(f) for f in films]

@app.delete("/api/proprio-film/{user_id}/film/{film_id}")
def supprimer_film(user_id: int, film_id: int):
    """Supprimer un film et ses programmations"""
    conn = get_db()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    # Vérifier que le film appartient à l'utilisateur
    cur.execute("SELECT id_utilisateur FROM cinema.film WHERE id = %s", (film_id,))
    film = cur.fetchone()
    if not film or film['id_utilisateur'] != user_id:
        raise HTTPException(status_code=403, detail="Film non trouvé ou accès refusé")
    
    # Supprimer les créneaux, puis les programmations, puis le film
    cur.execute("""
        DELETE FROM cinema.creneau_hebdo
        WHERE id_programmation IN (SELECT id FROM cinema.programmation WHERE id_film = %s)
    """, (film_id,))
    cur.execute("DELETE FROM cinema.programmation WHERE id_film = %s", (film_id,))
    cur.execute("DELETE FROM cinema.film WHERE id = %s", (film_id,))
    conn.commit()
    cur.close()
    conn.close()
    return {"message": "Film supprimé"}

@app.put("/api/proprio-film/{user_id}/film/{film_id}")
def modifier_film(user_id: int, film_id: int, film: FilmCreate):
    """Modifier un film"""
    conn = get_db()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    cur.execute("SELECT id_utilisateur FROM cinema.film WHERE id = %s", (film_id,))
    f = cur.fetchone()
    if not f or f['id_utilisateur'] != user_id:
        raise HTTPException(status_code=403, detail="Film non trouvé ou accès refusé")
    
    cur.execute("""
        UPDATE cinema.film
        SET titre = %s, duree = %s, langue = %s, realisateur = %s, age_min = %s, sous_titre = %s
        WHERE id = %s
    """, (film.titre, film.duree, film.langue, film.realisateur, film.age_min, film.sous_titre, film_id))
    conn.commit()
    cur.close()
    conn.close()
    return {"message": "Film modifié"}

# Partie proprio_cinema
@app.get("/api/proprio-cinema/{user_id}/films-disponibles")
def films_disponibles(user_id: int):
    """Tous les films disponibles pour programmation"""
    conn = get_db()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        SELECT id, titre, duree, langue, realisateur, age_min, sous_titre
        FROM cinema.film
        ORDER BY titre
    """)
    films = cur.fetchall()
    cur.close()
    conn.close()
    return [dict(f) for f in films]

@app.get("/api/proprio-cinema/{user_id}/cinema")
def mon_cinema(user_id: int):
    """Récupérer le cinéma du propriétaire"""
    conn = get_db()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        SELECT id, nom, adresse, ville FROM cinema.cinema WHERE id_utilisateur = %s
    """, (user_id,))
    cinema = cur.fetchone()
    cur.close()
    conn.close()
    if not cinema:
        raise HTTPException(status_code=404, detail="Cinéma non trouvé")
    return dict(cinema)

@app.post("/api/proprio-cinema/{user_id}/programmation")
def creer_programmation(user_id: int, prog: ProgrammationCreate):
    """Créer une programmation"""
    conn = get_db()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    # Récupérer le cinéma du propriétaire
    cur.execute("SELECT id FROM cinema.cinema WHERE id_utilisateur = %s", (user_id,))
    cinema = cur.fetchone()
    if not cinema:
        raise HTTPException(status_code=404, detail="Cinéma non trouvé")
    
    cinema_id = cinema['id']
    
    # Créer la programmation
    cur.execute("""
        INSERT INTO cinema.programmation (id_film, id_cinema, date_deb, date_fin)
        VALUES (%s, %s, %s, %s)
        RETURNING id
    """, (prog.id_film, cinema_id, prog.date_deb, prog.date_fin))
    prog_id = cur.fetchone()['id']
    
    # Ajouter les créneaux
    for creneau in prog.creneaux:
        cur.execute("""
            INSERT INTO cinema.creneau_hebdo (jour_semaine, heure_debut, id_programmation)
            VALUES (%s, %s, %s)
        """, (creneau['jour_semaine'], creneau['heure_debut'], prog_id))
    
    conn.commit()
    cur.close()
    conn.close()
    return {"id": prog_id, "message": "Programmation créée"}

@app.get("/api/proprio-cinema/{user_id}/programmations")
def mes_programmations(user_id: int):
    """Programmations du cinéma"""
    conn = get_db()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        SELECT c.id as cinema_id FROM cinema.cinema c WHERE c.id_utilisateur = %s
    """, (user_id,))
    cinema = cur.fetchone()
    if not cinema:
        raise HTTPException(status_code=404, detail="Cinéma non trouvé")
    
    cur.execute("""
        SELECT p.id, p.date_deb, p.date_fin,
               f.id as film_id, f.titre, f.duree, f.realisateur
        FROM cinema.programmation p
        JOIN cinema.film f ON p.id_film = f.id
        WHERE p.id_cinema = %s
        ORDER BY p.date_deb
    """, (cinema['cinema_id'],))
    progs = cur.fetchall()
    
    result = []
    for prog in progs:
        cur.execute("""
            SELECT jour_semaine, heure_debut::text
            FROM cinema.creneau_hebdo
            WHERE id_programmation = %s
        """, (prog['id'],))
        creneaux = cur.fetchall()
        result.append({
            "id": prog['id'],
            "film": {"id": prog['film_id'], "titre": prog['titre'], "duree": prog['duree']},
            "date_deb": str(prog['date_deb']),
            "date_fin": str(prog['date_fin']),
            "creneaux": [{"jour_semaine": c['jour_semaine'], "heure_debut": c['heure_debut']} for c in creneaux]
        })
    
    cur.close()
    conn.close()
    return result

@app.delete("/api/proprio-cinema/{user_id}/programmation/{prog_id}")
def supprimer_programmation(user_id: int, prog_id: int):
    """Supprimer une programmation"""
    conn = get_db()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    cur.execute("""
        SELECT p.id FROM cinema.programmation p
        JOIN cinema.cinema c ON p.id_cinema = c.id
        WHERE p.id = %s AND c.id_utilisateur = %s
    """, (prog_id, user_id))
    if not cur.fetchone():
        raise HTTPException(status_code=403, detail="Programmation non trouvée")
    
    cur.execute("DELETE FROM cinema.creneau_hebdo WHERE id_programmation = %s", (prog_id,))
    cur.execute("DELETE FROM cinema.programmation WHERE id = %s", (prog_id,))
    conn.commit()
    cur.close()
    conn.close()
    return {"message": "Programmation supprimée"}

@app.put("/api/proprio-cinema/{user_id}/programmation/{prog_id}")
def modifier_programmation(user_id: int, prog_id: int, prog: ProgrammationCreate):
    """Modifier une programmation"""
    conn = get_db()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    cur.execute("""
        SELECT p.id FROM cinema.programmation p
        JOIN cinema.cinema c ON p.id_cinema = c.id
        WHERE p.id = %s AND c.id_utilisateur = %s
    """, (prog_id, user_id))
    if not cur.fetchone():
        raise HTTPException(status_code=403, detail="Programmation non trouvée")
    
    # Mettre à jour la programmation
    cur.execute("""
        UPDATE cinema.programmation
        SET id_film = %s, date_deb = %s, date_fin = %s
        WHERE id = %s
    """, (prog.id_film, prog.date_deb, prog.date_fin, prog_id))
    
    # Supprimer et recréer les créneaux
    cur.execute("DELETE FROM cinema.creneau_hebdo WHERE id_programmation = %s", (prog_id,))
    for creneau in prog.creneaux:
        cur.execute("""
            INSERT INTO cinema.creneau_hebdo (jour_semaine, heure_debut, id_programmation)
            VALUES (%s, %s, %s)
        """, (creneau['jour_semaine'], creneau['heure_debut'], prog_id))
    
    conn.commit()
    cur.close()
    conn.close()
    return {"message": "Programmation modifiée"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
