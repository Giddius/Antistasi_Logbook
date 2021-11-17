import pytest
from antistasi_logbook.parsing.parser import Parser, SimpleRegexKeeper, RawRecord, RecordLine, Version, ModItem
from pathlib import Path
from typing import Union, Optional, Mapping, Iterable, Hashable
from datetime import datetime
from dateutil.tz import UTC
from dateutil.parser import parse as dateutil_parse

THIS_FILE_DIR = Path(__file__).parent.absolute()

PARSE_RECORDS_TEST_FILE_DIR = THIS_FILE_DIR.joinpath("parameter_files", "parse_records_parameter_files")

test_parse_entries_parameter = []

test_parse_entries_parameter_1_file = PARSE_RECORDS_TEST_FILE_DIR.joinpath("simple_records_file_1.txt")

test_parse_entries_parameter_1_expected = []
test_parse_entries_parameter_1_expected.append(RawRecord([RecordLine("2021/10/05, 08:40:59 [CBA] (xeh) INFO: [12189,153.042,0] PreInit finished.", 1)]))
test_parse_entries_parameter_1_expected.append(RawRecord([RecordLine('2021/10/05, 08:40:59 "armahosts/BIS_fnc_log: [preInit] CBA_fnc_preInit (707.001 ms)"', 2)]))
test_parse_entries_parameter_1_expected.append(RawRecord([RecordLine('2021/10/05, 08:40:59 "armahosts/BIS_fnc_log: [preInit] HR_GRG_fnc_initServer (1.00708 ms)"', 3)]))
test_parse_entries_parameter_1_expected.append(RawRecord([RecordLine('2021/10/05, 08:40:59 PortableHelipadLight_01_white_F: light_1_blinking - unknown animation source MarkerLight (defined in AnimationSources::Light_1_source)', 4)]))

test_parse_entries_parameter.append((test_parse_entries_parameter_1_file, test_parse_entries_parameter_1_expected))


test_parse_entries_parameter_2_file = PARSE_RECORDS_TEST_FILE_DIR.joinpath("simple_records_file_2.txt")

test_parse_entries_parameter_2_expected = test_parse_entries_parameter_1_expected.copy()
test_parse_entries_parameter_2_expected.append(RawRecord([RecordLine('2021/11/06, 02:42:58 2021-11-06 09:42:58:958 | Antistasi | Debug | File: fn_initServer.sqf | Land_New_WiredFence_10m_F killed by UNKNOWN', 5)]))
test_parse_entries_parameter_2_expected.append(RawRecord([RecordLine("2021/11/06, 02:43:03 Can't change owner from 0 to 2", 6)]))
test_parse_entries_parameter_2_expected.append(RawRecord([RecordLine('2021/11/06, 02:42:58 2021-11-06 09:42:58:997 | Antistasi | Debug | File: fn_initServer.sqf |  killed by UNKNOWN', 7)]))
test_parse_entries_parameter_2_expected.append(
    RawRecord([RecordLine("2021/11/08, 10:26:07 2021-11-08 18:26:07:393 | Antistasi | Debug | File: A3A_fnc_createAttackVehicle | Spawn Performed: Created vehicle UK3CB_BAF_Merlin_HC3_18_GPMG_DPMT_RM with 12 soldiers | Called By: A3A_fnc_SUP_QRF", 8)]))

test_parse_entries_parameter.append((test_parse_entries_parameter_2_file, test_parse_entries_parameter_2_expected))


test_parse_entries_parameter_3_file = PARSE_RECORDS_TEST_FILE_DIR.joinpath("multiline_records_file_1.txt")


test_parse_entries_parameter_3_expected = test_parse_entries_parameter_2_expected.copy()
test_parse_entries_parameter_3_expected.append(RawRecord([RecordLine('2021/11/08, 08:26:14 Error in expression <gress", 0];', 9), RecordLine("_progress = _progress - (1 / (((_decayTimeMax - (_decayTimeMax - _d>", 10)]))
test_parse_entries_parameter_3_expected.append(RawRecord([RecordLine("2021/11/08, 08:22:19 2021-11-08 16:22:19:760 | Antistasi | Info | File: A3A_fnc_saveLoop | Starting persistent save", 11)]))

