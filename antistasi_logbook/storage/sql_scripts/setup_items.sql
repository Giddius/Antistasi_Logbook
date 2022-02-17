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
    OR IGNORE INTO LogLevel (id, name)
VALUES
    (0, "NO_LEVEL"),
    (1, "DEBUG"),
    (2, "INFO"),
    (3, "WARNING"),
    (4, "CRITICAL"),
    (5, "ERROR");

INSERT
    OR IGNORE INTO Server (
        local_path,
        name,
        remote_path,
        remote_storage,
        update_enabled,
        comments,
        marked
    )
VALUES
    (NULL, "NO_SERVER", "NO_PATH", 0, 0, NULL, 0),
    (
        NULL,
        "Mainserver_1",
        "Antistasi_Community_Logs/Mainserver_1/Server/",
        1,
        1,
        NULL,
        0
    ),
    (
        NULL,
        "Mainserver_2",
        "Antistasi_Community_Logs/Mainserver_2/Server/",
        1,
        1,
        NULL,
        0
    ),
    (
        NULL,
        "Testserver_1",
        "Antistasi_Community_Logs/Testserver_1/Server/",
        1,
        1,
        NULL,
        0
    ),
    (
        NULL,
        "Testserver_2",
        "Antistasi_Community_Logs/Testserver_2/Server/",
        1,
        1,
        NULL,
        0
    ),
    (
        NULL,
        "Testserver_3",
        "Antistasi_Community_Logs/Testserver_3/Server/",
        1,
        1,
        NULL,
        0
    ),
    (
        NULL,
        "Eventserver",
        "Antistasi_Community_Logs/Eventserver/Server/",
        1,
        0,
        NULL,
        0
    );

INSERT
    OR IGNORE INTO GameMap (
        full_name,
        name,
        official,
        dlc,
        map_image_high_resolution,
        map_image_low_resolution,
        coordinates,
        workshop_link,
        comments,
        marked
    )
VALUES
    (
        "Altis",
        "Altis",
        1,
        NULL,
        NULL,
        NULL,
        NULL,
        NULL,
        NULL,
        0
    ),
    (
        "Tanoa",
        "Tanoa",
        1,
        "Apex",
        NULL,
        NULL,
        NULL,
        NULL,
        NULL,
        0
    ),
    (
        "Livonia",
        "Enoch",
        1,
        "Contact",
        NULL,
        NULL,
        NULL,
        NULL,
        NULL,
        0
    ),
    (
        "Malden",
        "Malden",
        1,
        "Malden",
        NULL,
        NULL,
        NULL,
        NULL,
        NULL,
        0
    ),
    (
        "Takistan",
        "takistan",
        0,
        NULL,
        NULL,
        NULL,
        NULL,
        NULL,
        NULL,
        0
    ),
    (
        "Virolahti",
        "vt7",
        0,
        NULL,
        NULL,
        NULL,
        NULL,
        "https://steamcommunity.com/workshop/filedetails/?id=1926513010",
        NULL,
        0
    ),
    (
        "Sahrani",
        "sara",
        0,
        NULL,
        NULL,
        NULL,
        NULL,
        "https://steamcommunity.com/sharedfiles/filedetails/?id=583544987",
        NULL,
        0
    ),
    (
        "Chernarus Winter",
        "Chernarus_Winter",
        0,
        NULL,
        NULL,
        NULL,
        NULL,
        "https://steamcommunity.com/sharedfiles/filedetails/?id=583544987",
        NULL,
        0
    ),
    (
        "Anizay",
        "tem_anizay",
        0,
        NULL,
        NULL,
        NULL,
        NULL,
        "https://steamcommunity.com/workshop/filedetails/?id=1537973181",
        NULL,
        0
    ),
    (
        "Tembelan",
        "Tembelan",
        0,
        NULL,
        NULL,
        NULL,
        NULL,
        "https://steamcommunity.com/workshop/filedetails/?id=1252091296",
        NULL,
        0
    );

INSERT
    OR IGNORE INTO GameMap (
        full_name,
        name,
        official,
        dlc,
        map_image_high_resolution,
        map_image_low_resolution,
        coordinates,
        workshop_link,
        comments,
        marked
    )
