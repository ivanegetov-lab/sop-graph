# Review report: How Plant 2 is run

20 documents, 133 things they touch, 380 links. **16 findings**, plus 11 housekeeping items and 31 things Claude was unsure about.

This report lists what the documents say. Whether each item matters is an engineering and quality decision.

**Quote check:** 136 quotes were compared with the document text. 0 could not be found word for word.

## Two documents, two numbers (2)

- **Two values for fill weight check interval (Lines 1, 2 and 3)** QP-303 says 1 hour; SOP-101 says 30 minutes
  - QP-303, step 1: “Once every hour, take 5 bottles in a row from the filler discharge.”
  - SOP-101, step 15: “then every 30 minutes for the rest of the shift, as described in QP-303.”
- **Two torque values for the same 38 mm cap** WI-211 Rev C raised the 38 mm cap torque from 15 to 17 in-lb after leak complaints. SOP-104 step 7.3 still tells the Operator to set 15 in-lb, and TR-701 requires operators to be trained on WI-211 Rev A, the version before the change. Line 2 operators following SOP-104 or trained to TR-701 would set the old torque.
  - SOP-104, 7.0 step 3: “Set the application torque to 15 in-lb, plus or minus 2.”
  - WI-211, Application torque table: “38 mm Line 2 (CAP-2), both bottle sizes 17 plus or minus 2”

## Two documents, two rules (6)

- **SOP-101, SOP-104 and MP-501 have the Maintenance Technician remove locks; SP-402 says each person removes only their own** SP-402 step 8 lets each person remove only their own lock, and Operators can be Authorized Employees. SOP-101, SOP-104 and MP-501 assign lock removal to the Maintenance Technician alone, which cannot cover a lock an operator applied.
  - MP-501, 6.0 step 4: “Maintenance Technician: Remove locks. Run the filler empty for 2 minutes”
  - SOP-101, Roles / step 2: “Removes locks after maintenance work.”
  - SOP-104, 7.0 step 7: “Maintenance Technician: Remove locks and tags as described in SP-402.”
  - SP-402, step 8: “Each person removes only their own lock.”
- **MP-502 still tells technicians to use the group lock box that SP-402 Rev D removed** MP-502 step 7.1 locks out the case packer with the group lock box per SP-402 Rev B. SP-402 Rev D says 'Group lock box removed' and requires one person, one lock, one key. WI-213 points to SP-402 without a revision, so only MP-502 is out of date.
  - MP-502, 7.0 step 1: “Lock out the case packer using the group lock box, as described in SP-402, Rev B.”
  - SP-402, step 5 / Revision history: “One person, one lock, one key. Each person working on the machine applies their own lock to the hasp.”
  - WI-213, step 7: “For any work inside the guards, lock out as described in SP-402.”
- **Two answers to who may change the fill setpoint** WI-210 Rev D (2023) lets operators adjust the setpoint by up to 2 g. QP-303 Rev F (2024) says operators must not change it and only the Maintenance Technician may. WI-210 was not revised after QP-303, and TR-701 trains operators on WI-210.
  - QP-303, step 6: “Operators must not change the fill setpoint.”
  - QP-303, step 7: “Only the Maintenance Technician changes the setpoint, and the change is written on the chart.”
  - WI-210, step 5: “you may adjust the fill setpoint by up to 2 g up or down.”
  - WI-210, step 6: “stop adjusting and call the Maintenance Technician.”
- **Two different roles move held product to the hold cage** QP-315 step 2 makes the Team Leader responsible for moving held product to the hold cage the same shift. SOP-102 step 4 has the Operator do it at shutdown. Team Leader is not defined anywhere else.
  - QP-315, step 2: “Move held product to the hold cage the same shift. Nothing on hold stays at the line.”
  - SOP-102, step 4: “Move any product on hold to the hold cage as described in QP-315.”
- **Forklift speed limit: 5 mph everywhere (SP-405) versus 3 mph on the dock (WH-601)** SP-405 step 2 says the maximum is 5 mph everywhere inside the building, including dock doors. WH-601 step 3 says no faster than 3 mph on the dock and in the receiving lanes. A driver who reads only SP-405 would think 5 mph is allowed at the dock.
  - SP-405, step 2: “Maximum speed is 5 mph everywhere inside the building.”
  - WH-601, step 3: “no faster than 3 mph”
