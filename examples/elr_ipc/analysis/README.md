# ELR IPC DPS XML engineering analysis

## Executive finding

`XMLFile.xml` is a GM DPS ECU Configuration file for the Cadillac ELR instrument-panel cluster. It is not a Type-4 archive. DPS can use it with the ECU Configuration workflow to calculate and write IPC configuration DIDs from vehicle build/RPO data.

## Identification

| Field | Value |
|---|---|
| ECU | `IPC_Instrumentation_Panel_Cluster` |
| Diagnostic address | `60` |
| Part number | `0503DB75` |
| Alpha code | `4141` |
| Security access | `true` |
| Security table | `01` |
| Security algorithm | `37` |
| Application layer | `GMW3110` |
| Physical layer | `GMW3122` |
| Protocol description | `LScan B4 ELR` |
| Compatibility ID | `0011` |
| Physical signal | `LS Can GMLAN` |
| DLC pin | `1` |
| XML schema | `01.02.02` |
| Revision | `01.66.00` dated `2016-07-26` |

## Scope and counts

- 14 defined DIDs
- 147 configurable bit fields
- 65 build/RPO-driven value rules
- 23 recognized RPO codes
- 14 entries in the prescribed write sequence
- No read sequence is defined in `ReadSection`; it is empty.
- No model-designator rules are defined; `ModelDesignatorList` is empty.

## DID map

| DID | Bytes | Fields | Purpose | Default |
|---|---:|---:|---|---|
| `0x0002` | 32 | 16 | This DID enables or disables individual display warnings. | `FFFFFFEFDFFFFC7FFFDFFFFFFF7F7EE7C7FFFFFE7F5FD7FF5FBFFEB1F7FD7D01` |
| `0x0003` | 32 | 25 | This DID enables or disables 'Extended Set' warnings | `880007D2E9010FFA0F00CFFFE40180FCBFF1E7FFE7FFFFFFFF1FEE0000007D00` |
| `0x0090` | 17 | 0 | This DID contains the Vehicle Identification Number. It shall be write protected via security access and shall be impemented according to GMW 3110. | `0000000000000000000000000000000000` |
| `0x009C` | 4 | 0 | This DID contains the XML Data File Part Number. It shall be implemented according to GMW 3110. | `00000000` |
| `0x009D` | 2 | 0 | This DID contains the XML Data File Alpha Code. It shall be implemented according to GMW 3110. | `0000` |
| `0x00A0` | 1 | 0 | This DID shall be implemented according to the GGSE ECU Diagnostic Infrastucture document and GMW 3110. The MEC shall be supported during ECU development and production by all nodes which implement the SecurityAccess ($27) service. The MEC is a single byte in permanent (EEPROM or equivalent) memory which allows a node to remain unlocked as long as its value is not $00. When the value of the MEC becomes $00, security shall be enabled and the SecurityAccess ($27) service shall be required to access security. The MEC counter shall be decremented each time system power mode transition from System Power Mode "RUN" to either System Power Mode "ACC" or "OFF". A node shall not allow the value of the MEC to change once it becomes $00 unless SecurityAccess ($27) is successfully initiated (Security_Access_Unlocked is set to TRUE). Note: MEC should not be written to $FF value in the production ECUs. In development ECUs its allowed to write to $FF. | `FE` |
| `0x00A1` | 20 | 11 | This DID is used for enabling and disabling menues on the display. It shall be write protected via security access. | `1F11F0FFFFFF7FE05F3D210A0000000106002801` |
| `0x00A2` | 12 | 16 | This DID is used for masking DTCs/FTBs in the ECU. A bit set to zero means that the DTC/FTB is disabled. Note: If DTC is triggered and then masked in this DID the DTC status byte will not be changed. The service $04 should be sent to the IPC after an update of this DID. | `FEF70C800100000000000000` |
| `0x00A3` | 8 | 25 | This DID is used for enabling and disabling menues on the display. It shall be write protected via security access. | `3FFDF31C1C004086` |
| `0x00A4` | 11 | 13 | This DID is used for enabling and disabling functionality. It shall be write protected via security access. | `9A9A3F0120460000000000` |
| `0x00A5` | 32 | 23 | This DID is used to set functionality controls. It shall be write protected via security access. | `09B1001083D1C0106C091100000000800004000000011D00E80000F078532000` |
| `0x00A6` | 12 | 16 | This DID enables or disables Indicator. | `F3FFFFF36EEFDF00B8030000` |
| `0x00A7` | 1 | 1 | This DID is used to set the configuration flag. It indicates if the IPC configuration was done or if it needs to be configured. | `01` |
| `0x00A8` | 5 | 1 | This DID is used to set the display unit to any of the below units 0x0 UNIT_METRIC, 0x1 UNIT_US, 0x2 UNIT_IMPERIAL 0x3 reserved | `0000000000` |

