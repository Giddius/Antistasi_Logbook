INSERT
    OR IGNORE INTO "RemoteType" ("name", "id")
VALUES
    ("local", 0);

INSERT
    OR IGNORE INTO "RemoteType" (
        "name",
        "id",
        "log_folder",
        "base_url",
        "login",
        "password"
    )
VALUES
    (
        "webdav",
        1,
        "Antistasi_Community_Logs",
        "https://antistasi.de/dev_drive/remote.php/dav/files",
        "Giddi",
        "erZPi-dCKpH-2baKg-cHZtK-zjBxE"
    );

INSERT
    OR IGNORE INTO "LogLevel" ("name", "id")
values
    ("NO_LEVEL", 0);

INSERT
    OR IGNORE INTO "LogLevel" ("name", "id")
values
    ("DEBUG", 1);

INSERT
    OR IGNORE INTO "LogLevel" ("name", "id")
values
    ("INFO", 2);

INSERT
    OR IGNORE INTO "LogLevel" ("name", "id")
values
    ("WARNING", 3);

INSERT
    OR IGNORE INTO "LogLevel" ("name", "id")
values
    ("CRITICAL", 4);

INSERT
    OR IGNORE INTO "LogLevel" ("name", "id")
values
    ("ERROR", 5);

INSERT
    OR IGNORE INTO "PunishmentAction" ("name", "id")
values
    ("NO_ACTION", 0);

INSERT
    OR IGNORE INTO "PunishmentAction" ("name", "id")
values
    ("WARNING", 1);

INSERT
    OR IGNORE INTO "PunishmentAction" ("name", "id")
values
    ("DAMAGE", 2);

INSERT
    OR IGNORE INTO "Server" ("name", "remote_path", "remote_type")
values
    ("NO_SERVER", "NO_PATH", 0);

INSERT
    OR IGNORE INTO "Server" ("name", "remote_path", "remote_type")
values
    (
        "Mainserver_1",
        "Antistasi_Community_Logs/Mainserver_1",
        1
    );

INSERT
    OR IGNORE INTO "Server" ("name", "remote_path", "remote_type")
values
    (
        "Mainserver_2",
        "Antistasi_Community_Logs/Mainserver_2",
        1
    );

INSERT
    OR IGNORE INTO "Server" ("name", "remote_path", "remote_type")
values
    (
        "Testserver_1",
        "Antistasi_Community_Logs/Testserver_1",
        1
    );

INSERT
    OR IGNORE INTO "Server" ("name", "remote_path", "remote_type")
values
    (
        "Testserver_2",
        "Antistasi_Community_Logs/Testserver_2",
        1
    );

INSERT
    OR IGNORE INTO "Server" ("name", "remote_path", "remote_type")
values
    (
        "Testserver_3",
        "Antistasi_Community_Logs/Testserver_3",
        1
    );

INSERT
    OR IGNORE INTO "Server" ("name", "remote_path", "remote_type")
values
    (
        "Eventserver",
        "Antistasi_Community_Logs/Eventserver",
        1
    );

INSERT
    Or IGNORE INTO "GameMap" (
        "name",
        "full_name",
        "official",
        "dlc"
    )
VALUES
    ("Altis", "Altis", 1, NULL);

INSERT
    Or IGNORE INTO "GameMap" (
        "name",
        "full_name",
        "official",
        "dlc"
    )
VALUES
    ("Tanoa", "Tanoa", 1, "Apex");

INSERT
    Or IGNORE INTO "GameMap" (
        "name",
        "full_name",
        "official",
        "dlc"
    )
VALUES
    ("Enoch", "Livonia", 1, "Contact");

INSERT
    Or IGNORE INTO "GameMap" (
        "name",
        "full_name",
        "official",
        "dlc"
    )
VALUES
    ("Malden", "Malden", 1, "Malden");

INSERT
    Or IGNORE INTO "GameMap" (
        "name",
        "full_name",
        "official",
        "dlc"
    )
VALUES
    ("takistan", "Takistan", 0, NULL);