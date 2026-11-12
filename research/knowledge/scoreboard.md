# Placar de day trade (exploração, custo base)

Gerado por `python -m lab.knowledge` a partir das listas de trades da exploração de cada hipótese. Bruto e líquido são a média por trade, em % do valor operado; edge/ano = líquido por trade x trades por ano por par. Day trade = 95% das posições fechadas em até 24h.

| id | estratégia | gráfico | day trade | trades/ano/par | hold mediano (min) | p95 (h) | bruto % | líquido % | acerto % | pares líquido>0 | pares aprovados | 2022-24 % | edge/ano/par % | status |
|---|---|---|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|---|
| H-114 | DailyNR7Breakout_H114_v1 | 15m | não | 13 | 390 | 503.5 | 45.00 | 44.57 | 1 | 8/9 | 1 | -36 | 590.6 | rejected at exploration |
| H-016 | TimeSeriesMomentum_H016_v1 | 1h | não | 14 | 5760 | 1440.0 | 10.64 | 10.26 | 38 | 3/3 | 3 | 209 | 140.1 | not approved at validation |
| H-004 | SlowTimeSeriesMomentum_H004_v1 | 1h | não | 2 | 64800 | 4146.0 | 53.08 | 52.54 | 50 | 3/3 | 0 | 155 | 114.5 | invalid: implementation deviated from ru |
| H-005 | VolatilitySqueezeBreakout_H005_v1 | 1h | não | 5 | 21660 | 1584.0 | 14.88 | 14.47 | 27 | 3/3 | 0 | 57 | 75.7 | rejected at exploration |
| H-008 | VolatilitySqueezeBreakout_H008_v1 | 1h | não | 5 | 21660 | 1584.0 | 14.88 | 14.47 | 27 | 3/3 | 3 | 57 | 75.7 | not approved at validation |
| H-009 | WeeklyBreakoutRegime_H009_v1 | 1h | não | 12 | 5880 | 453.0 | 4.88 | 4.51 | 33 | 3/3 | 3 | -3 | 53.1 | candidate at exploration |
| H-024 | DailyMaxJumpMomentum_H024_v1 | 1h | não | 6 | 20760 | 1056.0 | 8.94 | 8.56 | 47 | 3/3 | 3 | 100 | 49.7 | not approved at validation |
| H-001 | SmaTrendBaseline | 1h | não | 56 | 2400 | 119.0 | 1.20 | 0.85 | 35 | 3/3 | 0 | 13 | 47.3 | frozen reference |
| H-025 | DailyKeltnerBreakout_H025_v1 | 1h | não | 5 | 18060 | 1008.0 | 10.03 | 9.65 | 42 | 3/3 | 3 | 131 | 46.3 | not approved at validation |
| H-007 | RisingTrendBreakoutGate_H007_v1 | 1h | não | 4 | 10740 | 1099.0 | 10.95 | 10.56 | 26 | 3/3 | 0 | -8 | 41.4 | rejected at exploration |
| H-017 | WeeklyBreakoutRegime_H017_v1 | 1h | não | 9 | 6240 | 440.0 | 4.85 | 4.48 | 33 | 3/3 | 2 | -0 | 41.4 | rejected at exploration |
| H-046 | LivermorePivotFailFast_H046_v1 | 1h | não | 20 | 1560 | 311.0 | 2.12 | 1.77 | 24 | 3/3 | 3 | 78 | 35.7 | not approved at validation |
| H-047 | RelativeStrengthRatioRotation_H047_v1 | 1h | não | 31 | 1440 | 87.0 | 1.18 | 0.83 | 41 | 3/3 | 3 | 65 | 26.1 | not approved at validation |
| H-044 | HeikinAshi4hFlip_H044_v1 | 1h | não | 63 | 960 | 48.0 | 0.66 | 0.31 | 32 | 3/3 | 0 | 31 | 19.2 | rejected at exploration |
| H-040 | DailyNR7Breakout_H040_v1 | 1h | não | 13 | 2880 | 48.0 | 1.68 | 1.33 | 40 | 3/3 | 3 | -10 | 17.2 | not approved at validation |
| H-002 | DonchianBreakoutBaseline | 1h | não | 119 | 1320 | 74.0 | 0.49 | 0.13 | 33 | 2/3 | 0 | -260 | 16.0 | rejected at exploration |
| H-045 | HourlySwingStructureBreak_H045_v1 | 1h | não | 53 | 1680 | 115.0 | 0.65 | 0.30 | 35 | 3/3 | 2 | -42 | 15.8 | rejected at exploration |
| H-049 | FourHourKAMATrend_H049_v1 | 1h | não | 63 | 1920 | 124.0 | 0.60 | 0.25 | 33 | 3/3 | 2 | -110 | 15.7 | rejected at exploration |
| H-104 | HourlyWilliamsVolBreakoutRVol_H104_v1 | 1h | sim | 28 | 600 | 21.0 | 0.69 | 0.38 | 47 | 8/9 | 5 | -292 | 10.6 | rejected at exploration |
| H-057 | AbnormalDayContinuation_H057_v1 | 1h | sim | 75 | 1440 | 24.0 | 0.44 | 0.14 | 45 | 2/3 | 1 | -27 | 10.5 | rejected at exploration |
| H-020 | Double7ChannelDip_H020_v1 | 1h | não | 10 | 11520 | 528.0 | 1.33 | 0.98 | 66 | 3/3 | 3 | 78 | 9.3 | not approved at validation |
| H-043 | HourlyWilliamsVolBreakout_H043_v1 | 1h | sim | 38 | 660 | 21.0 | 0.54 | 0.24 | 46 | 7/9 | 6 | -367 | 9.1 | not approved at validation |
| H-100 | RSIOverboughtMomentumRVol_H100_v1 | 1h | sim | 50 | 540 | 23.0 | 0.44 | 0.14 | 43 | 6/9 | 4 | -243 | 7.1 | rejected at exploration |
| H-101 | HourlyIchimokuTrendRVol_H101_v1 | 1h | sim | 21 | 1380 | 24.0 | 0.63 | 0.33 | 39 | 7/9 | 4 | 29 | 7.1 | rejected at exploration |
| H-035 | HourlyRangeExpansionDrift_H035_v1 | 1h | sim | 18 | 1440 | 24.0 | 0.67 | 0.32 | 48 | 3/3 | 1 | 41 | 5.6 | rejected at exploration |
| H-019 | DailyRSI2Dip_H019_v1 | 1h | não | 8 | 4320 | 168.0 | 0.89 | 0.54 | 68 | 3/3 | 2 | 41 | 4.2 | rejected at exploration |
| H-085 | RSIOverboughtMomentum_H085_v1 | 1h | sim | 81 | 540 | 23.0 | 0.35 | 0.05 | 41 | 6/9 | 3 | -348 | 3.7 | rejected at exploration |
| H-103 | AbnormalDayContinuationRVol_H103_v1 | 1h | sim | 42 | 1440 | 24.0 | 0.39 | 0.09 | 41 | 5/9 | 3 | -255 | 3.7 | rejected at exploration |
| H-102 | IntradayJumpContinuationStrong_H102_v1 | 15m | sim | 14 | 540 | 22.8 | 0.57 | 0.27 | 42 | 7/9 | 5 | -93 | 3.6 | rejected at exploration |
| H-059 | IntradayJumpContinuation_H059_v1 | 15m | sim | 41 | 495 | 22.8 | 0.35 | 0.05 | 38 | 5/9 | 2 | -372 | 2.0 | rejected at exploration |
| H-003 | BollingerMeanReversionBaseline | 1h | não | 9 | 900 | 29.0 | 0.43 | 0.08 | 60 | 1/3 | 0 | -19 | 0.7 | rejected at exploration |
| H-084 | HourlyIchimokuTrend_H084_v1 | 1h | sim | 79 | 1080 | 24.0 | 0.31 | 0.00 | 34 | 4/9 | 1 | -340 | 0.4 | rejected at exploration |
| H-073 | BreadthThrustIntraday_H073_v1 | 1h | sim | 135 | 780 | 24.0 | 0.29 | -0.01 | 34 | 2/9 | 0 | -684 | -1.0 | rejected at exploration |
| H-051 | HighVolumeSessionMomentum_H051_v1 | 1h | sim | 10 | 420 | 7.0 | 0.11 | -0.19 | 38 | 0/3 | 0 | -9 | -1.9 | rejected at exploration |
| H-036 | USOpenVolumeContinuation_H036_v1 | 1h | sim | 8 | 240 | 4.0 | 0.10 | -0.25 | 31 | 1/3 | 0 | -14 | -2.1 | rejected at exploration |
| H-041 | WeeklyAnchoredVWAPReclaim_H041_v1 | 1h | não | 34 | 720 | 48.0 | 0.23 | -0.12 | 28 | 1/3 | 0 | -121 | -4.1 | rejected at exploration |
| H-063 | VarianceRatioRegimeBreakout_H063_v1 | 15m | sim | 13 | 465 | 24.0 | -0.04 | -0.34 | 29 | 3/9 | 0 | -108 | -4.4 | rejected at exploration |
| H-078 | CrossSectionalLowVolReversal_H078_v1 | 1h | sim | 19 | 480 | 12.0 | 0.03 | -0.27 | 47 | 2/9 | 1 | -42 | -5.1 | rejected at exploration |
| H-074 | FeedbackVolRegimeSwitch_H074_v1 | 1h | sim | 54 | 780 | 13.0 | 0.19 | -0.11 | 42 | 3/9 | 0 | -255 | -5.7 | rejected at exploration |
| H-010 | UptrendPullbackRecovery_H010_v1 | 1h | não | 26 | 2760 | 261.0 | 0.11 | -0.24 | 37 | 0/3 | 0 | -115 | -6.2 | rejected at exploration |
| H-055 | HourlyFailedBreakdownReclaim_H055_v1 | 15m | sim | 27 | 165 | 12.0 | 0.05 | -0.24 | 55 | 0/3 | 0 | -24 | -6.5 | rejected at exploration |
| H-121 | HighOfDayRVolBreak_H121_v1 | 15m | sim | 24 | 30 | 8.0 | 0.01 | -0.29 | 26 | 0/9 | 0 | -153 | -6.7 | rejected at exploration |
| H-075 | HourlyBullFlagBreak_H075_v1 | 1h | sim | 19 | 360 | 24.0 | -0.09 | -0.39 | 48 | 0/9 | 0 | -124 | -7.2 | rejected at exploration |
| H-038 | HourlyFailedBreakdownReclaim_H038_v1 | 1h | não | 7 | 900 | 48.0 | -0.83 | -1.18 | 31 | 0/3 | 0 | -43 | -7.7 | rejected at exploration |
| H-012 | EMASnapbackATR_H012_v1 | 1h | sim | 18 | 360 | 17.0 | -0.12 | -0.47 | 55 | 0/3 | 0 | -69 | -8.2 | rejected at exploration |
| H-072 | IdiosyncraticResidualReversal_H072_v1 | 1h | sim | 15 | 600 | 12.0 | -0.29 | -0.59 | 42 | 0/9 | 0 | -205 | -9.0 | rejected at exploration |
| H-039 | WeekendDaytimeSession_H039_v1 | 1h | sim | 53 | 480 | 8.0 | 0.18 | -0.17 | 39 | 0/3 | 0 | -126 | -9.2 | rejected at exploration |
| H-080 | CrossPairCatchUp_H080_v1 | 15m | sim | 54 | 165 | 4.0 | 0.12 | -0.18 | 49 | 0/9 | 0 | -153 | -9.5 | rejected at exploration |
| H-097 | RSIBullDivergence_H097_v1 | 15m | sim | 31 | 420 | 12.0 | -0.05 | -0.35 | 39 | 0/9 | 0 | -269 | -10.9 | rejected at exploration |
| H-033 | HourlyShockOverreaction_H033_v1 | 1h | sim | 25 | 840 | 24.0 | -0.09 | -0.44 | 47 | 0/3 | 0 | -19 | -11.0 | rejected at exploration |
| H-092 | SessionOpeningRangeBreakout_H092_v1 | 15m | sim | 20 | 135 | 5.8 | -0.28 | -0.58 | 30 | 0/9 | 0 | -298 | -11.6 | rejected at exploration |
| H-094 | HolyGrailADXPullback_H094_v1 | 15m | sim | 69 | 300 | 8.0 | 0.08 | -0.22 | 34 | 0/2 | 0 | -106 | -15.0 | failed: exploration |
| H-030 | OvernightDropReversal_H030_v1 | 1h | sim | 34 | 480 | 8.0 | -0.10 | -0.45 | 39 | 0/3 | 0 | -94 | -15.3 | rejected at exploration |
| H-050 | VolumeConditionedReversal_H050_v1 | 15m | sim | 32 | 480 | 12.0 | -0.19 | -0.49 | 40 | 0/3 | 0 | -82 | -15.5 | rejected at exploration |
| H-110 | InverseFVGReclaim_H110_v1 | 15m | sim | 91 | 330 | 12.0 | 0.11 | -0.19 | 40 | 0/9 | 0 | -340 | -17.4 | rejected at exploration |
| H-053 | VolumeConditionedReversal_H053_v1 | 1h | sim | 42 | 720 | 12.0 | -0.12 | -0.42 | 46 | 0/3 | 0 | -66 | -17.6 | rejected at exploration |
| H-120 | ADRExhaustionReversal_H120_v1 | 15m | sim | 52 | 225 | 12.0 | -0.04 | -0.34 | 43 | 1/9 | 1 | -327 | -17.8 | rejected at exploration |
| H-065 | ADXRegimeSwitch_H065_v1 | 1h | sim | 26 | 780 | 24.0 | -0.41 | -0.71 | 35 | 0/9 | 0 | -356 | -18.6 | rejected at exploration |
| H-089 | WeeklyBreakoutRegime_H089_v1 | 1h | sim | 88 | 420 | 12.0 | 0.08 | -0.22 | 31 | 0/5 | 0 | -366 | -19.6 | failed: exploration |
| H-108 | LivermorePivotFailFast_H108_v1 | 1h | sim | 91 | 360 | 12.0 | 0.08 | -0.22 | 30 | 0/9 | 0 | -749 | -20.1 | rejected at exploration |
| H-091 | DailyRSI2Dip_H091_v1 | 1h | sim | 90 | 240 | 10.0 | 0.06 | -0.24 | 50 | 0/9 | 0 | -386 | -21.3 | rejected at exploration |
| H-093 | TDSetupExhaustion_H093_v1 | 15m | sim | 76 | 195 | 8.0 | -0.04 | -0.34 | 37 | 0/9 | 0 | -496 | -25.9 | rejected at exploration |
| H-115 | SMTDivergenceSweep_H115_v1 | 15m | sim | 116 | 375 | 12.0 | 0.07 | -0.23 | 38 | 0/9 | 0 | -868 | -26.3 | rejected at exploration |
| H-123 | MomentumPinballSession_H123_v1 | 15m | sim | 83 | 135 | 12.0 | -0.02 | -0.32 | 37 | 0/4 | 0 | -152 | -26.8 | implemented |
| H-064 | SameSlotPeriodicity_H064_v1 | 1h | sim | 126 | 240 | 4.0 | 0.06 | -0.24 | 42 | 0/9 | 0 | -565 | -30.0 | rejected at exploration |
| H-116 | PocketPivotVolume_H116_v1 | 1h | sim | 110 | 300 | 12.0 | 0.01 | -0.29 | 32 | 0/9 | 0 | -1052 | -31.5 | rejected at exploration |
| H-113 | CrossSectionalAttentionVolume_H113_v1 | 1h | sim | 96 | 60 | 6.0 | -0.05 | -0.34 | 25 | 0/9 | 0 | -680 | -33.2 | rejected at exploration |
| H-060 | SameSlotPeriodicity_H060_v1 | 1h | sim | 144 | 240 | 4.0 | 0.05 | -0.25 | 42 | 0/9 | 0 | -728 | -36.6 | rejected at exploration |
| H-061 | DailyPivotS1Reclaim_H061_v1 | 15m | sim | 112 | 180 | 15.5 | -0.04 | -0.34 | 34 | 0/9 | 0 | -658 | -37.6 | rejected at exploration |
| H-069 | SessionOpeningRangeBreakout_H069_v1 | 15m | sim | 152 | 240 | 6.0 | 0.05 | -0.25 | 35 | 0/9 | 0 | -762 | -38.0 | rejected at exploration |
| H-068 | SeasonalVolumeSurprise_H068_v1 | 1h | sim | 150 | 360 | 12.0 | 0.04 | -0.26 | 30 | 1/9 | 0 | -669 | -39.3 | rejected at exploration |
| H-062 | VolumeSpikeCrashRebound_H062_v1 | 15m | sim | 144 | 135 | 4.0 | -0.01 | -0.31 | 45 | 0/9 | 0 | -752 | -44.5 | rejected at exploration |
| H-052 | IntradayNoiseAreaMomentum_H052_v1 | 1h | sim | 174 | 120 | 17.0 | 0.04 | -0.26 | 21 | 0/9 | 0 | -1179 | -45.7 | rejected at exploration |
| H-058 | USSessionOvernightHold_H058_v1 | 1h | sim | 150 | 1020 | 17.0 | -0.01 | -0.31 | 40 | 0/9 | 0 | -1331 | -45.9 | rejected at exploration |
| H-096 | SessionRangeJudasSweep_H096_v1 | 15m | sim | 142 | 210 | 7.0 | -0.03 | -0.33 | 34 | 0/9 | 0 | -1056 | -47.3 | rejected at exploration |
| H-106 | Double7ChannelDip_H106_v1 | 1h | sim | 169 | 360 | 12.0 | 0.01 | -0.29 | 41 | 0/9 | 0 | -1111 | -48.4 | rejected at exploration |
| H-118 | OrderBlockRetest_H118_v1 | 15m | sim | 172 | 135 | 12.0 | 0.02 | -0.28 | 31 | 0/9 | 0 | -976 | -48.5 | rejected at exploration |
| H-098 | HourlyFailedBreakdownReclaim_H098_v1 | 15m | sim | 168 | 285 | 12.0 | -0.01 | -0.31 | 36 | 0/4 | 0 | -465 | -51.6 | failed: implementation |
| H-087 | IntradayReturnAcceleration_H087_v1 | 15m | sim | 143 | 150 | 4.2 | -0.10 | -0.40 | 32 | 0/9 | 0 | -946 | -57.0 | rejected at exploration |
| H-117 | FairValueGapRetest_H117_v1 | 15m | sim | 201 | 135 | 12.0 | -0.01 | -0.30 | 30 | 0/9 | 0 | -1367 | -61.3 | rejected at exploration |