- **SOP-104 locks out only FIL-2 and CAP-2 but the changeover also works on LAB-2, CPK-2 and CNV-2** SP-402 applies to all servicing, cleaning and jam clearing that puts any part of the body inside a guard on any equipment. SOP-104 locks out only FIL-2 and CAP-2 in preparation, then has operators change parts on the labeler, case packer and conveyor with no lockout stated. If those changes reach inside a guard, SP-402 requires a lock.
  - SOP-104, 6.0 step 4: “Lock out FIL-2 and CAP-2 as described in SP-402.”
  - SOP-104, 7.0 step 5: “change the case magazine guides and select the pack pattern”
  - SP-402, Scope: “All servicing, cleaning and jam clearing that puts any part of the body inside a guard, on any equipment at Plant 2.”

## Gap between documents (4)

- **Label liner caliper is critical on every lot (QP-309 Rev G) but QP-308 does not check it** QP-309 Rev G made label liner caliper (0.075 mm plus or minus 0.005) a critical characteristic that must be measured on every lot. QP-308 Rev D (2023, older than QP-309 Rev G) lists the label checks at incoming inspection and liner caliper is not among them. QP-309 step 3 also requires QP-308 to be updated after a change.
  - QP-309, step 4: “Characteristics marked critical below must be measured on every lot.”
  - QP-309, Revision history: “Label liner caliper made a critical characteristic for the new Line 3 labeler.”
  - QP-308, step 6: “print quality, barcode grade C or better, roll width, core diameter 76 mm, labels wound outward.”
- **SOP-102 shutdown cleaning does not refer to lockout** SOP-102 has operators clean the filler nozzles and drip tray and empty the case packer reject bin, and does not mention SP-402. SP-402 covers cleaning that puts any part of the body inside a guard. Whether these tasks reach inside guards is not stated.
  - SOP-102, step 2: “Clean filler nozzles and the drip tray. Wipe the labeler rollers. Empty the case packer reject bin.”
  - SP-402, Scope: “All servicing, cleaning and jam clearing that puts any part of the body inside a guard, on any equipment at Plant 2.”
- **QP-306 asks for a packed case at first-off but SOP-101 start-up does not produce one** QP-306 step 1 has the Operator bring the first 5 good bottles and one packed case to the QA bench, and QA checks the case in step 6. SOP-101 steps 11 and 12 run 20 bottles and take the first-off samples to the QA Technician, with no step for a packed case.
  - QP-306, step 1: “Bring the first 5 good bottles and one packed case to the QA bench.”
  - SOP-101, step 12: “Run 20 bottles and stop. Take the first-off samples to the QA Technician.”
- **QP-306 checks cap removal torque against a range that WI-211 does not give** QP-306 step 3 passes the first-off cap if removal torque is inside the range in WI-211. WI-211 only gives an application torque with a tolerance for each cap size, and has the operator measure removal torque without stating a removal range.
  - QP-306, step 3: “Cap: correct cap, removal torque inside the range in WI-211.”
  - WI-211, step 3: “Set the application torque from the table below.”

## Cites an old revision (2)

- **MP-502 cites SP-402 Rev B; the current revision is D** Work may be following a withdrawn version.
  - MP-502, 5.0 and 7.0 step 1
- **TR-701 cites WI-211 Rev A; the current revision is C** Work may be following a withdrawn version.
  - TR-701, Required procedures by role; Related documents

## Points to a document that isn't there (2)

- **QP-315 points to QP-318, which is not in the set** The document is referenced but was not among the files provided. It may be missing, withdrawn or renumbered.
  - QP-315, step 5
- **WI-212 points to WI-215, which is not in the set** The document is referenced but was not among the files provided. It may be missing, withdrawn or renumbered.
  - WI-212, step 7

## Job without required training (3)

- **QA Technician has a job in 7 procedures that are not on its training list** Procedures: QP-309, QP-316, SOP-101, SOP-104, SOP-105, WH-601, WI-212.
  - QP-309, Roles
  - QP-316, 3.0 Responsibilities
  - SOP-101, Roles
  - SOP-104, 3.0 Responsibilities
  - SOP-105, 3.0 Responsibilities
  - WH-601, Roles
  - WI-212, step 11
- **Maintenance Technician has a job in 5 procedures that are not on its training list** Procedures: QP-303, SOP-101, SOP-104, WI-211, WI-212.
  - QP-303, Roles
  - SOP-101, Roles
  - SOP-104, 3.0 Responsibilities
  - WI-211, Roles
  - WI-212, Roles
- **Operator has a job in 2 procedures that are not on its training list** Procedures: MP-501, QP-306.
  - MP-501, 7.0 step 4
  - QP-306, Roles

## Role missing from the training list (1)

