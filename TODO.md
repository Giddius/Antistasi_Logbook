# Todo's

## General Todo's



### Todo


- **Formatting**



> Go through all classes and change the visual order of the methods and properties to be consistent and make sense.

---


- **Refactoring**



> simplify and check each piece of code that is threading related!

---




### Idea


- **Feature**



> Create AAR-Animation via [ChangingSidesRecord](antistasi_logbook/records/antistasi_records.py#L511) entries for a certain 'Campaign_id' and have it play back by painting the locations with user controlled replay speed.

---


- **Performance**



> Make [amount_log_records](antistasi_logbook/gui/models/log_files_model.py#L71), [amount_warnings](antistasi_logbook/gui/models/log_files_model.py#L71) and [amount_errors](antistasi_logbook/gui/models/log_files_model.py#L71) of [LogFile](antistasi_logbook/gui/models/log_files_model.py#L71) and actual DB column and not a calculated Property. Maybe via Trigger or Table-function, better via the normal [update-mechanism](antistasi_logbook/gui/misc.py#L45)

---





## Code Todo's



### **Todo**


- **[antistasi\_logbook/\_\_init\_\_.py](antistasi_logbook/__init__.py#L25)**
    *Line-num: 25*



> Create release-task that auto-updates `INCLUDED_APSW_ENVIRONMENTS`, or find a way to parse the file names (unlikely, can't find UNIX format)

---


- **[antistasi\_logbook/\_\_init\_\_.py](antistasi_logbook/__init__.py#L31)**
    *Line-num: 31*



> create own library for somthing like that and replace 'pynotifier', because it emit deprecation warnings from wintypes

---


- **[antistasi\_logbook/\_\_init\_\_.py](antistasi_logbook/__init__.py#L42)**
    *Line-num: 42*



> Create general functions/classes for something like that in 'gidapptools'

---


- **[antistasi\_logbook/call\_tree/call\_tree\_item.py](antistasi_logbook/call_tree/call_tree_item.py#L63)**
    *Line-num: 63*



> This is Proof-of-Concept!

---


- **[antistasi\_logbook/parsing/parsing\_context.py](antistasi_logbook/parsing/parsing_context.py#L190)**
    *Line-num: 190*



> Refractor this Monster!

---


- **[antistasi\_logbook/records/record\_class\_manager.py](antistasi_logbook/records/record_class_manager.py#L108)**
    *Line-num: 108*



> make generic regarding record_classes selection

---


- **[antistasi\_logbook/updating/remote\_managers.py](antistasi_logbook/updating/remote_managers.py#L235)**
    *Line-num: 235*



> Custom Error

---


- **[antistasi\_logbook/utilities/path\_utilities.py](antistasi_logbook/utilities/path_utilities.py#L80)**
    *Line-num: 80*



> add custom error

---