VALUES
    (
        "Cam Lao Nam",
        "cam_lao_nam",
        1,
        "S.O.G. Prairie Fire",
        NULL,
        NULL,
        NULL,
        NULL,
        NULL,
        0
    ),
    (
        "Khe Sanh",
        "vn_khe_sanh",
        1,
        "S.O.G. Prairie Fire",
        NULL,
        NULL,
        NULL,
        NULL,
        NULL,
        0
    );

INSERT
    OR IGNORE INTO ArmaFunction (id, name)
VALUES
    (1, "init"),
    (2, "initServer"),
    (3, "initParams"),
    (4, "initFuncs"),
    (5, "JN_fnc_arsenal_init"),
    (6, "initVar"),
    (7, "initVarCommon"),
    (8, "initVarServer"),
    (9, "initDisabledMods"),
    (10, "compatibilityLoadFaction");

INSERT
    OR IGNORE INTO ArmaFunction (id, name)
VALUES
    (11, "registerUnitType"),
    (12, "aceModCompat"),
    (13, "initVarClient"),
    (14, "initACEUnconsciousHandler"),
    (15, "loadNavGrid"),
    (16, "initZones"),
    (17, "initSpawnPlaces"),
    (18, "initGarrisons"),
    (19, "loadServer"),
    (20, "returnSavedStat");

INSERT
    OR IGNORE INTO ArmaFunction (id, name)
VALUES
    (21, "getStatVariable"),
    (22, "loadStat"),
    (23, "updatePreference"),
    (24, "tierCheck"),
    (25, "initPetros"),
    (26, "createPetros"),
    (27, "assignBossIfNone"),
    (28, "loadPlayer"),
    (29, "addHC"),
    (30, "advancedTowingInit");

INSERT
    OR IGNORE INTO ArmaFunction (id, name)
VALUES
    (31, "logPerformance"),
    (32, "initServer"),
    (33, "onPlayerDisconnect"),
    (34, "savePlayer"),
    (35, "vehKilledOrCaptured"),
    (36, "postmortem"),
    (37, "scheduler"),
    (38, "distance"),
    (39, "theBossToggleEligibility"),
    (40, "retrievePlayerStat");

INSERT
    OR IGNORE INTO ArmaFunction (id, name)
VALUES
    (41, "resetPlayer"),
    (42, "HR_GRG_fnc_addVehicle"),
    (43, "punishment_FF"),
    (44, "HR_GRG_fnc_removeFromPool"),
    (45, "HR_GRG_fnc_toggleLock"),
    (46, "unlockEquipment"),
    (47, "arsenalManage"),
    (48, "economicsAI"),
    (49, "resourcecheck"),
    (50, "promotePlayer");

INSERT
    OR IGNORE INTO ArmaFunction (id, name)
VALUES
    (51, "reinforcementsAI"),
    (52, "AAFroadPatrol"),
    (53, "createAIAction"),
    (54, "selectReinfUnits"),
    (55, "createConvoy"),
    (56, "findSpawnPosition"),
    (57, "milBuildings"),
    (58, "placeIntel"),
    (59, "createAIOutposts"),
    (60, "convoyMovement");

INSERT
    OR IGNORE INTO ArmaFunction (id, name)
VALUES
    (61, "rebelAttack"),
    (62, "rebelAttack"),
    (63, "markerChange"),
    (64, "freeSpawnPositions"),
    (65, "punishment"),
    (66, "supportAvailable"),
    (67, "sendSupport"),
    (68, "createSupport"),
    (69, "SUP_mortar"),
    (70, "chooseSupport");

INSERT
    OR IGNORE INTO ArmaFunction (id, name)
VALUES
    (71, "AIreactOnKill"),
    (72, "findBaseForQRF"),
    (73, "SUP_QRF"),
    (74, "getVehiclePoolForQRFs"),
    (75, "spawnVehicleAtMarker"),
    (76, "endSupport"),
    (77, "findAirportForAirstrike"),
    (78, "SUP_ASF"),
    (79, "addSupportTarget"),
    (80, "zoneCheck");

INSERT
    OR IGNORE INTO ArmaFunction (id, name)
VALUES
    (81, "AIVEHinit"),
    (82, "createAIResources"),
    (83, "saveLoop"),
    (84, "vehiclePrice"),
    (85, "patrolReinf"),
    (86, "SUP_mortarRoutine"),
    (87, "theBossTransfer"),
    (88, "setPlaneLoadout"),
    (89, "SUP_ASFRoutine"),
    (90, "createAttackVehicle");

