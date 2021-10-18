INSERT
    OR REPLACE INTO "LogFile_tbl" (
        "item_id",
        "name",
        "server",
        "remote_path",
        "size",
        "modified_at",
        "created_at",
        "last_parsed_line_number",
        "finished",
        "game_map",
        "header_text",
        "utc_offset",
        "comments"
    )
VALUES
    (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)