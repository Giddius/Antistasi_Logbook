INSERT
    OR IGNORE INTO "RemoteStorage" ("name", "id", "base_url", "manager_type")
VALUES
    ("local_files", 0, "--LOCAL--", "LocalManager");

INSERT
    OR IGNORE INTO "RemoteStorage" (
        "name",
        "id",
        "base_url",
        "manager_type"
    )
VALUES
    (
        "community_webdav",
        1,
        "https://antistasi.de",
        "WebdavManager"
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
    OR IGNORE INTO "PunishmentAction" ("name", "id")
values
    ("COLLISION", 3);

INSERT
    OR IGNORE INTO "PunishmentAction" ("name", "id")
values
    ("RELEASE", 4);

INSERT
    OR IGNORE INTO "PunishmentAction" ("name", "id")
values
    ("GUILTY", 5);

INSERT
    OR IGNORE INTO "Server" (
        "name",
        "remote_path",
        "remote_storage",
        "update_enabled"
    )
values
    ("NO_SERVER", "NO_PATH", 0, 0);

INSERT
    OR IGNORE INTO "Server" ("name", "remote_path", "remote_storage")
values
    (
        "Mainserver_1",
        "Antistasi_Community_Logs/Mainserver_1/Server/",
        1
    );

INSERT
    OR IGNORE INTO "Server" ("name", "remote_path", "remote_storage")
values
    (
        "Mainserver_2",
        "Antistasi_Community_Logs/Mainserver_2/Server/",
        1
    );

INSERT
    OR IGNORE INTO "Server" ("name", "remote_path", "remote_storage")
values
    (
        "Testserver_1",
        "Antistasi_Community_Logs/Testserver_1/Server/",
        1
    );

INSERT
    OR IGNORE INTO "Server" ("name", "remote_path", "remote_storage")
values
    (
        "Testserver_2",
        "Antistasi_Community_Logs/Testserver_2/Server/",
        1
    );

INSERT
    OR IGNORE INTO "Server" ("name", "remote_path", "remote_storage")
values
    (
        "Testserver_3",
        "Antistasi_Community_Logs/Testserver_3/Server/",
        1
    );

INSERT
    OR IGNORE INTO "Server" (
        "name",
        "remote_path",
        "remote_storage",
        "update_enabled"
    )
values
    (
        "Eventserver",
        "Antistasi_Community_Logs/Eventserver/Server/",
        1,
        0
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

INSERT
    Or IGNORE INTO "GameMap" (
        "name",
        "full_name",
        "official",
        "dlc",
        "workshop_link"
    )
VALUES
    (
        "vt7",
        "Virolahti",
        0,
        NULL,
        "https://steamcommunity.com/workshop/filedetails/?id=1926513010"
    );

INSERT
    Or IGNORE INTO "GameMap" (
        "name",
        "full_name",
        "official",
        "dlc",
        "workshop_link"
    )
VALUES
    (
        "sara",
        "Sahrani",
        0,
        NULL,
        "https://steamcommunity.com/sharedfiles/filedetails/?id=583544987"
    );

INSERT
    Or IGNORE INTO "GameMap" (
        "name",
        "full_name",
        "official",
        "dlc",
        "workshop_link"
    )
VALUES
    (
        "Chernarus_Winter",
        "Chernarus Winter",
        0,
        NULL,
        "https://steamcommunity.com/sharedfiles/filedetails/?id=583544987"
    );

INSERT
    Or IGNORE INTO "GameMap" (
        "name",
        "full_name",
        "official",
        "dlc",
        "workshop_link"
    )
VALUES
    (
        "tem_anizay",
        "Anizay",
        0,
        NULL,
        "https://steamcommunity.com/workshop/filedetails/?id=1537973181"
    );