from antistasi_logbook.parsing.parser import Parser, SimpleRegexKeeper, RawRecord, RecordLine

_0 = RawRecord([RecordLine(content='2021/10/05, 08:40:59 [CBA] (xeh) INFO: [12189,153.042,0] PreInit finished.', start=1)])


_1 = RawRecord([RecordLine(content='2021/10/05, 08:40:59 "armahosts/BIS_fnc_log: [preInit] CBA_fnc_preInit (707.001 ms)"', start=2)])


_2 = RawRecord([RecordLine(content='2021/10/05, 08:40:59 "armahosts/BIS_fnc_log: [preInit] HR_GRG_fnc_initServer (1.00708 ms)"', start=3)])


_3 = RawRecord([RecordLine(content='2021/10/05, 08:40:59 PortableHelipadLight_01_white_F: light_1_blinking - unknown animation source MarkerLight (defined in AnimationSources::Light_1_source)', start=4)])


_4 = RawRecord([RecordLine(content='2021/11/06, 02:42:58 2021-11-06 09:42:58:958 | Antistasi | Debug | File: fn_initServer.sqf | Land_New_WiredFence_10m_F killed by UNKNOWN', start=5)])


_5 = RawRecord([RecordLine(content="2021/11/06, 02:43:03 Can't change owner from 0 to 2", start=6)])


_6 = RawRecord([RecordLine(content='2021/11/06, 02:42:58 2021-11-06 09:42:58:997 | Antistasi | Debug | File: fn_initServer.sqf |  killed by UNKNOWN', start=7)])


_7 = RawRecord([RecordLine(content='2021/11/08, 10:26:07 2021-11-08 18:26:07:393 | Antistasi | Debug | File: A3A_fnc_createAttackVehicle | Spawn Performed: Created vehicle UK3CB_BAF_Merlin_HC3_18_GPMG_DPMT_RM with 12 soldiers | Called By: A3A_fnc_SUP_QRF', start=8)])


_8 = RawRecord([RecordLine(content='2021/11/08, 08:26:14 Error in expression <gress", 0];', start=9),
                RecordLine(content='_progress = _progress - (1 / (((_decayTimeMax - (_decayTimeMax - _d>', start=10)])


_9 = RawRecord([RecordLine(content='2021/11/08, 08:22:19 2021-11-08 16:22:19:760 | Antistasi | Info | File: A3A_fnc_saveLoop | Starting persistent save', start=11)])


_10 = RawRecord([RecordLine(content='2021/11/08, 06:02:43 2021-11-08 14:02:43:868 | Antistasi | Info | File: A3A_fnc_savePlayer | Saved player 76561198321187728: PRIVATE rank 100 money  vehicles | Called By: A3A_fnc_onPlayerDisconnect', start=12)])


_11 = RawRecord([RecordLine(content='2021/11/08, 06:02:46 Warning: Cleanup player - person 115:12 not found', start=13)])


_12 = RawRecord([RecordLine(content='2021/11/08, 06:02:46 2021-11-08 14:02:46:359 | Antistasi | Debug | File: A3A_fnc_supportAvailable | Support check for QRF returns 0 array is [] | Called By: A3A_fnc_sendSupport', start=14)])


_13 = RawRecord([RecordLine(content='2021/11/08, 06:02:46 2021-11-08 14:02:46:359 | Antistasi | Info | File: A3A_fnc_sendSupport | Sending support type QRF to help at [9200.05,6126.25,0]', start=15)])


_14 = RawRecord([RecordLine(content='2021/11/08, 06:02:46 2021-11-08 14:02:46:379 | Antistasi | Debug | File: A3A_fnc_createSupport | New support name will be QRF0', start=16)])


_15 = RawRecord([RecordLine(content='2021/11/08, 06:02:46 2021-11-08 14:02:46:382 | Antistasi | Debug | File: A3A_fnc_findSpawnPosition | Result is [[9237.49,4874.04,0.1],0] | Called By: A3A_fnc_findBaseForQRF', start=17)])


_16 = RawRecord([RecordLine(content='2021/11/08, 06:02:46 2021-11-08 14:02:46:400 | Antistasi | Debug | File: A3A_fnc_freeSpawnPositions | Spawn places for airport [', start=18),
                RecordLine(content='>>> [[[[9312.57,4879.49,0.1],0],false],[[[9317.92,4879.49,0.1],0],false],[[[9323.27,4879.49,0.1],0],false],[[[9328.62,4879.49,0.1],0],false],[[[9333.97,4879.49,0.1],0],false],[[[9232.14,4874.04,0.1],0],false],[[[9237.49,4874.04,0.1],0],true],[[[9242.83,4874.04,0.1],0],false],[[[9248.18,4874.04,0.1],0],false],[[[9253.53,4874.04,0.1],0],false]]', start=19),
                RecordLine(content='>>> [[[[9199.5,4872.5,0.4],0],false],[[[9174.5,4872.5,0.4],0],false]]', start=20),
                RecordLine(content='>>> [[[[9354.78,4858.85,0.1],270],false],[[[9354.77,4821.33,0.350112],270],false],[[[9354.75,4783.82,0.834962],270],false]]', start=21),
                RecordLine(content='>>> [[[[9355.79,4802.36,0.1],0],false],[[[9179.59,4776.29,0.1],0],false]]', start=22),
                RecordLine(content='>>> ] | Called By: A3A_fnc_findBaseForQRF', start=23)])


_17 = RawRecord([RecordLine(content='2021/11/08, 06:02:46 2021-11-08 14:02:46:400 | Antistasi | Debug | File: A3A_fnc_findSpawnPosition | Result is [[9255.55,5118.35,0.1],359.565] | Called By: A3A_fnc_findBaseForQRF', start=24)])


_18 = RawRecord([RecordLine(content='2021/11/08, 06:02:46 2021-11-08 14:02:46:402 | Antistasi | Debug | File: A3A_fnc_freeSpawnPositions | Spawn places for outpost_9 [', start=25),
                RecordLine(content='>>> [[[[9250.17,5118.31,0.1],359.565],false],[[[9255.55,5118.35,0.1],359.565],true],[[[9260.92,5118.39,0.1],359.565],false],[[[9266.29,5118.43,0.1],359.565],false],[[[9271.66,5118.47,0.1],359.565],false],[[[9277.03,5118.51,0.1],359.565],false],[[[9282.4,5118.55,0.1],359.565],false]]', start=26),
                RecordLine(content='>>> [[[[9269.75,5152.01,0.4],1.00179e-005],false]]', start=27),
                RecordLine(content='>>> []', start=28),
                RecordLine(content='>>> []', start=29),
                RecordLine(content='>>> ] | Called By: A3A_fnc_findBaseForQRF', start=30)])


all_records = [_0,
               _1,
               _2,
               _3,
               _4,
               _5,
               _6,
               _7,
               _8,
               _9,
               _10,
               _11,
               _12,
               _13,
               _14,
               _15,
               _16,
               _17,
               _18]


if __name__ == '__main__':
    pass