## RPO inputs

| RPO | Description | Rule references |
|---|---|---:|
| `CT1` | COUNTRY-BELGIUM | 2 |
| `CT2` | COUNTRY-AUSTRIA | 2 |
| `CT3` | COUNTRY-GERMANY | 2 |
| `CT5` | COUNTRY-NETHERLANDS | 2 |
| `CT6` | COUNTRY-ITALY | 2 |
| `CT7` | COUNTRY-DENMARK | 2 |
| `CU3` | COUNTRY-FRANCE | 2 |
| `CU5` | COUNTRY-SWITZERLAND | 2 |
| `CV3` | Mexico | 2 |
| `CW1` | Korea | 7 |
| `CZ2` | COUNTRY-CHINA | 2 |
| `EF7` | COUNTRY-UNITED STATES OF AMERICA (USA) | 13 |
| `IO6` | RADIO-INFOTAINMENT SYSTEM - UPLEVEL HMI, ENHANCED CONNECTIVITY, EMBEDDED NAVIGATION | 4 |
| `KSG` | CRUISE CONTROL-AUTOMATIC, ADAPTIVE, WITH STOP/GO | 19 |
| `UE1` | ONSTAR | 3 |
| `UE4` | SENSOR INDICATOR-FOLLOWING DISTANCE | 2 |
| `UEU` | SENSOR INDICATOR-FORWARD COLLISION ALERT | 4 |
| `UFG` | SENSOR INDICATOR-REAR CROSS TRAFFIC ALERT | 2 |
| `UFQ` | PARK ASSIST-FRONT, REAR, LATERAL-FRONT (SEMIAUTOMATIC STEERING ADVANCED PARKING AID) | 4 |
| `UHX` | LANE ACTIVE SAFETY-KEEP ASSIST | 4 |
| `UKC` | SIDE ACTIVE SAFETY-OBSTACLE DETECTION ENHANCED | 8 |
| `UVX` | SENSOR INDICATOR-TRAFFIC SIGN RECOGNITION ENHANCED | 2 |
| `Z49` | COUNTRY-CANADA | 4 |

## Notable display and driver-assistance fields

The complete 147-field inventory is in `parameters.csv`. These are the fields most directly related to the display, menus, navigation, HUD, units, warnings, and driver-assistance presentation. Byte positions are reproduced exactly from the XML and should be treated as schema-defined positions, not guessed raw offsets.

