Parsing
=======

.. card::
   :shadow: md
   :class-body: card-logbook-body


   Each Log-file goes through up to 4 different kinds of parsing steps:

   * :ref:`Meta-Data Parsing`
   * :ref:`Header-Text Parsing`
   * :ref:`Startup-Entries Parsing`
   * :ref:`Entries Parsing`
      * :ref:`Record Processing`
         * :ref:`Generic Records`
         * :ref:`Antistasi Records`


   .. dropdown:: Overview Image
      :color: secondary


      Image showing what is parsed by which part.

      * 🟨 -> Header-Text
      * 🟪 -> Startup-Entries
      * 🟥 -> Meta-Data
      * 🟧 -> Multiline entry


      .. image:: /_images/doc_example_log_file.png
         :scale: 10 %
         :align: center





Meta-Data Parsing
++++++++++++++++++

.. card::
   :shadow: md
   :class-body: card-logbook-body


   To parse the meda-data, the whole file has to be available.
   The Meta-Data parser goes through the file in chunks and tries to find each attribute via regex.

   It takes a 'LogFile'-Instance as input and copies all Meta-Data attributes that the 'LogFile' already has to itself.
   This means it only searches for those attributes that are missing on the 'LogFile'.

   .. card:: Meta-Data attributes
      :shadow: md

      * .. dropdown:: Game Map

         This has to be the arma internal used name (no spaces, can also differ from the display name like `virolahti` -> `vt7`)

         .. tab-set::

            .. tab-item:: Example

               .. code::

                  2022/11/13, 11:52:47  Mission world: cam_lao_nam

            .. tab-item:: Regex

               .. button-link:: https://regex101.com/r/smMRra/1
                  :color: primary
                  :shadow:

                  🔗explanation with regex101.com



               .. code:: python

                  re.compile(r"\sMission world\:\s*(?P<game_map>.*)")


      * .. dropdown:: Version

         A :term:`semi-semvar-version` is needed to be parseable


         .. tab-set::

            .. tab-item:: Example

               .. code::

                  2022/11/13, 11:53:11 2022-11-13 19:53:11:377 | Antistasi | Info | File: A3A_fnc_initServer | Server version: 2.6.1.872dbb3

            .. tab-item:: Regex

               .. button-link:: https://regex101.com/r/5qFKRc/1
                  :color: primary
                  :shadow:

                  🔗explanation with regex101.com


               .. code:: python

                  re.compile(r"\s*((MP server version)|(Server version)):\s*(?P<version>.*?)(?=\s|$)")



      * .. dropdown:: Mods

         It looks for the special delimited block of mods that arma puts in the logs by default and then processes each line as a possible mod.


         .. tab-set::

            .. tab-item:: Example

               .. include:: /_data/mod_example_text.txt


            .. tab-item:: Regex

               .. button-link:: https://regex101.com/r/G7BaoJ/1
                  :color: primary
                  :shadow:

                  🔗explanation with regex101.com


               .. include:: /_data/mod_regex_text.txt





      * .. dropdown::  Campaign ID

         Is only allowed to consist of digits. Currently this attribute also sets if the Log-file is from a new Campaign or loaded and continued from a saved Campaign.

         .. tab-set::

            .. tab-item:: Example

               .. code::

                  2022/07/04, 06:11:28 2022-07-04 13:11:28:248 | Antistasi | Info | File: A3A_fnc_initServer | Loading last campaign ID 93344

            .. tab-item:: Regex

               .. button-link:: https://regex101.com/r/8P312m/2
                  :color: primary
                  :shadow:

                  🔗explanation with regex101.com


               .. code:: python

                  re.compile(r"((?P<text_loading>(Loading last campaign ID)|(Loading campaign with ID))|(?P<text_creating>Creating new campaign with ID))\s*(?P<campaign_id>\d+)")


      * .. dropdown:: UTC offset of the log-file


         .. DANGER::

            if this attribute is not found, the log-file is marked as `unparsable` and will not be parsed any further.


         It does this by looking for the first log-entry it can find, that contains the full local datetime **AND** the full UTC datetime and calculate the offset from those two.

         .. tab-set::

            .. tab-item:: Example

               .. code::

                  2022/11/13, 11:53:11 2022-11-13 19:53:11:377 | Antistasi | Info | File: A3A_fnc_initServer | Server init started

            .. tab-item:: Regex


               .. button-link:: https://regex101.com/r/h51YxR/1
                  :color: primary
                  :shadow:

                  🔗explanation with regex101.com

               .. code:: python

                  re.compile(r"""^
                                 (?P<local_year>\d{4})
                                 /
                                 (?P<local_month>[01]\d)
                                 /
                                 (?P<local_day>[0-3]\d)
                                 \,\s+
                                 (?P<local_hour>[0-2]\d)
                                 \:
                                 (?P<local_minute>[0-6]\d)
                                 \:
                                 (?P<local_second>[0-6]\d)
                                 \s
                                 (?P<year>\d{4})
                                 \-
                                 (?P<month>[01]\d)
                                 \-
                                 (?P<day>[0-3]\d)
                                 \s
                                 (?P<hour>[0-2]\d)
                                 \:
                                 (?P<minute>[0-6]\d)
                                 \:
                                 (?P<second>[0-6]\d)
                                 \:
                                 (?P<microsecond>\d{3})
                                 (?=\s)""",
                                 re.VERBOSE | re.MULTILINE)



   To not use too much memory when reading large log-files and to not accidentally cut one of the search texts in half with chunking, it always keeps 2 chunks and processes the combined text of both.
   When reading a new chunk, the older one of the 2 stored gets discarded and the other one gets combined with the new one to create the new text to search.

   .. figure:: /_images/PairedReader_diagram.png
      :scale: 25 %
      :align: center

      The Mechanism of how the files are read.


   It will continue reading chunks and searching until one of the following conditions is fulfilled:

   * ☐ end of file reached
   * ☐ all meta-attributes found
   * ☐ it has read more than the set limit (in bytes), as all attributes should be able to be found (if they exist) in the beginning of a log-file.