test_parse_entries_parameter.append((test_parse_entries_parameter_3_file, test_parse_entries_parameter_3_expected))


test_parse_entries_parameter_4_file = PARSE_RECORDS_TEST_FILE_DIR.joinpath("single_record_multiline_1.txt")
test_parse_entries_parameter_4_expected = [RawRecord([RecordLine(content='2021/11/08, 06:02:46 2021-11-08 14:02:46:402 | Antistasi | Debug | File: A3A_fnc_freeSpawnPositions | Spawn places for outpost_9 [', start=1),
                                                     RecordLine(
                                                         content='>>> [[[[9250.17,5118.31,0.1],359.565],false],[[[9255.55,5118.35,0.1],359.565],true],[[[9260.92,5118.39,0.1],359.565],false],[[[9266.29,5118.43,0.1],359.565],false],[[[9271.66,5118.47,0.1],359.565],false],[[[9277.03,5118.51,0.1],359.565],false],[[[9282.4,5118.55,0.1],359.565],false]]', start=2),
                                                     RecordLine(content='>>> [[[[9269.75,5152.01,0.4],1.00179e-005],false]]', start=3),
                                                     RecordLine(content='>>> []', start=4),
                                                     RecordLine(content='>>> []', start=5),
                                                     RecordLine(content='>>> ] | Called By: A3A_fnc_findBaseForQRF', start=6)])]
test_parse_entries_parameter.append((test_parse_entries_parameter_4_file, test_parse_entries_parameter_4_expected))

test_parse_entries_parameter_5_file = PARSE_RECORDS_TEST_FILE_DIR.joinpath("single_record_multiline_2.txt")
test_parse_entries_parameter_5_expected = [RawRecord([RecordLine(content='2021/11/08, 06:02:46 2021-11-08 14:02:46:400 | Antistasi | Debug | File: A3A_fnc_freeSpawnPositions | Spawn places for airport [', start=1),
                                                      RecordLine(
                                                          content='>>> [[[[9312.57,4879.49,0.1],0],false],[[[9317.92,4879.49,0.1],0],false],[[[9323.27,4879.49,0.1],0],false],[[[9328.62,4879.49,0.1],0],false],[[[9333.97,4879.49,0.1],0],false],[[[9232.14,4874.04,0.1],0],false],[[[9237.49,4874.04,0.1],0],true],[[[9242.83,4874.04,0.1],0],false],[[[9248.18,4874.04,0.1],0],false],[[[9253.53,4874.04,0.1],0],false]]', start=2),
                                                      RecordLine(content='>>> [[[[9199.5,4872.5,0.4],0],false],[[[9174.5,4872.5,0.4],0],false]]', start=3),
                                                      RecordLine(content='>>> [[[[9354.78,4858.85,0.1],270],false],[[[9354.77,4821.33,0.350112],270],false],[[[9354.75,4783.82,0.834962],270],false]]', start=4),
                                                      RecordLine(content='>>> [[[[9355.79,4802.36,0.1],0],false],[[[9179.59,4776.29,0.1],0],false]]', start=5),
                                                      RecordLine(content='>>> ] | Called By: A3A_fnc_findBaseForQRF', start=6)])]
test_parse_entries_parameter.append((test_parse_entries_parameter_5_file, test_parse_entries_parameter_5_expected))

