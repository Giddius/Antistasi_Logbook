-- PRAGMA auto_vacuum = FULL;
PRAGMA journal_mode(OFF);

PRAGMA synchronous = OFF;

PRAGMA cache_size(-250000);

CREATE TABLE IF NOT EXISTS "LogLevel_tbl" (
    "item_id" INTEGER PRIMARY KEY,
    "name" TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS "PunishmentAction_tbl" (
    "item_id" INTEGER PRIMARY KEY,
    "name" TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS "Server_tbl" (
    "item_id" INTEGER PRIMARY KEY AUTOINCREMENT,
    "name" TEXT UNIQUE NOT NULL,
    "remote_path" REMOTEPATH UNIQUE NOT NULL,
    "local_path" PATH UNIQUE,
    "comments" TEXT
);

CREATE TABLE IF NOT EXISTS "GameMap_tbl" (
    "item_id" INTEGER PRIMARY KEY AUTOINCREMENT,
    "name" TEXT UNIQUE NOT NULL,
    "full_name" TEXT UNIQUE,
    "official" BOOL NOT NULL DEFAULT 0,
    "dlc" TEXT,
    "map_image_path" PATH,
    "comments" TEXT
);

CREATE TABLE IF NOT EXISTS "Mod_tbl" (
    "item_id" INTEGER PRIMARY KEY AUTOINCREMENT,
    "name" TEXT UNIQUE NOT NULL,
    "mod_dir" TEXT UNIQUE NOT NULL,
    "default" BOOL NOT NULL DEFAULT 0,
    "official" BOOL NOT NULL DEFAULT 0,
    "full_path" PATH UNIQUE,
    "hash" TEXT UNIQUE,
    "hashShort" TEXT UNIQUE,
    "Link" TEXT UNIQUE,
    "comments" TEXT
);

CREATE TABLE IF NOT EXISTS "LogFile_tbl" (
    "item_id" INTEGER PRIMARY KEY AUTOINCREMENT,
    "name" TEXT NOT NULL,
    "server" INTEGER NOT NULL REFERENCES "Server_tbl" ("item_id") ON DELETE CASCADE,
    "remote_path" REMOTEPATH UNIQUE NOT NULL,
    "size" INTEGER NOT NULL,
    "modified_at" DATETIME NOT NULL,
    "last_parsed_line_number" INTEGER DEFAULT 0,
    "finished" BOOL DEFAULT 0,
    "created_at" DATETIME,
    "game_map" INTEGER REFERENCES "GameMap_tbl" ("item_id") ON DELETE CASCADE,
    "header_text" TEXT,
    "utc_offset" INT,
    "comments" TEXT,
    UNIQUE("name", "server", "remote_path")
);

CREATE TABLE IF NOT EXISTS "LogFile_Mod_join_tbl" (
    "log_file_id" INTEGER NOT NULL REFERENCES "LogFile_tbl" ("item_id") ON DELETE CASCADE,
    "mod_id" INTEGER NOT NULL REFERENCES "Mod_tbl" ("item_id") ON DELETE CASCADE,
    UNIQUE("log_file_id", "mod_id")
);

CREATE TABLE IF NOT EXISTS "Message_tbl" (
    "item_id" INTEGER PRIMARY KEY AUTOINCREMENT,
    "message" TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS "LogRecord_tbl" (
    "item_id" INTEGER PRIMARY KEY AUTOINCREMENT,
    "recorded_at" DATETIME NOT NULL,
    "message" INTEGER NOT NULL REFERENCES "Message_tbl" ("item_id") ON DELETE CASCADE,
    "start" INTEGER NOT NULL,
    "end" INTEGER NOT NULL,
    "logged_from" TEXT,
    "called_by" TEXT,
    "client" TEXT,
    "log_level" INTEGER DEFAULT 0 REFERENCES "LogLevel_tbl" ("item_id") ON DELETE CASCADE,
    "punishment_action" INTEGER DEFAULT 0 REFERENCES "PunishmentAction_tbl" ("item_id") ON DELETE CASCADE,
    "log_file" INTEGER NOT NULL REFERENCES "LogFile_tbl" ("item_id") ON DELETE CASCADE,
    "comments" TEXT,
    "record_class" TEXT NOT NULL,
    UNIQUE("start", "end", "log_file", "record_class")
);