# Todo's

## General Todo's

### Todo

-   **Formatting**

> Go through all classes and change the visual order of the methods and properties to be consistent and make sense.

---

-   **Refactoring**

> simplify and check each piece of code that is threading related!

---

### Idea

-   **Feature**

> Create AAR-Animation via [ChangingSidesRecord](antistasi_logbook/records/antistasi_records.py#L645) entries for a certain 'Campaign_id' and have it play back by painting the locations with user controlled replay speed.

---

-   **Performance**

> Make [amount_log_records](antistasi_logbook/storage/models/models.py#L397), [amount_warnings](antistasi_logbook/storage/models/models.py#L407) and [amount_errors](antistasi_logbook/storage/models/models.py#L402) of [LogFile](antistasi_logbook/storage/models/models.py#L345) and actual DB column and not a calculated Property. Maybe via Trigger or Table-function, better via the normal [update-mechanism](antistasi_logbook/updating/updater.py#L58)

---

## Code Todo's

### **Todo**

-   **[antistasi_logbook/\_\_init\_\_.py](antistasi_logbook/__init__.py#L32)**
    _Line-num: 32_

> Create release-task that auto-updates `INCLUDED_APSW_ENVIRONMENTS`, or find a way to parse the file names (unlikely, can't find UNIX format)

---

-   **[antistasi_logbook/\_\_init\_\_.py](antistasi_logbook/__init__.py#L38)**
    _Line-num: 38_

> create own library for somthing like that and replace 'pynotifier', because it emit deprecation warnings from wintypes

---

-   **[antistasi_logbook/\_\_init\_\_.py](antistasi_logbook/__init__.py#L49)**
    _Line-num: 49_

> Create general functions/classes for something like that in 'gidapptools'

---

-   **[antistasi_logbook/call_tree/call_tree_item.py](antistasi_logbook/call_tree/call_tree_item.py#L63)**
    _Line-num: 63_

> This is Proof-of-Concept!

---

-   **[antistasi_logbook/gui/main_window.py](antistasi_logbook/gui/main_window.py#L357)**
    _Line-num: 357_

> Connect update_action to the Stausbar label and shut it down while updating and start it up afterwards

---

-   **[antistasi_logbook/gui/main_window.py](antistasi_logbook/gui/main_window.py#L430)**
    _Line-num: 430_

> Rewrite so everything starts through the app

---

-   **[antistasi_logbook/gui/models/base_query_data_model.py](antistasi_logbook/gui/models/base_query_data_model.py#L504)**
    _Line-num: 504_

> Fix this and make everything sortable, find out how!

---

-   **[antistasi_logbook/parsing/parsing_context.py](antistasi_logbook/parsing/parsing_context.py#L190)**
    _Line-num: 190_

> Refractor this Monster!

---

-   **[antistasi_logbook/records/record_class_manager.py](antistasi_logbook/records/record_class_manager.py#L108)**
    _Line-num: 108_

> make generic regarding record_classes selection

---

-   **[antistasi_logbook/updating/remote_managers.py](antistasi_logbook/updating/remote_managers.py#L235)**
    _Line-num: 235_

> Custom Error

---

-   **[antistasi_logbook/utilities/path_utilities.py](antistasi_logbook/utilities/path_utilities.py#L80)**
    _Line-num: 80_

> add custom error

---
