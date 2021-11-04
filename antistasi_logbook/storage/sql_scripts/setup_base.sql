CREATE TABLE IF NOT EXISTS "LogLevel" (
    "id" INTEGER PRIMARY KEY,
    "name" TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS "PunishmentAction" (
    "id" INTEGER PRIMARY KEY,
    "name" TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS "RemoteStorage" (
    "id" INTEGER PRIMARY KEY,
    "name" TEXT UNIQUE NOT NULL,
    "base_url" URL,
    "login" BLOB,
    "password" BLOB,
    "manager_type" TEXT NOT NULL,
    UNIQUE("base_url", "login", "password", "manager_type")
);

CREATE TABLE IF NOT EXISTS "Server" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT,
    "local_path" PATH UNIQUE,
    "name" TEXT UNIQUE NOT NULL,
    "remote_path" REMOTEPATH UNIQUE,
    "remote_storage" INTEGER NOT NULL DEFAULT 0 REFERENCES "RemoteStorage" ("id") ON DELETE CASCADE,
    "update_enabled" BOOL NOT NULL DEFAULT 1,
    "comments" TEXT,
    "marked" BOOL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS "GameMap" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT,
    "full_name" TEXT UNIQUE,
    "name" TEXT UNIQUE NOT NULL,
    "official" BOOL NOT NULL DEFAULT 0,
    "dlc" TEXT,
    "map_image_high_resolution_path" BLOB,
    "map_image_low_resolution_path" BLOB,
    "coordinates" JSON,
    "workshop_link" URL,
    "comments" TEXT,
    "marked" BOOL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS "Mod" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT,
    "full_path" PATH,
    "hash" TEXT,
    "hash_short" TEXT,
    "link" TEXT,
    "mod_dir" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "default" BOOL NOT NULL DEFAULT 0,
    "official" BOOL NOT NULL DEFAULT 0,
    "comments" TEXT,
    "marked" BOOL DEFAULT 0,
    UNIQUE(
        "name",
        "mod_dir",
        "full_path",
        "hash",
        "hash_short"
    )
);

CREATE TABLE IF NOT EXISTS "LogFile" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT,
    "name" TEXT NOT NULL,
    "remote_path" REMOTEPATH UNIQUE NOT NULL,
    "modified_at" DATETIME NOT NULL,
    "size" INTEGER NOT NULL,
    "created_at" DATETIME,
    "finished" BOOL DEFAULT 0,
    "header_text" BLOB,
    "startup_text" BLOB,
    "last_parsed_line_number" INTEGER DEFAULT 0,
    "utc_offset" INT,
    "version" VERSION,
    "game_map" INTEGER REFERENCES "GameMap" ("id") ON DELETE CASCADE,
    "server" INTEGER NOT NULL REFERENCES "Server" ("id") ON DELETE CASCADE,
    "unparsable" BOOL DEFAULT 0,
    "comments" TEXT,
    "marked" BOOL DEFAULT 0,
    UNIQUE("name", "server", "remote_path")
);

CREATE TABLE IF NOT EXISTS "LogFile_and_Mod_join" (
    "log_file_id" INTEGER NOT NULL REFERENCES "LogFile" ("id") ON DELETE CASCADE,
    "mod_id" INTEGER NOT NULL REFERENCES "Mod" ("id") ON DELETE CASCADE,
    UNIQUE("log_file_id", "mod_id")
);

CREATE TABLE IF NOT EXISTS "RecordClass" (
    "id" INTEGER PRIMARY KEY,
    "name" TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS "AntstasiFunction" (
    "id" INTEGER PRIMARY KEY,
    "name" TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS "LogRecord" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT,
    "end" INTEGER NOT NULL,
    "start" INTEGER NOT NULL,
    "message" TEXT NOT NULL,
    "recorded_at" DATETIME NOT NULL,
    "called_by" INTEGER REFERENCES "AntstasiFunction" ("id") ON DELETE CASCADE,
    "client" TEXT,
    "is_antistasi_record" BOOL DEFAULT (0),
    "logged_from" INTEGER REFERENCES "AntstasiFunction" ("id") ON DELETE CASCADE,
    "log_file" INTEGER NOT NULL REFERENCES "LogFile" ("id") ON DELETE CASCADE,
    "log_level" INTEGER DEFAULT 0 REFERENCES "LogLevel" ("id") ON DELETE CASCADE,
    "punishment_action" INTEGER DEFAULT 0 REFERENCES "PunishmentAction" ("id") ON DELETE CASCADE,
    "record_class" INTEGER NOT NULL REFERENCES "RecordClass" ("id") ON DELETE CASCADE,
    "comments" TEXT,
    "marked" BOOL DEFAULT 0,
    UNIQUE("start", "end", "log_file", "record_class")
);