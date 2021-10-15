CREATE TABLE IF NOT EXISTS "LogLevel_tbl" (
  "id" INTEGER PRIMARY KEY,
  "name" TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS "PunishmentAction_tbl" (
  "id" INTEGER PRIMARY KEY,
  "name" TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS "Server_tbl" (
  "id" INTEGER PRIMARY KEY AUTOINCREMENT,
  "name" TEXT UNIQUE NOT NULL,
  "remote_path" REMOTEPATH UNIQUE NOT NULL,
  "local_path" PATH UNIQUE,
  "comments" TEXT
);

CREATE TABLE IF NOT EXISTS "GameMap_tbl" (
  "id" INTEGER PRIMARY KEY AUTOINCREMENT,
  "name" TEXT UNIQUE NOT NULL,
  "full_name" TEXT UNIQUE,
  "official" BOOL NOT NULL DEFAULT 0,
  "dlc" TEXT,
  "map_image_path" PATH,
  "comments" TEXT
);

INSERT
  Or IGNORE INTO "GameMap_tbl" (
    "name",
    "full_name",
    "official",
    "dlc",
    "map_image_path",
    "comments"
  )
VALUES
  ("Altis", "Altis", 1, NULL, NULL, NULL);

INSERT
  Or IGNORE INTO "GameMap_tbl" (
    "name",
    "full_name",
    "official",
    "dlc",
    "map_image_path",
    "comments"
  )
VALUES
  ("Tanoa", "Tanoa", 1, "Apex", NULL, NULL);

INSERT
  Or IGNORE INTO "GameMap_tbl" (
    "name",
    "full_name",
    "official",
    "dlc",
    "map_image_path",
    "comments"
  )
VALUES
  ("Enoch", "Livonia", 1, "Contact", NULL, NULL);

INSERT
  Or IGNORE INTO "GameMap_tbl" (
    "name",
    "full_name",
    "official",
    "dlc",
    "map_image_path",
    "comments"
  )
VALUES
  ("Malden", "Malden", 1, "Malden", NULL, NULL);

INSERT
  Or IGNORE INTO "GameMap_tbl" (
    "name",
    "full_name",
    "official",
    "dlc",
    "map_image_path",
    "comments"
  )
VALUES
  ("takistan", "Takistan", 0, NULL, NULL, NULL);

CREATE TABLE IF NOT EXISTS "Mod_tbl" (
  "id" INTEGER PRIMARY KEY AUTOINCREMENT,
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
  "id" INTEGER PRIMARY KEY AUTOINCREMENT,
  "name" TEXT NOT NULL,
  "server" INTEGER NOT NULL REFERENCES "Server_tbl" ("id") ON DELETE CASCADE,
  "remote_path" REMOTEPATH UNIQUE NOT NULL,
  "size" INTEGER NOT NULL,
  "modified_at" DATETIME NOT NULL,
  "last_parsed_line_number" INTEGER DEFAULT 0,
  "finished" BOOL DEFAULT 0,
  "created_at" DATETIME,
  "game_map" INTEGER REFERENCES "GameMap_tbl" ("id") ON DELETE CASCADE,
  "header_text" TEXT,
  "unparsable" BOOL,
  "comments" TEXT,
  UNIQUE("name", "server", "remote_path")
);

CREATE TABLE IF NOT EXISTS "LogFile_Mod_join_tbl" (
  "log_file_id" INTEGER NOT NULL REFERENCES "LogFile_tbl" ("id") ON DELETE CASCADE,
  "mod_id" INTEGER NOT NULL REFERENCES "Mod_tbl" ("id") ON DELETE CASCADE,
  UNIQUE("log_file_id", "mod_id")
);

CREATE TABLE IF NOT EXISTS "LogRecord_tbl" (
  "id" INTEGER PRIMARY KEY AUTOINCREMENT,
  "recorded_at" DATETIME NOT NULL,
  "message" TEXT NOT NULL,
  "start" INTEGER NOT NULL,
  "end" INTEGER NOT NULL,
  "logged_from" TEXT,
  "called_by" TEXT,
  "client" TEXT,
  "log_level" INTEGER DEFAULT 0 REFERENCES "LogLevel" ("id") ON DELETE CASCADE,
  "punishment_action" INTEGER DEFAULT 0 REFERENCES "PunishmentAction" ("id") ON DELETE CASCADE,
  "log_file" INTEGER NOT NULL REFERENCES "LogFile" ("id") ON DELETE CASCADE,
  "comments" TEXT,
  "record_class" TEXT NOT NULL,
  UNIQUE("start", "end", "log_file")
);

INSERT
  OR IGNORE INTO "LogLevel_tbl" ("name", "id")
values
  ("NO_LEVEL", 0);

INSERT
  OR IGNORE INTO "LogLevel_tbl" ("name", "id")
values
  ("DEBUG", 1);

INSERT
  OR IGNORE INTO "LogLevel_tbl" ("name", "id")
values
  ("INFO", 2);

INSERT
  OR IGNORE INTO "LogLevel_tbl" ("name", "id")
values
  ("WARNING", 3);

INSERT
  OR IGNORE INTO "LogLevel_tbl" ("name", "id")
values
  ("CRITICAL", 4);

INSERT
  OR IGNORE INTO "LogLevel_tbl" ("name", "id")
values
  ("ERROR", 5);

INSERT
  OR IGNORE INTO "PunishmentAction_tbl" ("name", "id")
values
  ("NO_ACTION", 0);

INSERT
  OR IGNORE INTO "PunishmentAction_tbl" ("name", "id")
values
  ("WARNING", 1);

INSERT
  OR IGNORE INTO "PunishmentAction_tbl" ("name", "id")
values
  ("DAMAGE", 2);

INSERT
  OR IGNORE INTO "Server_tbl" ("name", "remote_path")
values
  (
    "Mainserver_1",
    "Antistasi_Community_Logs/Mainserver_1"
  );

INSERT
  OR IGNORE INTO "Server_tbl" ("name", "remote_path")
values
  (
    "Mainserver_2",
    "Antistasi_Community_Logs/Mainserver_2"
  );

INSERT
  OR IGNORE INTO "Server_tbl" ("name", "remote_path")
values
  (
    "Testserver_1",
    "Antistasi_Community_Logs/Testserver_1"
  );

INSERT
  OR IGNORE INTO "Server_tbl" ("name", "remote_path")
values
  (
    "Testserver_2",
    "Antistasi_Community_Logs/Testserver_2"
  );

INSERT
  OR IGNORE INTO "Server_tbl" ("name", "remote_path")
values
  (
    "Testserver_3",
    "Antistasi_Community_Logs/Testserver_3"
  );

INSERT
  OR IGNORE INTO "Server_tbl" ("name", "remote_path")
values
  (
    "Eventserver",
    "Antistasi_Community_Logs/Eventserver"
  );

CREATE INDEX IF NOT EXISTS "idx_logfile__server" ON "LogFile_tbl" ("server");

CREATE INDEX IF NOT EXISTS "idx_logfile__name" ON "LogFile_tbl" ("name");

CREATE INDEX IF NOT EXISTS "idx_logfile__server_name" ON "LogFile_tbl" ("server", "name");

CREATE INDEX IF NOT EXISTS "idx_gamemap__offical" ON "GameMap_tbl" ("official");

CREATE INDEX IF NOT EXISTS "idx_gamemap__dlc" ON "GameMap_tbl" ("dlc");

-- CREATE INDEX IF NOT EXISTS "idx_logrecord__record_class" ON "LogRecord_tbl" ("record_class")
-- CREATE INDEX IF NOT EXISTS "idx_logrecord__log_file" ON "LogRecord_tbl" ("log_file");
-- CREATE INDEX IF NOT EXISTS "idx_logrecord__log_level" ON "LogRecord_tbl" ("log_level");
-- CREATE INDEX IF NOT EXISTS "idx_logrecord__created_at" ON "LogRecord_tbl" ("created_at");
-- CREATE INDEX IF NOT EXISTS "idx_logrecord__punishment_action" ON "LogRecord_tbl" ("punishment_action")