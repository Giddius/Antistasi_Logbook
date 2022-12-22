Glossary
========


.. glossary::
   :sorted:

   semi-semvar-version
      :samp:`<{major}>.<{minor}>.<{patch}>.<{extra(optional)}>`


   simple timestamp
      Timestamp that only contains hours, minutes, seconds. i.e. :samp:`{ 7}\:{21}\:{11}\ ` or :samp:`{11}\:{50}\:{57}\ `.


   full local timestamp
      Timestamp that contains date and time in the servers local timezone. i.e. :samp:`{2022/11/13}\, {11\:52\:52}`


   Header-text
      Text that is at the start of all Arma log-files and contains the Commandline used and basic infos about the server.

      .. dropdown:: Example

         from https://community.bistudio.com/wiki/Crash_Files#Log_File_Content_Explained

         .. code:: guess

            =====================================================================
            == C:\Program Files (x86)\Steam\steamapps\common\Arma 3\Arma3_x64.exe
            == "C:\Program Files (x86)\Steam\steamapps\common\Arma 3\Arma3_x64.exe" -skipIntro -noSplash -hugePages -showScriptErrors

            Original output filename: Arma3Retail_DX11_x64
            Exe timestamp: 2020/08/20 01:03:22
            Current time:  2020/09/06 10:35:03

            Type: Public
            Build: Development
            Version: 2.01.146606

            Allocator: C:\Program Files (x86)\Steam\steamapps\common\Arma 3\Dll\tbb4malloc_bi_x64.dll [2017.0.0.0] [2017.0.0.0]
            PhysMem: 24 GiB, VirtMem : 131072 GiB, AvailPhys : 18 GiB, AvailVirt : 131068 GiB, AvailPage : 19 GiB
            =====================================================================


   Entry
      A single log-message, that was emited from a single point in the code. A single entry means, that it does not depend on the position in the log or the other messages around it.
      If it depends on other messages aroung it, then they also belong to the entry.
      In allmost all cases it should only be from a single line of the log-file.
      Only in special cases, does an entry stretched over more than a single line and these special cases must either have a concrete syntax or start with special markers.


   Record
      An :term:`Entry` after it is processed, this means it has an assigned :term:`RecordClass` and all dates and times are converted to `UTC`.
      A Record knows about its content and has the ability to extract data from it.


   RecordClass
      The display-bridge of a :term:`Record`. It is specific to the message-content of the Record. If no RecordClass for a specific :term:`Record` can be determined, a Generic-RecordClass will be used.