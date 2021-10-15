INSERT
  OR REPLACE INTO "LogFile_tbl" (
    "id",
    "name",
    "server",
    "remote_path",
    "size",
    "modified_at",
    "created_at",
    "last_parsed_line_number",
    "finished",
    "game_map",
    "unparsable",
    "header_text",
    "comments"
  )
VALUES
  (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)