- **11 roles with jobs in procedures are not in the training list** Batching Operator (SOP-105); Department Manager (TR-701); Maintenance Planner (MP-501, MP-502); Production Planner (WH-601); Purchasing (QP-308, QP-309, WH-601); Quality Manager (QP-309, QP-315, QP-316); Safety Manager (SP-402, SP-405); Shift Lead (MP-501, QP-316, SOP-104, SOP-105); Team Leader (QP-315); Training Coordinator (TR-701); Warehouse Supervisor (SP-405, WH-601). Some may be other names for listed roles.

## Not revised for years (1)

- **11 documents not revised in more than 3 years** MP-502 (7.2 years), MP-501 (6.7 years), QP-316 (6.0 years), SOP-105 (5.8 years), SOP-104 (5.7 years), QP-315 (4.6 years), WI-213 (4.2 years), WI-211 (4.0 years), WI-210 (3.6 years), WH-601 (3.4 years), QP-308 (3.1 years).

## Names that may be the same thing (6)

- **“Shift Lead” and “Line Lead” may be the same role** If they are, add them to aliases.json and rebuild so the graph treats them as one.
- **“Shift Lead” and “Team Leader” may be the same role** If they are, add them to aliases.json and rebuild so the graph treats them as one.
- **“Operator” and “Batching Operator” may be the same role** If they are, add them to aliases.json and rebuild so the graph treats them as one.
- **“Line Lead” and “Team Leader” may be the same role** If they are, add them to aliases.json and rebuild so the graph treats them as one.
- **“Caps” and “Caps (28 mm)” may be the same material** If they are, add them to aliases.json and rebuild so the graph treats them as one.
- **“Caps” and “Caps (38 mm)” may be the same material** If they are, add them to aliases.json and rebuild so the graph treats them as one.

## Unclear to Claude (31)

Things that could not be read or had to be left open. Check these against the documents.

