# LouLa Ciné - Application de Gestion Cinéma

Application complète de gestion de cinéma avec backend FastAPI, frontend HTML/CSS/JS et base de données PostgreSQL.

## Structure du Projet

```
PROJET_XML/
├── backend/          # API FastAPI
│   ├── main.py
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/         # Interface web
│   ├── index.html
│   ├── styles.css
│   ├── app.js
│   └── Dockerfile
├── database/         # Schéma et données
│   ├── 01_init.sql
│   └── 02_seed.sql
└── docker-compose.yml
```

## Fonctionnalités

### Publiques
- Films à la une
- Recherche de films
- Détails d'un film avec programmations par ville
- Programmations par ville

### Client
- Création de compte
- Réservation de films
- Consultation des réservations

### Propriétaire Film
- Ajout de films
- Visualisation des films programmés
- Modification/Suppression de films

### Propriétaire Cinéma
- Programmation de films
- Modification/Suppression de programmations
- Gestion des créneaux horaires

## Installation et Lancement

### Prérequis
- Docker et Docker Compose installés

### Démarrage

```bash
# Démarrer tous les services
docker-compose up --build

# En arrière-plan
docker-compose up -d --build
```

Les services seront disponibles sur :
- Frontend : http://localhost:3000
- Backend API : http://localhost:8000
- Base de données : localhost:5432

### Arrêt

```bash
docker-compose down
```

## Utilisateurs de test

- **Propriétaire Film** : `owner_film1@cinema.fr` / `password`
- **Propriétaire Cinéma** : `owner_cinema1@cinema.fr` / `password`
- **Client** : Créer un compte via l'interface d'inscription

## API Documentation

L'API est accessible à `http://localhost:8000`

Documentation interactive : `http://localhost:8000/docs`

## Thème

Interface en **noir et rouge** pour LouLa Ciné 🎬