test_parse_entries_parameter_6_file = PARSE_RECORDS_TEST_FILE_DIR.joinpath("single_record_multiline_split_1.txt")
test_parse_entries_parameter_6_expected = [RawRecord([RecordLine("""2021/11/05, 10:56:11 2021-11-05 17:56:11:363 | Antistasi | Debug | File: A3A_fnc_economicsAI | Occupants arsenal [""", 1),
                                                     RecordLine(""">>> ["RHS_TOW_TriPod_WD",19.6549]""", 2),
                                                     RecordLine(""">>> ["RHS_Stinger_AA_pod_WD",20.9627]""", 3),
                                                     RecordLine(""">>> ["UK3CB_BAF_FV432_Mk3_GPMG_Green_DPMT",3.97412]""", 4),
                                                     RecordLine(""">>> ["UK3CB_BAF_FV432_Mk3_RWS_Green_DPMT",6.92176]""", 5),
                                                     RecordLine(""">>> ["UK3CB_BAF_Warrior_A3_W_MTP",3.35]""", 6),
                                                     RecordLine(""">>> ["UK3CB_BAF_Warrior_A3_W_Cage_MTP",0.37353]""", 7),
                                                     RecordLine(""">>> ["UK3CB_BAF_Warrior_A3_W_Cage_Camo_MTP",5.69824]""", 8),
                                                     RecordLine(""">>> ["UK3CB_BAF_Warrior_A3_W_Camo_MTP",6.06529]""", 9),
                                                      RecordLine(""">>> ["rhsusf_m1a1aimwd_usarmy",7.69294]""", 10),
                                                     RecordLine(""">>> ["RHS_M6_wd",8.93059]""", 11),
                                                     RecordLine(""">>> ["UK3CB_BAF_RHIB_HMG_DDPM",17.7412]""", 12),
                                                     RecordLine(""">>> ["RHS_A10",2.71446]""", 13),
                                                     RecordLine(""">>> ["rhsusf_f22",2.83432]""", 14),
                                                     RecordLine(""">>> ["UK3CB_BAF_Hercules_C3_DDPM",8.43971]""", 15),
                                                     RecordLine(""">>> ["UK3CB_BAF_Hercules_C4_DDPM",12.0029]""", 16),
                                                     RecordLine(""">>> ["UK3CB_BAF_Wildcat_AH1_TRN_8A_DDPM_RM",13.2525]""", 17),
                                                     RecordLine(""">>> ["UK3CB_BAF_Merlin_HC3_18_GPMG_DDPM_RM",8.96569]""", 18),
                                                     RecordLine(""">>> ["UK3CB_BAF_Chinook_HC1_DDPM",11.2819]""", 19),
                                                     RecordLine(""">>> ["UK3CB_BAF_Apache_AH1_CAS_DDPM_RM",3.75059]""", 20),
                                                     RecordLine(""">>> ["UK3CB_BAF_Apache_AH1_DDPM_RM",2.57059]""", 21),
                                                     RecordLine(""">>> ["UK3CB_BAF_Wildcat_AH1_CAS_6A_DDPM_RM",4.64]""", 22),
                                                      RecordLine(""">>>""", 23),
                                                     RecordLine(""">>> ["UK3CB_BAF_Wildcat_AH1_CAS_8A",5]""", 24),
                                                     RecordLine(""">>> ["rhsusf_m109_usarmy",6.67088]""", 25),
                                                     RecordLine(""">>> ] | Called By: A3A_fnc_resourcecheck""", 26), ])]

test_parse_entries_parameter.append((test_parse_entries_parameter_6_file, test_parse_entries_parameter_6_expected))


@pytest.mark.parametrize("log_file, expected", test_parse_entries_parameter, ids=[i[0].stem for i in test_parse_entries_parameter])
def test_parse_entries(fake_parsing_context_class, log_file, expected):
    parser = Parser(database=None, regex_keeper=SimpleRegexKeeper())
    with fake_parsing_context_class(log_file=log_file) as context:
        result = list(parser.parse_entries(context=context))
    for idx, r in enumerate(result):
        assert r.start == expected[idx].start
        assert r.end == expected[idx].end
        assert r.content == expected[idx].content
    assert result == expected


