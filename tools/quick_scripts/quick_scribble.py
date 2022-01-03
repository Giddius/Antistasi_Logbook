from pathlib import Path
import json
import pp

infile = Path(r"D:\Dropbox\hobby\Modding\Programs\Github\My_Repos\Antistasi_Logbook\antistasi_logbook\data\coordinates\chernarus_winter_pos.json")

old_data = json.loads(infile.read_text(encoding='utf-8', errors='ignore'))


new_data = {}


for cat, data in old_data.items():
    new_data[cat] = []
    for subdata in data:
        new_data[cat].append({"name": subdata[0], "x": subdata[1][0], "y": subdata[1][1]})


with infile.open("w", encoding='utf-8', errors='ignore') as f:
    json.dump(new_data, f, default=str, indent=4)
