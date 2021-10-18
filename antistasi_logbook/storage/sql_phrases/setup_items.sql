PRAGMA journal_mode(OFF);

PRAGMA synchronous = OFF;

PRAGMA cache_size(-250000);

INSERT
    OR IGNORE INTO "LogLevel_tbl" ("name", "item_id")
values
    ("NO_LEVEL", 0);

INSERT
    OR IGNORE INTO "LogLevel_tbl" ("name", "item_id")
values
    ("DEBUG", 1);

INSERT
    OR IGNORE INTO "LogLevel_tbl" ("name", "item_id")
values
    ("INFO", 2);

INSERT
    OR IGNORE INTO "LogLevel_tbl" ("name", "item_id")
values
    ("WARNING", 3);

INSERT
    OR IGNORE INTO "LogLevel_tbl" ("name", "item_id")
values
    ("CRITICAL", 4);

INSERT
    OR IGNORE INTO "LogLevel_tbl" ("name", "item_id")
values
    ("ERROR", 5);

INSERT
    OR IGNORE INTO "PunishmentAction_tbl" ("name", "item_id")
values
    ("NO_ACTION", 0);

INSERT
    OR IGNORE INTO "PunishmentAction_tbl" ("name", "item_id")
values
    ("WARNING", 1);

INSERT
    OR IGNORE INTO "PunishmentAction_tbl" ("name", "item_id")
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