PARSE_HEADER_LINES_TEST_FILE_DIR = THIS_FILE_DIR.joinpath("parameter_files", "parse_header_lines_parameter_files")
test_parse_header_lines_parameter = []
parse_header_lines_file_1 = PARSE_HEADER_LINES_TEST_FILE_DIR.joinpath("simple_header_lines_1.txt")
parse_header_lines_expected_1 = r"""=====================================================================
== C:\TCAFiles\Users\Antistasi\2433\arma3server_x64.exe
== "C:\TCAFiles\Users\Antistasi\2433\arma3server_x64.exe" -port=2312   -MaxMem=16384 -filePatching -collection= "-servermod=@members;@utility;@TaskForceEnforcer;" "-mod=@ace;@ACECompatRHSArmedForcesoftheRussianFederation;@ACECompatRHSGREF;@ACECompatRHSUnitedStatesArmedForces;@CBAA3;@RHSAFRF;@RHSGREF;@RHSUSAF;@TaskForceArrowheadRadioBETA;@RKSLStudiosAttachmentsv302;@3CBBAFEquipment;@3CBBAFUnits;@3CBBAFUnitsACEcompatibility;@3CBBAFUnitsRHScompatibility;@3CBBAFVehicles;@3CBBAFVehiclesRHSreskins;@3CBBAFVehiclesServicingextension;@3CBBAFWeapons;@3CBBAFWeaponsRHSammocompatibility;@EnhancedMovement;@ZeusEnhanced;@ZeusEnhancedACE3Compatibility;@VETUnflipping;@GruppeAdlerTrenches;@TembelanIsland" -profiles=ARMAHOSTS -config=ARMAHOSTS\server\server.cfg -cfg=ARMAHOSTS\server\basic.cfg "-name=armahosts" -Server -O=2 -H=2

Original output filename: Arma3Retail_Server_x64
Exe timestamp: 2021/09/30 12:39:26
Current time:  2021/11/05 17:37:16

Type: Public
Build: Stable
Version: 2.06.148221

Allocator: C:\TCAFiles\Users\Antistasi\2433\Dll\tbb4malloc_bi_x64.dll [2017.0.0.0] [2017.0.0.0]
PhysMem: 128 GiB, VirtMem : 131072 GiB, AvailPhys : 115 GiB, AvailVirt : 131068 GiB, AvailPage : 129 GiB, PageSize : 4.0 KiB/2.0 MiB/HasLockMemory
=====================================================================
"""

test_parse_header_lines_parameter.append((parse_header_lines_file_1, parse_header_lines_expected_1))


@pytest.mark.parametrize("log_file, expected", test_parse_header_lines_parameter, ids=[i[0].stem for i in test_parse_header_lines_parameter])
def test_parse_header_lines(fake_parsing_context_class, log_file, expected):
    parser = Parser(database=None, regex_keeper=SimpleRegexKeeper())
    with fake_parsing_context_class(log_file=log_file) as context:
        result = parser._parse_header_text(context)
        assert '\n'.join(i.content for i in result if i.content) == '\n'.join(x for x in expected.splitlines() if x)


PARSE_STARTUP_ENTRIES_TEST_FILE_DIR = THIS_FILE_DIR.joinpath("parameter_files", "parse_startup_entries_parameter_files")

test_parse_startup_entries_test_parameter = []

