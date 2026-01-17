-- 01_init.sql
-- Schéma + tables pour le projet (PostgreSQL)
-- Tout est créé dans le schéma: cinema

CREATE SCHEMA IF NOT EXISTS cinema;
SET search_path TO cinema;

-- ----------------------------
-- Table: acteur
-- ----------------------------
CREATE TABLE IF NOT EXISTS acteur (
  id SERIAL PRIMARY KEY,
  nom VARCHAR(255) NOT NULL,
  prenom VARCHAR(255) NOT NULL
);

-- ----------------------------
-- Table: utilisateur
-- ----------------------------
CREATE TABLE IF NOT EXISTS utilisateur (
  id SERIAL PRIMARY KEY,
  email VARCHAR(255) NOT NULL UNIQUE,
  mdp VARCHAR(255) NOT NULL,
  role VARCHAR(255) NOT NULL
);

-- ----------------------------
-- Table: film
-- ----------------------------
CREATE TABLE IF NOT EXISTS film (
  id SERIAL PRIMARY KEY,
  titre VARCHAR(255) NOT NULL,
  duree INT NOT NULL,
  langue VARCHAR(255) NOT NULL,
  realisateur VARCHAR(255) NOT NULL,
  age_min INT NOT NULL,
  sous_titre VARCHAR(255) NOT NULL,
  id_utilisateur INTEGER NOT NULL REFERENCES cinema.utilisateur(id)
);

-- ----------------------------
-- Table: cinema
-- ----------------------------
CREATE TABLE IF NOT EXISTS cinema (
  id SERIAL PRIMARY KEY,
  nom VARCHAR(255) NOT NULL,
  adresse VARCHAR(255) NOT NULL,
  ville VARCHAR(255) NOT NULL,
  id_utilisateur INTEGER NOT NULL REFERENCES cinema.utilisateur(id)
);

-- ----------------------------
-- Table: joue (Many-to-Many acteur <-> film)
-- ----------------------------
CREATE TABLE IF NOT EXISTS joue (
  id_acteur INTEGER NOT NULL REFERENCES cinema.acteur(id),
  id_film   INTEGER NOT NULL REFERENCES cinema.film(id),
  PRIMARY KEY (id_acteur, id_film)
);

-- ----------------------------
-- Table: programmation
-- ----------------------------
CREATE TABLE IF NOT EXISTS programmation (
  id SERIAL PRIMARY KEY,
  date_deb DATE NOT NULL,
  date_fin DATE NOT NULL,
  id_film   INTEGER NOT NULL REFERENCES cinema.film(id),
  id_cinema INTEGER NOT NULL REFERENCES cinema.cinema(id),
  CONSTRAINT chk_dates CHECK (date_fin >= date_deb)
);

-- ----------------------------
-- Table: creneau_hebdo
-- (jour_semaine en VARCHAR pour éviter soucis Hibernate/ENUM PG)
-- ----------------------------
CREATE TABLE IF NOT EXISTS creneau_hebdo (
  id SERIAL PRIMARY KEY,
  jour_semaine VARCHAR(3) NOT NULL,
  heure_debut TIME NOT NULL,
  id_programmation INTEGER NOT NULL REFERENCES cinema.programmation(id)
);
