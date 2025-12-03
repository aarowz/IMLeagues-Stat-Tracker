
-- ============================================================
-- TABLE CREATION
-- ============================================================

CREATE DATABASE IF NOT EXISTS im_league_tracker;
USE im_league_tracker;

DROP TABLE IF EXISTS Player_Awards;
DROP TABLE IF EXISTS Champions;
DROP TABLE IF EXISTS Reminders;
DROP TABLE IF EXISTS StatEvent;
DROP TABLE IF EXISTS Games_Keepers;
DROP TABLE IF EXISTS Players_Games;
DROP TABLE IF EXISTS Teams_Games;
DROP TABLE IF EXISTS Teams_Players;
DROP TABLE IF EXISTS Games;
DROP TABLE IF EXISTS Players;
DROP TABLE IF EXISTS Teams;
DROP TABLE IF EXISTS Stat_Keepers;
DROP TABLE IF EXISTS Rules;
DROP TABLE IF EXISTS Leagues;
DROP TABLE IF EXISTS Sports;

-- ============================================================
-- STRONG ENTITIES
-- ============================================================

-- Sports table
CREATE TABLE Sports (
    sport_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT
);

-- Leagues table
CREATE TABLE Leagues (
    league_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    sport_played INT NOT NULL,
    max_teams INT,
    league_start DATE,
    league_end DATE,
    semester VARCHAR(20),
    year INT,
    FOREIGN KEY (sport_played) REFERENCES Sports(sport_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);

-- Rules table
CREATE TABLE Rules (
    rules_id INT AUTO_INCREMENT PRIMARY KEY,
    sports_id INT NOT NULL,
    team_size INT,
    league_size INT,
    season_length INT,
    game_length INT,
    description TEXT,
    FOREIGN KEY (sports_id) REFERENCES Sports(sport_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);

-- Teams table
CREATE TABLE Teams (
    team_id INT AUTO_INCREMENT PRIMARY KEY,
    founded_date DATE,
    name VARCHAR(100) NOT NULL,
    league_played INT NOT NULL,
    wins INT DEFAULT 0,
    losses INT DEFAULT 0,
    FOREIGN KEY (league_played) REFERENCES Leagues(league_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);

-- Players table
CREATE TABLE Players (
    player_id INT AUTO_INCREMENT PRIMARY KEY,
    phone_number VARCHAR(15) UNIQUE,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL
);

-- Stat_Keepers table
CREATE TABLE Stat_Keepers (
    keeper_id INT AUTO_INCREMENT PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    total_games_tracked INT DEFAULT 0
);

-- Games table
CREATE TABLE Games (
    game_id INT AUTO_INCREMENT PRIMARY KEY,
    attendance INT,
    league_played INT NOT NULL,
    date_played DATE NOT NULL,
    start_time TIME,
    location VARCHAR(100),
    home_score INT DEFAULT 0,
    away_score INT DEFAULT 0,
    FOREIGN KEY (league_played) REFERENCES Leagues(league_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);

-- StatEvent table
CREATE TABLE StatEvent (
    event_id INT AUTO_INCREMENT PRIMARY KEY,
    performed_by INT NOT NULL,
    scored_during INT NOT NULL,
    description TEXT,
    time_entered DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (performed_by) REFERENCES Players(player_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    FOREIGN KEY (scored_during) REFERENCES Games(game_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);

-- Reminders table
CREATE TABLE Reminders (
    reminder_id INT AUTO_INCREMENT PRIMARY KEY,
    priority VARCHAR(20) DEFAULT 'medium',
    message TEXT NOT NULL,
    time_sent DATETIME DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) DEFAULT 'pending',
    team_id INT NOT NULL,
    game_id INT,
    FOREIGN KEY (team_id) REFERENCES Teams(team_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    FOREIGN KEY (game_id) REFERENCES Games(game_id)
        ON DELETE SET NULL
        ON UPDATE CASCADE
);

-- Player_Awards table
CREATE TABLE Player_Awards (
    award_id INT AUTO_INCREMENT PRIMARY KEY,
    description TEXT,
    recipient INT NOT NULL,
    award_type VARCHAR(100) NOT NULL,
    year INT NOT NULL,
    FOREIGN KEY (recipient) REFERENCES Players(player_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);

-- Champions table
CREATE TABLE Champions (
    champion_id INT AUTO_INCREMENT PRIMARY KEY,
    winner INT NOT NULL,
    league_id INT NOT NULL,
    year INT NOT NULL,
    FOREIGN KEY (winner) REFERENCES Teams(team_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    FOREIGN KEY (league_id) REFERENCES Leagues(league_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);

-- ============================================================
-- BRIDGE TABLES (for M:N relationships)
-- ============================================================

-- Teams_Players bridge table
CREATE TABLE Teams_Players (
    player_id INT,
    team_id INT,
    role VARCHAR(20) DEFAULT 'player',
    PRIMARY KEY (player_id, team_id),
    FOREIGN KEY (player_id) REFERENCES Players(player_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    FOREIGN KEY (team_id) REFERENCES Teams(team_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);

-- Teams_Games bridge table
CREATE TABLE Teams_Games (
    team_id INT,
    game_id INT,
    is_home_team BOOLEAN DEFAULT FALSE,
    PRIMARY KEY (team_id, game_id),
    FOREIGN KEY (team_id) REFERENCES Teams(team_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    FOREIGN KEY (game_id) REFERENCES Games(game_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);

-- Players_Games bridge table (for game lineups)
CREATE TABLE Players_Games (
    player_id INT,
    game_id INT,
    is_starter BOOLEAN DEFAULT FALSE,
    position VARCHAR(50),
    PRIMARY KEY (player_id, game_id),
    FOREIGN KEY (player_id) REFERENCES Players(player_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    FOREIGN KEY (game_id) REFERENCES Games(game_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);

-- Games_Keepers bridge table
CREATE TABLE Games_Keepers (
    keeper_id INT,
    game_id INT,
    assignment_date DATE DEFAULT (CURRENT_DATE),
    PRIMARY KEY (keeper_id, game_id),
    FOREIGN KEY (keeper_id) REFERENCES Stat_Keepers(keeper_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    FOREIGN KEY (game_id) REFERENCES Games(game_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);
