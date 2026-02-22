# Interview Prep: Collier County — Instrumentation/Electrical Technician

**Interview Date:** February 19, 2026 ✓ (Completed)
**Location:** 6027 Shirley Street, Naples, FL 34109
**Interviewers:** Frank, Glenn, + one other
**Status:** Awaiting response / Potential follow-up

---

## 1. The Opportunity

### Role: Instrumentation/Electrical Technician
- **Department:** Collier County Public Utilities
- **Focus:** Telemetry systems, water & wastewater pump stations
- **Day-to-day:** Ladder logic programming, RTU/PLC maintenance, instrumentation troubleshooting

### The Succession Angle (BIG OPPORTUNITY)
- **Glenn** = current programmer handling backend work (Python, C++, JavaScript)
- Glenn is **retiring soon**
- They see you as a potential replacement for Glenn's role
- Most of the team uses **ladder logic** — Glenn is the exception doing higher-level programming
- This means: **Start as tech → grow into Glenn's programming/engineering role**

### Why This Matters
- County government = job stability, benefits, pension
- You're local (Naples) — no relocation
- Clear career path built into the position
- Your Python skills + controls background = perfect for Glenn's succession

---

## 2. Collier County Public Utilities — Overview

### Scale
- Serves 300,000+ residents in Collier County
- Water, wastewater, irrigation, and reclaimed water systems
- Multiple treatment plants + hundreds of remote sites (lift stations, pump stations, wells)

### Facilities (likely what you'd work on)
- **Water Treatment Plants:** North, South, and regional facilities
- **Wastewater Treatment Plants:** Multiple facilities
- **Lift Stations:** Dozens across the county — pump sewage to treatment plants
- **Pump Stations:** Water distribution, irrigation, stormwater
- **Remote Wells & Tanks:** Level monitoring, telemetry

### Location Context
- 6027 Shirley Street = Collier County Public Utilities Operations Center
- You'd likely be based here with field work across the county

---

## 3. Core Technical Knowledge

### A. Telemetry Systems

**What it is:**
Remote monitoring and control — field sites send data back to central SCADA, and operators can control equipment remotely.

**Components:**
| Component | Function |
|-----------|----------|
| **RTU/PLC** | Collects data from sensors, executes control logic |
| **Radio/Cellular** | Transmits data wirelessly (MDS radios, cellular modems) |
| **Master Station** | Central SCADA server that aggregates all site data |
| **HMI** | Operator screens for monitoring and control |

**What you'd do:**
- Troubleshoot communication failures (radio issues, signal loss)
- Configure RTU/PLC communication settings
- Verify data is transmitting correctly to SCADA
- Replace/repair failed telemetry equipment

---

### B. Remote Terminal Units (RTUs)

**What it is:**
Ruggedized field controller that collects sensor data and executes basic control logic. Similar to a PLC but designed for remote, harsh environments.

**Common RTU brands:**
- Motorola ACE / MOSCAD
- Schneider Electric SCADAPack
- ABB RTU500 series

**Typical RTU I/O:**
- Digital Inputs: Float switches, pump run status, door alarms
- Digital Outputs: Pump start/stop commands
- Analog Inputs: Level transmitters (4-20mA), flow meters, pressure sensors
- Analog Outputs: VFD speed commands

**Programming:**
- Usually ladder logic or function block
- Some support structured text or C-based scripting

---

### C. Water & Wastewater Pump Stations

#### Lift Stations (Wastewater)
**Purpose:** Pump sewage from low points up to treatment plant or next gravity sewer

**Key components:**
- Wet well (holding tank)
- Submersible pumps (usually 2 — lead/lag)
- Level sensors (ultrasonic, pressure transducer, or floats)
- Control panel with PLC/RTU
- Telemetry radio/cellular

**Control logic:**
- Pump 1 (Lead) starts at high level setpoint
- Pump 2 (Lag) starts if level keeps rising
- Both stop at low level setpoint
- Lead/lag alternation to equalize wear
- High-high alarm → notify operator
- Pump fail → auto-switch to backup

#### Water Pump Stations (Potable/Distribution)
**Purpose:** Maintain pressure in distribution system, fill storage tanks

**Key components:**
- Pumps (often VFD-controlled)
- Pressure transmitters
- Flow meters
- Chlorine analyzers (for boosting)

**Control logic:**
- Maintain discharge pressure setpoint
- VFD adjusts speed based on demand
- Start/stop based on tank levels or system pressure

---

### D. HMI (Human-Machine Interface)

**What it is:**
The screens operators use to monitor and control the system — either local touchscreens at the site or SCADA workstations centrally.

**Common HMI/SCADA platforms:**
- Wonderware (AVEVA)
- Ignition (Inductive Automation)
- VTScada
- FactoryTalk View (Rockwell)
- GE iFIX

**What you'd do:**
- Navigate HMI to diagnose issues
- Read trends and alarm logs
- Acknowledge alarms
- Possibly make minor screen edits

---

### E. Ladder Logic

**What it is:**
Graphical programming language for PLCs — looks like electrical relay diagrams.

