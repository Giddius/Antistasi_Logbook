INSERT
    OR IGNORE INTO "Mod" (
        "full_path",
        "mod_hash",
        "mod_hash_short",
        "mod_dir",
        "name",
        "default",
        "official",
        "marked"
    )
VALUES
    (?, ?, ?, ?, ?, ?, ?, ?)