Header-Text Parsing
++++++++++++++++++++

.. card::
   :shadow: md
   :class-body: card-logbook-body


   The :term:`Header-text`, that each arma log-file has, is parsed by collecting lines, until a line that starts with a :term:`simple timestamp`. That line is not consumed.

   .. note::
      The file-object position is not reset to zero after parsing the header-text.


Startup-Entries Parsing
++++++++++++++++++++++++

.. card::
   :shadow: md
   :class-body: card-logbook-body


   All lines from the end of the :term:`Header-text` to the first line that has a :term:`full local timestamp` are collected and stored unprocessed.
   This is done because most of the time these messages do not contain data that is usually checked and would bloat the database and slow down parsing.

   .. note::
      The file-object position is not reset to zero after parsing the header-text.


Entries Parsing
++++++++++++++++

.. card::
   :shadow: md
   :class-body: card-logbook-body


   .. note::
      This programm assumes that each line is a unique :term:`entry` and only in special cases, does an entry stretched over more than a single line.

      These special cases must either have a concrete syntax or start with special markers.

      **It is not advised to use multiline entries, not with the Logbook, but also not in General.**


   The Parser read the log-file line by line (using the `FileLineProvider` which gives easy access to the previous, current and the next line),
   if the line starts with a :term:`full local timestamp`, it stores the line and looks at the next line.
   If the next line

   * does not start with a full local timestamp
   * has a entry continuing-marker after the timestamp

   then it adds the next line also to the stored lines, if not it yields the stored lines as an entry and clears the line-storage.



   .. dropdown:: Flowchart
      :color: secondary

      .. raw:: html
         :file: ../../_data/entry_parsing_flowchart.svg


   .. admonition:: Future Plans

      This will probably change in the future, to be more flexible. If I am able to achieve this, the parsing will change to statemachine parser, that is extendable.
      It is mostly necessary for the default arma error entries, that often need knowledge of lines about 4 lines after the current one to check if they are still part of the entry.


Record Processing
------------------

.. card::
   :shadow: md
   :class-body: card-logbook-body



   .. warning::
      Most Code here will be changed in the near future as it currently is almost hardcoded specifically to Antistasi-logs. It will be changed to be more generic and also easier to extend.



Generic Records
~~~~~~~~~~~~~~~~~

.. card::
   :shadow: md
   :class-body: card-logbook-body



Antistasi Records
~~~~~~~~~~~~~~~~~~~


.. card::
   :shadow: md
   :class-body: card-logbook-body