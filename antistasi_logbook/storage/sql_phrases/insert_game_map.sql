INSERT
    OR REPLACE INTO "GameMap_tbl" (
        "item_id",
        "name",
        "full_name",
        "official",
        "dlc",
        "map_image_path",
        "comments"
    )
VALUES
    (?, ?, ?, ?, ?, ?, ?);