| DID | Byte | Bit | Len | Parameter | Default | RPO-driven | Interpretations |
|---|---:|---:|---:|---|---|---|---|
| `0x0002` | 16 | 0 | 1 | `P_REAR_ACCESS_OPEN_ENABLE` | `00` | false | 00=Disable / 01=Enable |
| `0x0002` | 16 | 2 | 1 | `P_GAP_ALERT_SET_TO_X_ENABLE` | `01` | true | 00=Disable / 01=Enable |
| `0x0003` | 5 | 7 | 1 | `P_GAP_ALERT_SET_TO_X_ENABLE_ACC` | `00` | true | 00=Disable / 01=Enable |
| `0x0003` | 17 | 2 | 1 | `P_ENGINE_OVERHEATED_REDUCE_SPEED_ENABLE` | `01` | false | 00=Disable / 01=Enable |
| `0x0003` | 17 | 3 | 1 | `P_ENGINE_OIL_OVERHEATED_REDUCE_SPEED_ENABLE` | `01` | false | 00=Disable / 01=Enable |
| `0x0003` | 18 | 2 | 1 | `P_PTO_ACCELERATION_UPON_BRAKE_RELEASE_ENABLE` | `00` | false | 00=Disable / 01=Enable |
| `0x00A1` | 2 | 3 | 4 | `P_NG_DEFAULT_LAYOUT` | `01` | false | 00=Layout 0 / 01=Layout 1 / 02=Layout 2 / 03=Layout 3 / 04=Layout 4 / 05=Layout 5 / 06=Layout 6 / 07=Layout 7 / 08=Layout 8 / 09=Layout 9 / 0A=Layout 10 / 0B=Layout 11 / 0C=Layout 12 / 0D=Layout 13 / 0E=Layout 14 / 0F=Layout 15 |
| `0x00A1` | 2 | 4 | 1 | `P_NG_SOURCE_LIST_ENABLE_PANDORA` | `00` | false | 00=False / 01=True |
| `0x00A1` | 2 | 5 | 1 | `P_NG_SOURCE_LIST_ENABLE_INTERNET_RADIO` | `00` | false | 00=False / 01=True |
| `0x00A1` | 2 | 6 | 1 | `P_NG_NAV_APPLICATION_ENABLE` | `01` | true | 00=False / 01=True |
| `0x00A1` | 5 | 3 | 1 | `P_NG_SPEED_CURVE_MENU_DEFAULT` | `00` | false | 00=False / 01=True |
| `0x00A1` | 6 | 6 | 1 | `P_NG_TBT_MENU_DEFAULT` | `01` | true | 00=False / 01=True |
| `0x00A1` | 10 | 5 | 1 | `P_NG_MOST_HUD_PRESENT` | `00` | false | 00=False / 01=True |
| `0x00A1` | 10 | 7 | 1 | `P_HYBRID_EFF_SHOW_GOOD_STATUS_ENABLED` | `01` | false | 00=False / 01=True |
| `0x00A1` | 15 | 1 | 1 | `P_TRIP2_AFE_MENU_PRESENT` | `01` | false | 00=False / 01=True |
| `0x00A1` | 18 | 3 | 1 | `P_SPEED_SIGN_IN_SPEED_PAGE` | `00` | false | 00=False / 01=True |
| `0x00A3` | 0 | 7 | 1 | `P_SPEED_MENU_PRESENT` | `01` | false | 00=Disable / 01=Enable |
| `0x00A3` | 1 | 4 | 1 | `P_COMPASS_RECALIBRATION_MENU_PRESENT` | `00` | false | 00=Disable / 01=Enable |
| `0x00A3` | 1 | 5 | 1 | `P_COMPASS_ZONE_SELECTION_MENU_PRESENT` | `00` | false | 00=Disable / 01=Enable |
| `0x00A3` | 1 | 6 | 1 | `P_TRAILER_BRAKE_MENU_PRESENT` | `00` | false | 00=Disable / 01=Enable |
| `0x00A3` | 1 | 7 | 1 | `P_TRANSMISSIONFLUID_TEMP_MENU_PRESENT` | `00` | false | 00=Disable / 01=Enable |
| `0x00A3` | 2 | 3 | 1 | `P_DIC_SPEED_CURVE_MENU_ENABLED` | `00` | true | 00=Disable / 01=Enable |
| `0x00A3` | 2 | 4 | 1 | `P_TSM_MENU_PRESENT` | `01` | true | 00=False / 01=True |
| `0x00A3` | 2 | 5 | 1 | `P_BLANK_MENU2_PRESENT` | `00` | false | 00=Disable / 01=Enable |
| `0x00A3` | 2 | 6 | 1 | `P_DEF_RANGE_MENU_PRESENT` | `00` | false | 00=Disable / 01=Enable |
| `0x00A3` | 2 | 7 | 1 | `P_FUEL_FILTER_LIFE_MENU_PRESENT` | `00` | false | 00=Disable / 01=Enable |
| `0x00A3` | 3 | 2 | 1 | `P_OAT_MENU_PRESENT` | `00` | false | 00=False / 01=True |
| `0x00A3` | 3 | 3 | 1 | `P_JUMP_START_MENU_PRESENT` | `00` | false | 00=Disable / 01=Enable |
| `0x00A3` | 4 | 2 | 1 | `P_PERFORMANCE_TIMER_MENU_PRESENT` | `00` | false | 00=Disable / 01=Enable |
| `0x00A3` | 4 | 3 | 1 | `P_COOLANTBATTERY_MENU3_PRESENT` | `00` | false | 00=Disable / 01=Enable |
| `0x00A3` | 4 | 5 | 1 | `P_FDI_MENU_PRESENT` | `00` | true | 00=Disable / 01=Enable |
| `0x00A3` | 4 | 6 | 1 | `P_HYBRID_ELECTRIC_RANGE_MENU_PRESENT` | `01` | false | 00=Disable / 01=Enable |
| `0x00A3` | 4 | 7 | 1 | `P_TOTAL_COMBINED_VEHICLE_RANGE_MENU_PRESENT` | `01` | false | 00=Disable / 01=Enable |
| `0x00A3` | 5 | 0 | 1 | `P_HYBRID_ODOMETERS_MENU_PRESENT` | `01` | false | 00=Disable / 01=Enable |
| `0x00A3` | 5 | 1 | 1 | `P_USABLE_BATTERY_SOC_MENU_PRESENT` | `01` | false | 00=Disable / 01=Enable |
| `0x00A3` | 5 | 3 | 1 | `P_CHARGING_PEEKIN_MENU_ENABLED` | `01` | false | 00=Disable / 01=Enable |
| `0x00A3` | 6 | 3 | 1 | `P_GAP_MENU_PRESENT` | `00` | true | 00=False / 01=True |
| `0x00A3` | 7 | 1 | 1 | `P_COMPASS_DISPLAY_MENU_PRESENT` | `01` | true | 00=False / 01=True |
| `0x00A3` | 7 | 5 | 1 | `P_HYBRID_POWER_MENU_PRESENT` | `01` | false | 00=Disable / 01=Enable |
| `0x00A4` | 2 | 0 | 1 | `P_OPTION_LANE_DEPARTURE_PRESENT` | `00` | false | 00=False / 01=True |
| `0x00A4` | 4 | 6 | 1 | `P_OPTION_LANE_KEEPER_PRESENT` | `00` | true | 00=False / 01=True |
| `0x00A5` | 1 | 4 | 1 | `P_JAPANESE_DISPLAY_UNITS_ENABLED` | `00` | true | 00=Disable / 01=Enable |
| `0x00A5` | 4 | 7 | 1 | `P_UNITS_IMPERIAL_ENABLED` | `00` | true | 00=False / 01=True |
| `0x00A5` | 5 | 2 | 1 | `P_ACC_ENGAGED_INDICATOR_IN_DISPLAY` | `01` | false | 00=False / 01=True |
| `0x00A5` | 5 | 4 | 1 | `P_CRUISE_ON_INDICATION_IN_DISPLAY` | `01` | true | 00=False / 01=True |
| `0x00A5` | 5 | 5 | 1 | `P_CRUISE_ENABLED_INDICATION_IN_DISPLAY` | `00` | true | 00=False / 01=True |
| `0x00A5` | 8 | 3 | 1 | `P_UNITS_CHANGED_POPUP_ENABLED` | `00` | false | 00=False / 01=True |
| `0x00A5` | 25 | 7 | 8 | `DID_A5_P_NG_PHONE_NUMBER_DISPLAY_LAYOUT` | `00` | true |  |
| `0x00A6` | 0 | 1 | 1 | `P_DIESEL_PARTICLE_FILTER_INDICATOR_ENABLED` | `00` | false | 00=Disable / 01=Enable |
| `0x00A6` | 0 | 2 | 1 | `P_CHANGE_OIL_INDICATOR_ENABLED` | `01` | false | 00=Disable / 01=Enable |
| `0x00A6` | 0 | 3 | 1 | `P_LANE_KEEPER_ASSIST_INDICATOR_ENABLED` | `00` | true | 00=Disable / 01=Enable |
| `0x00A6` | 1 | 5 | 1 | `P_LANE_DEPARTURE_INDICATOR_ENABLED` | `00` | false | 00=Disable / 01=Enable |
| `0x00A6` | 1 | 6 | 1 | `P_DIESEL_EXHAUST_FLUID_INDICATOR_ENABLED` | `00` | false | 00=Disable / 01=Enable |
| `0x00A6` | 2 | 2 | 1 | `P_TOW_HAUL_INDICATOR_ENABLED` | `00` | false | 00=Disable / 01=Enable |
| `0x00A6` | 3 | 0 | 1 | `P_WATER_IN_FUEL_INDICATOR_ENABLED` | `00` | false | 00=Disable / 01=Enable |
| `0x00A6` | 3 | 1 | 1 | `P_CONTROVENTO_DOOR_INPUT_INDICATOR_ENABLED` | `00` | false | 00=Disable / 01=Enable |
| `0x00A6` | 3 | 5 | 1 | `P_TAILGATE_AJAR_INDICATOR_ENABLED` | `00` | false | 00=Disable / 01=Enable |
| `0x00A6` | 5 | 1 | 1 | `P_REAR_LEFT_SEAT_BELT_INDICATOR_ENABLED` | `00` | false | 00=Disable / 01=Enable |
| `0x00A6` | 5 | 2 | 1 | `P_REAR_CENTER_SEAT_BELT_INDICATOR_ENABLED` | `00` | false | 00=Disable / 01=Enable |
| `0x00A6` | 5 | 3 | 1 | `P_REAR_RIGHT_SEAT_BELT_INDICATOR_ENABLED` | `00` | false | 00=Disable / 01=Enable |
| `0x00A6` | 6 | 5 | 1 | `P_VEHICLE_PROPULSION_READY_INDICATOR_ENABLED` | `01` | false | 00=Disable / 01=Enable |
| `0x00A6` | 6 | 6 | 1 | `P_4WD_INDICATOR_ENABLED` | `00` | false | 00=Disable / 01=Enable |
| `0x00A6` | 6 | 7 | 1 | `P_POWER_TAKE_OFF_ENGAGEMENT_INDICATOR_ENABLED` | `00` | false | 00=Disable / 01=Enable |
| `0x00A6` | 9 | 1 | 1 | `P_SUPERCRUISE_LANE_CENTERING_INDICATOR_ENABLED` | `00` | false | 00=Disable / 01=Enable |
| `0x00A8` | 0 | 1 | 2 | `P_CURRENT_DISPLAY_UNIT` | `00` | true | 00=UNIT_METRIC / 01=UNIT_US / 02=UNIT_IMPERIAL / 03=Reserved |