parse_startup_entries_file_1 = PARSE_STARTUP_ENTRIES_TEST_FILE_DIR.joinpath("simple_parse_startup_lines_1.txt")
parse_startup_entries_expected_1 = [RecordLine(r"""11:59:57 SteamAPI initialization failed. Steam features won't be accessible!""", 1),
                                    RecordLine(r"""11:59:58 Initializing stats manager.""", 2),
                                    RecordLine(r"""11:59:58 Stats config disabled.""", 3),
                                    RecordLine(r"""11:59:58 sessionID: 1e0073fd0516f42cfe685085423755bd247568c7""", 4),
                                    RecordLine(r"""12:00:05 Unsupported language English in stringtable""", 5),
                                    RecordLine(r"""12:00:05  ➥ Context: vet\unflipping\stringtable.xml""", 6),
                                    RecordLine(r"""12:00:05 Unsupported language English in stringtable""", 7),
                                    RecordLine(r"""12:00:05  ➥ Context: z\tfar\addons\core\stringtable.xml""", 8),
                                    RecordLine(r"""12:00:06 Unsupported language English in stringtable""", 9),
                                    RecordLine(r"""12:00:06  ➥ Context: rhsafrf\addons\rhs_main\stringtable.xml""", 10),
                                    RecordLine(r"""12:00:10 Updating base class RscShortcutButton->RscButton, by a3\editor_f\config.bin/RscDisplayEditObject/Controls/B_OK/ (original bin\config.bin)""", 11),
                                    RecordLine(r"""12:00:10 Updating base class RscSliderH->RscXSliderH, by a3\editor_f\config.bin/RscDisplayEditObject/Slider/ (original bin\config.bin)""", 12),
                                    RecordLine(r"""12:00:10 Updating base class RscText->RscPicture, by a3\editor_f\config.bin/RscDisplayEditObject/Preview/ (original bin\config.bin)""", 13),
                                    RecordLine(r"""12:00:10 Updating base class RscShortcutButton->RscButton, by a3\editor_f\config.bin/RscDisplayMissionLoad/Controls/B_OK/ (original bin\config.bin)""", 14),
                                    RecordLine(r"""12:00:10 Updating base class RscShortcutButton->RscButton, by a3\editor_f\config.bin/RscDisplayMissionSave/Controls/B_OK/ (original bin\config.bin)""", 15),
                                    RecordLine(r"""12:00:10 Updating base class ->RscControlsGroup, by a3\ui_f\config.bin/RscControlsGroupNoScrollbars/ (original a3\ui_f\config.bin)""", 16),
                                    RecordLine(r"""12:00:10 Updating base class ->RscControlsGroup, by a3\ui_f\config.bin/RscControlsGroupNoHScrollbars/ (original a3\ui_f\config.bin)""", 17),
                                    RecordLine(r"""12:00:10 Updating base class ->RscControlsGroup, by a3\ui_f\config.bin/RscControlsGroupNoVScrollbars/ (original a3\ui_f\config.bin)""", 18),
                                    RecordLine(r"""12:00:10 Updating base class ->RscText, by a3\ui_f\config.bin/RscLine/ (original a3\ui_f\config.bin)""", 19),
                                    RecordLine(r"""12:00:10 Updating base class ->RscActiveText, by a3\ui_f\config.bin/RscActivePicture/ (original a3\ui_f\config.bin)""", 20),
                                    RecordLine(r"""12:00:10 Updating base class ->RscButton, by a3\ui_f\config.bin/RscButtonTextOnly/ (original a3\ui_f\config.bin)""", 21),
                                    RecordLine(r"""12:00:10 Updating base class ->RscShortcutButton, by a3\ui_f\config.bin/RscShortcutButtonMain/ (original a3\ui_f\config.bin)""", 22),
                                    RecordLine(r"""12:00:10 Updating base class ->RscShortcutButton, by a3\ui_f\config.bin/RscButtonEditor/ (original a3\ui_f\config.bin)""", 23),
                                    RecordLine(r"""12:00:10 Updating base class ->RscShortcutButton, by a3\ui_f\config.bin/RscIGUIShortcutButton/ (original a3\ui_f\config.bin)""", 24),
                                    RecordLine(r"""12:00:10 Updating base class ->RscShortcutButton, by a3\ui_f\config.bin/RscGearShortcutButton/ (original a3\ui_f\config.bin)""", 25),
                                    RecordLine(r"""12:00:10 Updating base class ->RscShortcutButton, by a3\ui_f\config.bin/RscButtonMenu/ (original a3\ui_f\config.bin)""", 26),
                                    RecordLine(r"""12:00:10 Updating base class ->RscButtonMenu, by a3\ui_f\config.bin/RscButtonMenuOK/ (original a3\ui_f\config.bin)""", 27)]

