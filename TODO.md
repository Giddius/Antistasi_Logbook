# Todo's

## General Todo's



### Todo


- [ ] **Bug**



> make it so that generic `Error in Expression` gets fully parsed including the file and line number into a single record

---


- [ ] **Formatting**



> Go through all classes and change the visual order of the methods and properties to be consistent and make sense.

---


- [ ] **Refactoring**



> simplify and check each piece of code that is threading related!

---




### Idea


- [ ] **Feature**



> Create AAR-Animation via [ChangingSidesRecord](antistasi_logbook/records/antistasi_records.py#L645) entries for a certain 'Campaign_id' and have it play back by painting the locations with user controlled replay speed.

---


- [ ] **Feature**



> Make it so that single [LogFile](antistasi_logbook/storage/models/models.py#L345) can be reparsed completely, on demand (context-menu)

---


- [ ] **Performance**



> Make [amount_log_records](antistasi_logbook/storage/models/models.py#L398), [amount_warnings](antistasi_logbook/storage/models/models.py#L410) and [amount_errors](antistasi_logbook/storage/models/models.py#L404) of [LogFile](antistasi_logbook/storage/models/models.py#L345) and actual DB column and not a calculated Property. Maybe via Trigger or Table-function, better via the normal [update-mechanism](antistasi_logbook/updating/updater.py#L58)

---





## Code Todo's



### **Todo**


- **[antistasi\_logbook/\_\_init\_\_.py](antistasi_logbook/__init__.py#L32)**
    *Line-num: 32*



> Create release-task that auto-updates `INCLUDED_APSW_ENVIRONMENTS`, or find a way to parse the file names (unlikely, can't find UNIX format)

---


- **[antistasi\_logbook/\_\_init\_\_.py](antistasi_logbook/__init__.py#L38)**
    *Line-num: 38*



> create own library for somthing like that and replace 'pynotifier', because it emit deprecation warnings from wintypes

---


- **[antistasi\_logbook/\_\_init\_\_.py](antistasi_logbook/__init__.py#L49)**
    *Line-num: 49*



> Create general functions/classes for something like that in 'gidapptools'

---


- **[antistasi\_logbook/call\_tree/call\_tree\_item.py](antistasi_logbook/call_tree/call_tree_item.py#L63)**
    *Line-num: 63*



> This is Proof-of-Concept!

---


- **[antistasi\_logbook/gui/main\_window.py](antistasi_logbook/gui/main_window.py#L354)**
    *Line-num: 354*



> Connect update_action to the Stausbar label and shut it down while updating and start it up afterwards

---


- **[antistasi\_logbook/gui/main\_window.py](antistasi_logbook/gui/main_window.py#L427)**
    *Line-num: 427*



> Rewrite so everything starts through the app

---


- **[antistasi\_logbook/gui/models/base\_query\_data\_model.py](antistasi_logbook/gui/models/base_query_data_model.py#L516)**
    *Line-num: 516*



> Fix this and make everything sortable, find out how!

---


- **[antistasi\_logbook/parsing/parsing\_context.py](antistasi_logbook/parsing/parsing_context.py#L191)**
    *Line-num: 191*



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