## DPS execution inputs

1. Put the XML and the matching DPS ECU-configuration XSD files in the DPS `Config` directory.
2. Supply the vehicle Build Record Data file (`.txt` or `.xml`) containing the applicable RPO content.
3. Configure DPS for GMW3110 over low-speed GMLAN/SWCAN, IPC address `0x60`, DLC pin 1.
4. Use **ECU Configuration**, select this XML and the build-data file, and inspect the calculated results before execution.
5. A write requires GM security access using table `01`, algorithm `37`; possession of the XML alone does not provide the security implementation.

## Safety and validation controls

- Do not use the XML defaults as a replacement for the car's current data. Defaults describe the configuration model, not necessarily the present vehicle configuration.
- Read and save DIDs `0x0002`, `0x0003`, and `0x00A1` through `0x00A8` before any configuration write, even though this XML has an empty `ReadSection`.
- Record VIN, IPC hardware/software/calibration identifiers, XML identifier DIDs `0x009C/0x009D`, RPO list, and the complete before/after payloads.
- `0x00A2` controls DTC/FTB masking. Incorrect values can hide faults; do not alter it casually.
- `0x00A0` is the Manufacturing Enable Counter. Incorrect handling can change security behavior; preserve the original value.
- `0x00A7` is the configuration-complete flag. Writing it prematurely can misrepresent an incomplete configuration as valid.
- Perform initial work on the donor IPC or a bench harness with stable battery support, not the operating car.

## Generated files

- `dids.csv`: all DID metadata and defaults
- `parameters.csv`: all 147 byte/bit definitions and interpretations
- `rpo_rules.csv`: every computed value and its Boolean RPO expression
- `rpo_codes.csv`: recognized build-option inputs
- `write_sequence.csv`: prescribed DID write order