test_parse_startup_entries_test_parameter.append((parse_startup_entries_file_1, parse_startup_entries_expected_1))


@pytest.mark.parametrize("log_file, expected", test_parse_startup_entries_test_parameter, ids=[i[0].stem for i in test_parse_startup_entries_test_parameter])
def test_parse_startup_entries(fake_parsing_context_class, log_file, expected):
    parser = Parser(database=None, regex_keeper=SimpleRegexKeeper())
    with fake_parsing_context_class(log_file=log_file) as context:
        result = parser._parse_startup_entries(context=context)
    for idx, i in enumerate(result):
        assert i.content == expected[idx].content
        assert i.start == expected[idx].start
    assert '\n'.join(item.content for item in result if item.content) == '\n'.join(other.content for other in expected if other.content)


ALL_LOG_FILES_DIR = THIS_FILE_DIR.parent.joinpath("data", "fake_log_files")

test_get_log_file_meta_data_params = []


class MetaDataTestParam:

    def __init__(self, log_file: Path) -> None:
        self.log_file = log_file
        self.game_map_expected: str = None
        self.full_datetime_expected: tuple[datetime, datetime] = None
        self.version_expected: Version = None
        self.mods_expected: list[ModItem] = []

    def add_mod_item(self, mod_item: Union[Mapping[str, str], ModItem, str]) -> None:
        if isinstance(mod_item, Mapping):
            mod_item = ModItem(**mod_item)
        elif isinstance(mod_item, str):
            mod_item = ModItem.from_text_line(mod_item)
        self.mods_expected.append(mod_item)

    def add_version(self, version: Union[str, Version]) -> None:
        if isinstance(version, str):
            version = Version.from_string(version)
        self.version_expected = version

    def add_full_datetime(self, full_datetime: Union[str, tuple[datetime, datetime]]) -> None:
        if isinstance(full_datetime, str):
            local_str, utc_str = full_datetime.split("|")
            rest, msec = utc_str.rsplit(':', 1)
            utc_datetime = datetime.strptime(rest, "%Y-%m-%d %H:%M:%S").replace(tzinfo=UTC, microsecond=int(msec))
            local_datetime = datetime.strptime(local_str, "%Y/%m/%d, %H:%M:%S").replace(tzinfo=UTC)
            full_datetime = (utc_datetime, local_datetime)
        self.full_datetime_expected = full_datetime

    def to_params(self) -> tuple:
        return (self.log_file, self.game_map_expected, self.full_datetime_expected, self.version_expected, self.mods_expected)


first_meta_data_test_param = MetaDataTestParam(ALL_LOG_FILES_DIR.joinpath("Mainserver_1", "arma3server_x64_2021-10-20_22-12-41.txt"))
first_meta_data_test_param.game_map_expected = "Altis"
first_meta_data_test_param.add_version(Version(2, 5, 3))
first_meta_data_test_param.add_full_datetime("2021/10/20, 22:14:58|2021-10-21 05:14:58:205")

