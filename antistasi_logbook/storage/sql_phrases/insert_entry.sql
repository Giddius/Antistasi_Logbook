INSERT
    OR REPLACE INTO "LogRecord_tbl" (
        "item_id",
        "record_class",
        "recorded_at",
        "log_file",
        "message",
        "start",
        "end",
        "logged_from",
        "called_by",
        "client",
        "log_level",
        "punishment_action",
        "comments"
    )
VALUES
    (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)