- **MP-501** 7.0 step 4: Step 4 of section 7.0 is written as a Maintenance Technician step but assigns the action to 'the operator' Unclear who actually repeats the nozzle check; WI-210 has no 'repeat after seal change' step
- **MP-501** 3.0 Responsibilities: Shift Lead, a role not used in the Line Lead procedures May be the same person as the Line Lead; not stated
- **MP-502** 6.0 step 3: Vacuum reading is taken at the pump inlet with the erector idle (0.7 bar), WI-213 reads at the erector cups (0.6 bar) Different measuring points; document does not say how they relate
- **QP-303** step 3 / Tools: The 1 kg test weight is used in step 3 but is not listed under Tools Tools list only the check scale and tare bottles
- **QP-303** Roles / step 5: Roles table says the QA Technician places product on hold; step 5 has the Line Lead doing it Internal inconsistency in who places the hold
- **QP-306** step 3: Step 3 checks removal torque against 'the range in WI-211' WI-211's table gives application torque with a tolerance, not a removal torque range
- **QP-306** step 2: Fill weight check says 'limits in WI-210' WI-210 limits are per product; which product's limits apply is by context only
- **QP-308** step 6: Label checks do not list liner caliper QP-309 Rev G (later than this Rev D) makes label liner caliper a critical characteristic on every lot; this document is not updated for it
- **QP-309** step 3: 'the label and cap setup instructions' not named by number Assumed to be WI-212 (labeler) and WI-211 (capper); the document does not give numbers
- **QP-309** Specifications table: 'Caps, 28 mm and 38 mm' share one row; Labels row says 'pressure-sensitive' Table cells wrap; supplier column alignment read from the image
- **QP-315** Roles / steps 2 and 3: Team Leader is not a role in any other document May be the Line Lead or Shift Lead; not stated
- **QP-315** step 5: QP-318 Rework is referenced but its content is not in the document set Not provided
- **QP-316** 6.0 step 1: Lot code form P2-L3-261104-A: plant, line, year-month-day, shift The date '261104' reads as 2026-11-04 but the document is dated 2020; it is only an example
- **QP-316** 3.0 Responsibilities: 'Shift Lead' role Other documents use Line Lead; not stated whether these are the same
- **SOP-101** step 12: Step 12 has the Operator run 20 bottles before first-off samples; QP-306 asks for the first 5 good bottles and one packed case Not clear whether the 20 bottles include the 5; the case sample is not mentioned in SOP-101
- **SOP-102** step 2: Cleaning filler nozzles, the drip tray and the case packer reject bin (step 2) does not mention lockout SP-402 scope covers cleaning that puts any part of the body inside a guard; SOP-102 does not reference SP-402
- **SOP-104** 2.0 Scope: Products FS-2000 and FS-0500 are named in scope but the schema has no field for products Not extracted as a node
- **SOP-104** 6.0 step 4 / 7.0 steps 4-6: Steps 7.0.4 to 7.0.6 (labeler, case packer, conveyor changes) are done by the Operator with no lockout stated Only FIL-2 and CAP-2 are locked out in 6.0 step 4; unclear whether the other machines are inside guards
- **SOP-105** 2.0 Scope: Scope says the clearance steps also apply to Line 2 size changeovers Not stated whether the Batching Operator flush applies to a Line 2 size change (SOP-104 does not mention it)
- **SOP-105** 2.0 Scope: Products AC-1000, AC-1000-LEM, DS-0750, DS-0750-ECO named in scope No field for products in the schema
- **SP-402** Roles: 'Trained and listed' Authorized Employees The list is not part of this document and TR-701 has no row for the Authorized Employee role
- **TR-701** Required procedures by role: Line Lead row says 'Everything for Operator, plus QP-306'; expanded here to the Operator list plus QP-306 Expansion is mine, not printed
- **TR-701** Required procedures by role: Operator row names WI-211 'Rev A', while the current WI-211 is Rev C May be intentional pinning or a stale revision; not explained
- **TR-701** Required procedures by role: No row for Shift Lead, Team Leader, Batching Operator, Quality Manager, Warehouse Supervisor, Purchasing, Authorized Employee Roles used in other procedures but absent from the training table
- **WH-601** Scope: Dock doors 1 to 4 have no equipment tag in this document SP-405 calls the dock levelers DOCK-1 to DOCK-4, but WH-601 does not give tags, so no tag assumed
- **WI-210** step 3: Number of nozzles on FIL-2 and FIL-3 Step 3 says 'all nozzles on FIL-2 and FIL-3' without a number
- **WI-210** Fill targets table: Products (AC-1000, FS-2000, FS-0500, DS-0750 and variants) have no field in the schema Only captured as applies_to text in parameters
- **WI-211** step 4 / table: The table gives application torque; step 4 has operators measure removal torque No removal torque range is given, although QP-306 step 3 refers to 'the range in WI-211'
- **WI-212** step 7: WI-215 Label Splicing is referenced but not in the document set Not provided
- **WI-212** Revision history: Rev D says 'Updated for the new Line 3 labeler' but no step mentions the liner caliper that QP-309 Rev G made critical Only a gap if QP-309 step 3 expects the setup instruction to change; not stated
- **WI-213** step 7: Rev B (2022) says nothing about the glue tank cool-down or tagged lid that SP-402 Rev D (2025) added for case packers WI-213 just points to SP-402 and does not say who locks out beyond 'the Operator'

## Compared and found consistent (7)

- Two values for minimum vacuum (case packer) (MP-502, WI-213). Measured at different points: MP-502 reads at least 0.7 bar at the pump inlet with the erector idle, WI-213 reads at least 0.6 bar at the erector cups with a case on them. The lower figure at the cups is expected, but neither document says how the two relate.
- Compare: who releases the line (MP-501, SOP-101, SOP-104). MP-501 (Shift Lead releases after maintenance), SOP-104 (Shift Lead releases for changeover) and SOP-101 (Line Lead owns the start-up) describe different events and do not contradict each other. The Shift Lead versus Line Lead naming is left for the plant to decide.
- Compare: who places product on hold (QP-303, QP-315, QP-316, WI-211, WI-212). QP-315 lets anyone place product on hold, so the QA Technician (QP-303, QP-316), Line Lead (QP-303), Operator (WI-211, WI-212) are all allowed. QP-303's own roles table and step 5 name different people, but neither forbids the other.
- Compare: who gives first-off approval (QP-306, SOP-101, SOP-105). QP-306, SOP-101 and SOP-105 all give first-off approval to the QA Technician.
- Compare: who releases packaging materials (QP-308, WH-601, WI-212). QP-308 and WH-601 both give release to the QA Technician, and WI-212 only loads rolls that carry the QA release sticker.
- Compare: which suppliers' packaging may be used (QP-308, QP-309, WI-212). QP-309 limits purchasing to the listed supplier, QP-308 rejects lots from unlisted suppliers and WI-212 refuses rolls from unlisted suppliers. The three documents agree.
- Compare: who checks the dock before entering a trailer (SP-405, WH-601). SP-405 and WH-601 both require the Forklift Driver to chock the wheels and lock the dock leveler before entering a trailer.

