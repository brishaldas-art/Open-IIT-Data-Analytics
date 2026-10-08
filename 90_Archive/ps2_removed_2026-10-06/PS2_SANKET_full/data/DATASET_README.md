# CN Synthetic Collections Data 

 collections data for three problem statements. Everything in it is invented.

## Files

| File | What it holds | Used for |
| :---- | :---- | :---- |
| `data/raw/accounts.csv` | One row per loan account: lender, product, bucket, dues and what the lender knows about the borrower | PS1, PS2, PS3 |
| `data/raw/splits.csv` | Which accounts are train, validation and test | PS1, PS2, PS3 |
| `data/raw/lenders.csv` | The six lenders | PS1, PS2, PS3 |
| `data/raw/agents.csv` | Tele-calling agents, field agents and the voice bot | PS1, PS2, PS3 |
| `data/raw/dial_attempts.csv` | Every outbound call attempt, with its result, disposition and agent remark | PS1, PS2 |
| `data/raw/payments.csv` | Every payment received | PS1, PS2 |
| `data/raw/addresses.csv` | Every address on file, as written in the lender's system | PS2, PS3 |
| `data/raw/field_visits.csv` | Every field visit, with check-in location, outcome and agent remark | PS2, PS3 |
| `../../../90_Archive/ps1_fake_ptp_not_used/ptps.csv` | Every promise to pay recorded on a call or a visit | PS1 |
| `../../../90_Archive/ps1_fake_ptp_not_used/call_transcripts.csv` | Turn-by-turn transcripts of calls | PS1 |
| `../../../90_Archive/ps1_fake_ptp_not_used/post_call_events.csv` | What happened after a PTP: payment link sent or opened, WhatsApp confirmations, customer calls | PS1 |
| `../../../90_Archive/ps1_fake_ptp_not_used/annotated_ptp_sample.csv` | 200 PTPs labelled by type by a reviewer (some labels are wrong) | PS1 |
| `data/raw/phones.csv` | Every phone number linked to an account, and where the number came from | PS2 |
| `data/raw/skip_traces.csv` | Skip-trace requests and what they found | PS2 |
| `data/raw/verified_contact_points.csv` | 250 numbers checked by a verification campaign | PS2 |
| `../../PS3_SUTRA/data/raw/towns.csv` | The three towns | PS3 |
| `../../PS3_SUTRA/data/raw/localities.csv` | Localities in each town, with pincode and approximate centre | PS3 |
| `../../PS3_SUTRA/data/raw/landmarks_poi.csv` | Landmark database (incomplete and slightly off) | PS3 |
| `../../PS3_SUTRA/data/raw/baseline_geocodes.csv` | Where a commercial geocoder places each address: the baseline to beat | PS3 |
| `../../PS3_SUTRA/data/raw/visit_gps_points.csv` | GPS trail for each field visit | PS3 |
| `../../PS3_SUTRA/data/raw/surveyed_addresses.csv` | 100 addresses with accurately surveyed locations | PS3 |

## Files by problem statement

PS1, Real-Time Fake PTP Detection: `ptps.csv`, `call_transcripts.csv`, `post_call_events.csv`, `annotated_ptp_sample.csv`, `dial_attempts.csv`, `payments.csv`, `accounts.csv`, `agents.csv`

PS2, Right-Party Contact Prediction and Skip-Trace Prioritisation: `dial_attempts.csv`, `phones.csv`, `skip_traces.csv`, `verified_contact_points.csv`, `field_visits.csv`, `addresses.csv`, `payments.csv`, `accounts.csv`, `agents.csv`

PS3, Address Geocoder That Learns from Field Visits: `addresses.csv`, `baseline_geocodes.csv`, `field_visits.csv`, `visit_gps_points.csv`, `surveyed_addresses.csv`, `localities.csv`, `landmarks_poi.csv`, `towns.csv`, `accounts.csv`, `agents.csv`

All three also use `splits.csv`.