INSERT
    OR IGNORE INTO ArmaFunction (id, name)
VALUES
    (91, "SUP_QRFRoutine"),
    (92, "spawnConvoy"),
    (93, "spawnConvoyLine"),
    (94, "despawnConvoy"),
    (95, "ConvoyTravelAir"),
    (96, "paradrop"),
    (97, "SUP_airstrike"),
    (98, "findPathPrecheck"),
    (99, "findPath"),
    (100, "airspaceControl");

INSERT
    OR IGNORE INTO ArmaFunction (id, name)
VALUES
    (101, "callForSupport"),
    (102, "SUP_airstrikeRoutine"),
    (103, "convoy"),
    (104, "airbomb"),
    (105, "mrkWIN"),
    (106, "occupantInvaderUnitKilledEH"),
    (107, "singleAttack"),
    (108, "getVehiclePoolForAttacks"),
    (109, "SUP_QRFAvailable"),
    (110, "wavedCA");

INSERT
    OR IGNORE INTO ArmaFunction (id, name)
VALUES
    (111, "garbageCleaner"),
    (112, "missionRequest"),
    (113, "minefieldAAF"),
    (114, "attackDrillAI"),
    (115, "invaderPunish"),
    (116, "vehicleConvoyTravel"),
    (117, "SUP_CAS"),
    (118, "splitVehicleCrewIntoOwnGroups"),
    (119, "makePlayerBossIfEligible"),
    (120, "replenishGarrison");

INSERT
    OR IGNORE INTO ArmaFunction (id, name)
VALUES
    (121, "HQGameOptions"),
    (122, "vehicleConvoyTravel"),
    (123, "WPCreate"),
    (124, "createVehicleQRFBehaviour"),
    (125, "AIVEHinit"),
    (126, "SUP_CASRoutine"),
    (127, "SUP_CASRun"),
    (128, "startBreachVehicle"),
    (129, "spawnDebuggingLoop"),
    (130, "SUP_SAM");

INSERT
    OR IGNORE INTO ArmaFunction (id, name)
VALUES
    (131, "cleanserVeh"),
    (132, "SUP_SAMRoutine"),
    (133, "punishment_release"),
    (134, "logistics_unload"),
    (135, "rebuildRadioTower"),
    (136, "roadblockFight"),
    (137, "HR_GRG_fnc_getCatIndex"),
    (138, "punishment_sentence_server"),
    (139, "punishment_checkStatus"),
    (140, "taskUpdate");

INSERT
    OR IGNORE INTO ArmaFunction (id, name)
VALUES
    (141, "punishment_FF_addEH"),
    (142, "askHelp"),
    (143, "unconscious"),
    (144, "handleDamage"),
    (145, "unconsciousAAF"),
    (146, "createCIV"),
    (147, "initPreJIP"),
    (148, "preInit"),
    (149, "init"),
    (150, "detector");

INSERT
    OR IGNORE INTO ArmaFunction (id, name)
VALUES
    (151, "selector"),
    (152, "TV_verifyLoadoutsData"),
    (153, "TV_verifyAssets"),
    (154, "compileMissionAssets"),
    (155, "createAIcontrols"),
    (156, "createAICities"),
    (157, "createAIAirplane"),
    (158, "spawnGroup"),
    (159, "fillLootCrate"),
    (160, "getNearestNavPoint");

INSERT
    OR IGNORE INTO ArmaFunction (id, name)
VALUES
    (161, "arePositionsConnected"),
    (162, "surrenderAction"),
    (163, "NATOinit"),
    (164, "chooseAttackType"),
    (165, "vehicleConvoyTravel"),
    (166, "RES_Refugees"),
    (167, "SUP_"),
    (168, "CIVinit"),
    (169, "onConvoyArrival"),
    (170, "HR_GRG_fnc_validateGarage");

INSERT
    OR IGNORE INTO ArmaFunction (id, name)
VALUES
    (171, "HR_GRG_fnc_loadSaveData"),
    (172, "compatabilityLoadFaction"),
    (173, "spawnHCGroup"),
    (174, "AS_Traitor"),
    (175, "LOG_Supplies"),
    (176, "DES_Heli"),
    (177, "LOG_Salvage"),
    (178, "ConvoyTravel");