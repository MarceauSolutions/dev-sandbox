# Workflow: Filing Procedure

## Overview
Step-by-step procedures for filing housing discrimination complaints with HUD, FCHR, and/or federal/state court.

## When to Use
- Ready to file an administrative complaint
- Considering legal action
- Responding to a filing or deadline

## Filing Options Comparison

| Option | Agency | Deadline | Cost | Attorney Needed? | Timeline |
|--------|--------|----------|------|-------------------|----------|
| HUD Complaint | HUD (federal) | 1 year | Free | No | 100 days investigation |
| FCHR Complaint | FCHR (Florida) | 365 days | Free | No | 180 days investigation |
| Federal Lawsuit | U.S. District Court | 2 years | Filing fee | Recommended | Months-years |
| State Lawsuit | FL Circuit Court | 2 years | Filing fee | Recommended | Months-years |

**Note**: You can pursue multiple options simultaneously. HUD and FCHR complaints can be dual-filed.

## Option A: HUD Administrative Complaint

### Prerequisites
- Discriminatory act occurred within last 1 year
- Evidence collected (SOP L1)
- Timeline documented (SOP L5)

### Steps
1. **Generate complaint draft**:
   ```bash
   python src/document_generator.py generate --template hud-complaint --output data/filings/
   ```
2. **Review and customize** the generated draft with case-specific details
3. **File with HUD** via one of:
   - Online: hud.gov/program_offices/fair_housing_equal_opp/online-complaint
   - Phone: 1-800-669-9777
   - Mail: Office of Fair Housing and Equal Opportunity, Dept. of HUD, 451 7th St SW, Washington DC 20410
   - Email: Send completed HUD Form 903 to your regional HUD office
4. **Log the filing**:
   ```bash
   python src/communication_logger.py add --date [today] --party "HUD" --medium online --summary "Filed housing discrimination complaint - Case #[number]"
   ```
5. **Add investigation deadline**:
   ```bash
   python src/deadline_tracker.py add --name "HUD 100-day investigation deadline" --date [date+100] --alert-days 90,60,30,14,7
   ```
6. **Save confirmation** to `data/filings/`

### What HUD Does
- Notifies respondent within 10 days
- Investigates within 100 days (can be extended)
- Attempts conciliation
- If cause found: charges filed before ALJ or election to go to federal court
- If no cause: dismissal (you can still file private lawsuit)

## Option B: FCHR Complaint

### Steps
1. File online at fchr.myflorida.com or by mail
2. FCHR has 180 days to investigate
3. If no determination within 180 days → request right to sue letter
4. With right to sue → 1 year to file state court action

## Option C: Federal Court Lawsuit

### Prerequisites
- Within 2-year statute of limitations
- Attorney recommended (can proceed pro se)
- Does NOT require exhausting administrative remedies first

### Potential Relief
- Actual damages (economic loss, emotional distress)
- Punitive damages
- Attorney fees and costs
- Injunctive relief (court order to stop discrimination)

## Option D: Pre-Suit Demand Letter

### Before Filing Anything
Consider sending a demand letter first:
```bash
python src/document_generator.py generate --template demand-letter --output data/filings/
```

A demand letter:
- Puts respondent on notice
- Creates documentation of the dispute
- May lead to settlement without litigation
- Shows good faith attempt to resolve

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Missed HUD deadline (>1 year) | File federal lawsuit (2-year deadline) or FCHR |
| HUD dismisses complaint | Request review or file private lawsuit |
| Can't afford attorney | Contact local legal aid, law school clinics, or fair housing organizations |
| Retaliation after filing | Document it - retaliation is a separate FHA violation (42 USC 3617) |

## Success Criteria
- [ ] Correct filing option selected based on timeline and strategy
- [ ] Document generated from template
- [ ] Filing submitted and confirmed
- [ ] Confirmation saved to data/filings/
- [ ] Communication logged
- [ ] Response deadlines added to tracker