**Basic elements:**
| Symbol | Name | Function |
|--------|------|----------|
| —] [— | Normally Open Contact | True when input is ON |
| —]/[— | Normally Closed Contact | True when input is OFF |
| —( )— | Output Coil | Energizes when rung is true |
| —[TON]— | Timer On-Delay | Delays turning on |
| —[CTU]— | Counter Up | Counts events |

**Example — Pump Start Logic:**
```
|  Start_PB    Stop_PB     Motor_Run    Motor_Out  |
|----] [----+----]/[----+----] [----+----( )-------|
|           |           |           |              |
|           | Seal-in   |           |              |
```

**Your experience:**
You taught this at FGCU for 3 years — you know ladder logic deeply. Emphasize that you've designed, built, and debugged ladder logic programs.

---

### F. Glenn's Programming Role (Your Future Path)

**Why they need Python/C++/JavaScript:**
- **Python:** Data analysis, automation scripts, custom tools, API integrations
- **C++:** Some RTUs support C-based programming (SCADAPack, etc.)
- **JavaScript:** Web-based HMIs (Ignition Perspective uses JS), custom dashboards

**What Glenn probably does:**
- Writes scripts to automate reports
- Custom SCADA integrations
- Data export/analysis tools
- Possibly custom HMI development

**Your advantage:**
You're already proficient in Python, have automation experience, and understand controls — you're the ideal candidate to take over Glenn's role.

---

## 4. Your Strengths for This Role

### 1. Controls Engineering TA (3 years)
- Designed and programmed PLC systems
- Built control panels
- Taught ladder logic to 100+ students
- Created documentation packages

### 2. Python Programming
- Self-taught, actively using
- Built automation tools
- Can step into Glenn's programming role

### 3. Industrial Experience
- AXI International: Control system layouts, EtherNet/IP, PLC troubleshooting
- Insulet: Regulated documentation, equipment maintenance
- Marmon: Electrical schematics, military-spec documentation

### 4. Local
- You're already in Naples — no relocation needed
- Know the area, can respond quickly to field sites

### 5. Fast Learner
- Track record of picking up new tools quickly
- Taught yourself Python, AI tools, multiple CAD platforms

---

## 5. Likely Technical Questions & Answers

**Q: Walk me through how a lift station works.**
> "A lift station collects wastewater in a wet well. Level sensors monitor the depth — typically a pressure transducer or ultrasonic sensor giving 4-20mA to the PLC. When level hits the high setpoint, the lead pump starts and pumps down the wet well. If level keeps rising, the lag pump kicks in. Both shut off at the low setpoint. The PLC alternates lead/lag to equalize pump wear. If level hits high-high, it triggers an alarm to SCADA so an operator can respond before overflow."

**Q: How do you troubleshoot a communication failure to a remote site?**
> "First, check if it's site-wide or just one signal. If site-wide, likely a radio/cellular issue — check signal strength, power to the radio, antenna connections. If it's one signal, the sensor or wiring might be bad. I'd check the RTU I/O status locally to see if the RTU is reading the value correctly. If the RTU sees it fine but SCADA doesn't, it's the telemetry link. If the RTU shows bad data, trace it back to the sensor."

**Q: Digital vs. analog — when would you use each?**
> "Digital for on/off status — pump running, valve position, float switches, alarms. Analog for variable measurements — tank level, flow rate, pressure, temperature. If I need to know how much, it's analog. If I just need yes or no, it's digital."

**Q: What's your experience with ladder logic?**
> "I taught PLC programming at FGCU for three years. I've designed ladder logic for pump control, traffic light sequencing, temperature PID loops, state machines. I understand the logic, timing, and how to structure programs that are readable and maintainable. I've also debugged students' broken code for years, so I'm quick at finding issues."

**Q: You know Python — how would that help in this role?**
> "A lot of SCADA data analysis is manual or clunky. Python can automate report generation, pull data from historians, run trend analysis, even build custom dashboards. If Glenn is doing that kind of work now, I can step into it. I've built automation scripts and data tools before — it's a natural fit."

---

## 6. Questions to Ask (if there's a follow-up)

1. **"What does Glenn's typical week look like — what kind of projects is he working on?"** (Shows you're thinking about the succession)

2. **"What SCADA platform and PLC brands does the county use?"** (Technical curiosity)

3. **"How many remote sites does the telemetry system cover?"** (Scope of the role)

4. **"What does the on-call rotation look like?"** (County jobs often have on-call)

5. **"What would success look like in the first 90 days?"**

---

## 7. Quick Reference — Formulas & Conversions

### 4-20mA to Engineering Units
```
EU = ((mA - 4) / 16) × EU_max
```

### Quick mA Reference
| mA | % of span |
|----|-----------|
| 4 | 0% |
| 8 | 25% |
| 12 | 50% |
| 16 | 75% |
| 20 | 100% |

### Pump Flow (approximation)
```
GPM = Velocity (ft/s) × Pipe Area (ft²) × 448.8
```

### Wet Well Capacity
```
Gallons = Length × Width × Depth × 7.48
```

---

## 8. Interview Debrief Notes

**Interviewers:**
- **Frank** — [role TBD]
- **Glenn** — Current programmer (Python, C++, JS), retiring soon
- **Third person** — [name/role TBD]

**Key Takeaways:**
- They see you as a potential Glenn replacement
- Ladder logic is the standard; Glenn is the exception doing real programming
- Required knowledge: telemetry, water/wastewater pump stations
- This is tech role → programming role succession path

**Your Impression:**
[Add your notes here after we discuss]

---

## 9. Study Priority

1. ✅ Telemetry systems architecture
2. ✅ RTU basics
3. ✅ Lift station control logic
4. ✅ Ladder logic fundamentals (you already know this)
5. ⬜ Collier County specific systems (ask about SCADA platform)
6. ⬜ VFD operation and troubleshooting
7. ⬜ Common sensor types and failure modes

---

*Last updated: 2026-02-21*
