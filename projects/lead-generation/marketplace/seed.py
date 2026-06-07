"""
Seed Marceau Air as the first (internal) buyer + a few sample appointments.
Idempotent: safe to run repeatedly. Marceau-Air-first phase.

Usage: python seed.py
"""
import os
import models
import config

# Seed account password: env-overridable so production never uses the repo default.
SEED_PASSWORD = os.getenv("MARKETPLACE_SEED_PASSWORD", "MarceauAir!2026")


SAMPLE_APPTS = [
    dict(service_type="AC Not Cooling — Repair", city="Naples", zip="34110",
         scheduled_time="2026-06-10 14:00", price_cents=7500, est_job_value_cents=45000,
         job_summary="3-ton split, ~12yr, warm air from vents; homeowner home, ready to schedule.",
         homeowner_name="(sample) R. Alvarez", address_full="(sample) 1423 Egret Ct, Naples FL 34110",
         homeowner_phone="(239) 555-0142", homeowner_email="sample-alvarez@example.com",
         private_notes="Gate code 4421. Prefers afternoon.",
         consent_captured=True, consent_source="web form 2026-06-07"),
    dict(service_type="New System Install — Quote", city="Bonita Springs", zip="34135",
         scheduled_time="2026-06-11 10:30", price_cents=12000, est_job_value_cents=900000,
         job_summary="2-story, two zones, 18yr old units, homeowner wants full replacement quote.",
         homeowner_name="(sample) D. Whitman", address_full="(sample) 88 Palmetto Dr, Bonita Springs FL 34135",
         homeowner_phone="(239) 555-0177", homeowner_email=None,
         private_notes="Budget-conscious; comparing 2 bids.",
         consent_captured=True, consent_source="inbound call 2026-06-07"),
    dict(service_type="Maintenance / Tune-up", city="Estero", zip="33928",
         scheduled_time="2026-06-12 09:00", price_cents=3000, est_job_value_cents=18000,
         job_summary="Annual tune-up + filter; possible low refrigerant.",
         homeowner_name="(sample) P. Nguyen", address_full="(sample) 209 Sabal Palm Ln, Estero FL 33928",
         homeowner_phone="(239) 555-0193", homeowner_email="sample-nguyen@example.com",
         private_notes="",
         consent_captured=False, consent_source=None),  # left as draft (no consent) on purpose
]


def main():
    models.init_db()
    # Marceau Air seed buyer
    existing = models.authenticate("ops@marceauair.com", SEED_PASSWORD)
    if existing:
        print(f"Marceau Air already seeded (contractor #{existing['id']}).")
        cid = existing["id"]
    else:
        cid = models.create_contractor(
            "Marceau Air", "William Marceau", "ops@marceauair.com", SEED_PASSWORD,
            phone=config.BRAND["support_phone"], service_area="Naples / Bonita / Estero",
            is_seed=True, grant_promo=True)
        print(f"Seeded Marceau Air as contractor #{cid} (promo {config.dollars(config.SIGNUP_PROMO_CENTS)}).")

    # Sample appointments (only if none exist yet)
    if not models.list_all_appointments():
        for a in SAMPLE_APPTS:
            aid = models.create_appointment(**a)
            if a["consent_captured"]:
                models.publish_appointment(aid)
                print(f"  + appointment #{aid} published: {a['service_type']}")
            else:
                print(f"  + appointment #{aid} draft (no consent): {a['service_type']}")
    else:
        print("Appointments already present — skipping sample seed.")

    print("\nSeed complete.")
    print(f"  Contractor login: ops@marceauair.com / (MARKETPLACE_SEED_PASSWORD)")
    print(f"  Admin login:      {config.ADMIN_EMAIL} / (MARKETPLACE_ADMIN_PASSWORD)")


if __name__ == "__main__":
    main()