mod_text_1 = r"""
Gruppe Adler Trenches | @GruppeAdlerTrenches |      false |      false |             GAME DIR | d0a3bf6a880bb83815a7ea1919a99de8892c69eb |  c7298f40 | C:\TCAFiles\Users\Antistasi\2433\@GruppeAdlerTrenches
VET_Unflipping - 1.3.2 |       @VETUnflipping |      false |      false |             GAME DIR | b87f16fa85a76c4522fe0fe67521f1ab4a7a7fb0 |  dc68cef1 | C:\TCAFiles\Users\Antistasi\2433\@VETUnflipping
@ZeusEnhancedACE3Compatibility | @ZeusEnhancedACE3Compatibility |      false |      false |             GAME DIR | d96ddd93715b4bb78e1ee90d61829b63a5da21bd |  41cbf8d5 | C:\TCAFiles\Users\Antistasi\2433\@ZeusEnhancedACE3Compatibility
Zeus Enhanced 1.12.1 |        @ZeusEnhanced |      false |      false |             GAME DIR | 44f84db4b41a5dd4569fd26166c5fc983afab1c2 |  9b635689 | C:\TCAFiles\Users\Antistasi\2433\@ZeusEnhanced
TFAR | @TaskForceArrowheadRadioBETA |      false |      false |             GAME DIR | 6e889b7a92591e469d9e037aa3631fb8e5a954fc |  d11c0c7f | C:\TCAFiles\Users\Antistasi\2433\@TaskForceArrowheadRadioBETA
RHS: United States Forces |             @RHSUSAF |      false |      false |             GAME DIR | 22dc683ee7645369b375f5d3a2db51a995658245 |  736ca0ba | C:\TCAFiles\Users\Antistasi\2433\@RHSUSAF
RHS: GREF |             @RHSGREF |      false |      false |             GAME DIR | d45628bb1168a22a9554c18f8c1458615546af9a |  44ebb00b | C:\TCAFiles\Users\Antistasi\2433\@RHSGREF
RHS: Armed Forces of the Russian Federation |             @RHSAFRF |      false |      false |             GAME DIR | c099f9533a1d61a33bef449594ec01c28661aa62 |  9f03db96 | C:\TCAFiles\Users\Antistasi\2433\@RHSAFRF
Enhanced Movement |    @EnhancedMovement |      false |      false |             GAME DIR | fbc1f582c89f11919f9c6ead5d842e6c1aea9b71 |  a47fddc8 | C:\TCAFiles\Users\Antistasi\2433\@EnhancedMovement
Community Base Addons v3.15.6 |               @CBAA3 |      false |      false |             GAME DIR | 00127cc3983804656fcdb4021c85a778b920cb3d |  5ca1ed2c | C:\TCAFiles\Users\Antistasi\2433\@CBAA3
@ACECompatRHSUnitedStatesArmedForces | @ACECompatRHSUnitedStatesArmedForces |      false |      false |             GAME DIR | e9ffe22d163157f20dd010fbf2e0b668dee2b55e |  3c458b15 | C:\TCAFiles\Users\Antistasi\2433\@ACECompatRHSUnitedStatesArmedForces
@ACECompatRHSGREF |    @ACECompatRHSGREF |      false |      false |             GAME DIR | c1f1b24b8fc49a37e649a0fc0f244a2ed945ba85 |  aaef152e | C:\TCAFiles\Users\Antistasi\2433\@ACECompatRHSGREF
@ACECompatRHSArmedForcesoftheRussianFederation | @ACECompatRHSArmedForcesoftheRussianFederation |      false |      false |             GAME DIR | b772e7740c2a0359bee19f99bae352054e04eb00 |  939ccfe5 | C:\TCAFiles\Users\Antistasi\2433\@ACECompatRHSArmedForcesoftheRussianFederation
Advanced Combat Environment 3.13.6 |                 @ace |      false |      false |             GAME DIR | e90e04c6168e82c0a3818ee733b3a25d36fa5d1f |  4919db26 | C:\TCAFiles\Users\Antistasi\2433\@ace
Arma 3 Art of War |                  aow |       true |       true |             GAME DIR | 0d4d518854024cf5824af507af9e16c050f38936 |   bb26feb | C:\TCAFiles\Users\Antistasi\2433\aow
Arma 3 Contact (Platform) |                enoch |       true |       true |             GAME DIR | 4cd4bf722e1a360ab4199316041aad8a3b1afbe5 |   c3ba4c1 | C:\TCAFiles\Users\Antistasi\2433\enoch
Arma 3 Tanks |                 tank |       true |       true |             GAME DIR | 9adf766a3291df59d96561ef5bbac024cd5f103c |  6b26ff75 | C:\TCAFiles\Users\Antistasi\2433\tank
Arma 3 Tac-Ops |               tacops |       true |       true |             GAME DIR | b2aeee6afb4d22a907356a94f5db210e5207741b |  8646e5fd | C:\TCAFiles\Users\Antistasi\2433\tacops
Arma 3 Laws of War |               orange |       true |       true |             GAME DIR | 0591fa9ec992d8e862d32f574c67b54402598c63 |  630e5234 | C:\TCAFiles\Users\Antistasi\2433\orange
Arma 3 Malden |                 argo |       true |       true |             GAME DIR | f049aea19468628fb3c360a8148a3867502024f2 |  3b10ba25 | C:\TCAFiles\Users\Antistasi\2433\argo
Arma 3 Jets |                 jets |       true |       true |             GAME DIR | 959b3d22f9145707051b0c44855a7be4bc8c24ba |  456e1ae6 | C:\TCAFiles\Users\Antistasi\2433\jets
Arma 3 Apex |            expansion |       true |       true |             GAME DIR | 1f9076ab9257e5993e739ce0776c871e63d1260e |  da0e3bbd | C:\TCAFiles\Users\Antistasi\2433\expansion
Arma 3 Marksmen |                 mark |       true |       true |             GAME DIR | 6c7dbe201e28b331761baaa253af901743e5cecc |  867884be | C:\TCAFiles\Users\Antistasi\2433\mark
Arma 3 Helicopters |                 heli |       true |       true |             GAME DIR | 54fec03b56fd2cc0c3d608bd988b6be8d99c8373 |  e9bda741 | C:\TCAFiles\Users\Antistasi\2433\heli
Arma 3 Karts |                 kart |       true |       true |             GAME DIR | a5ffd00a3db67b30af623a4a4ae57e4c158e9642 |  58a5c510 | C:\TCAFiles\Users\Antistasi\2433\kart
Arma 3 Zeus |              curator |       true |       true |             GAME DIR | 7845d8b549e114fb683237da35d1677f17fd8640 |  925d03b0 | C:\TCAFiles\Users\Antistasi\2433\curator
Arma 3 |                   A3 |       true |       true |            NOT FOUND |                                          |           |
@TaskForceEnforcer |   @TaskForceEnforcer |      false |      false |             GAME DIR | da39a3ee5e6b4b0d3255bfef95601890afd80709 |  11fdd19c | C:\TCAFiles\Users\Antistasi\2433\@TaskForceEnforcer
@utility |             @utility |      false |      false |             GAME DIR | da39a3ee5e6b4b0d3255bfef95601890afd80709 |  11fdd19c | C:\TCAFiles\Users\Antistasi\2433\@utility
@members |             @members |      false |      false |             GAME DIR | da39a3ee5e6b4b0d3255bfef95601890afd80709 |  11fdd19c | C:\TCAFiles\Users\Antistasi\2433\@members
"""
for line in mod_text_1.splitlines():
    if line:
        first_meta_data_test_param.add_mod_item(line)

test_get_log_file_meta_data_params.append(first_meta_data_test_param.to_params())


@pytest.mark.parametrize("log_file, game_map_expected, full_datetime_expected, version_expected, mods_expected", test_get_log_file_meta_data_params, ids=[i[0].stem for i in test_get_log_file_meta_data_params])
def test_get_log_file_meta_data(fake_parsing_context_class, log_file: Path, game_map_expected: str, full_datetime_expected: tuple[datetime, datetime], version_expected: Version, mods_expected: list[ModItem]):
    parser = Parser(database=None, regex_keeper=SimpleRegexKeeper())
    with fake_parsing_context_class(log_file=log_file) as context:
        finder = parser._get_log_file_meta_data(context=context)
    assert finder.game_map == game_map_expected
    assert finder.full_datetime == full_datetime_expected
    assert finder.version == version_expected
    assert set(finder.mods) == set(mods_expected)
