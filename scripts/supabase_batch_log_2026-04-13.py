"""
Supabase batch-log for Tier 1 Monday send — 14 outreach_activities rows.

Reads the sent-message log from Gmail audit JSONL, maps each messageId
to its UTM campaign, inserts outreach_activities, updates prospects.status,
sets next_follow_up_at.

Requires SENTINEL_CORE_SUPABASE_URL and SENTINEL_CORE_SERVICE_KEY env vars
(project: sentinel-core / zysfnkbwyhrfnpvcnptp).
"""
import json
import os
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

from supabase import create_client

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

AUDIT_LOG = Path(os.path.expanduser("~")) / "agent-office-audit" / "email-processor-2026-04.jsonl"

# Segment → utm_campaign mapping (from email body signature URLs)
SEGMENT_CAMPAIGNS = {
    "sales@twiddy.com": "obx_vacation_q2_2026",
    "info@villagerealtyobx.com": "obx_vacation_q2_2026",
    "vacations@resortrealty.com": "obx_vacation_q2_2026",
    "rentals@carolinadesigns.com": "obx_vacation_q2_2026",
    "sunservices@sunrealtync.com": "obx_vacation_q2_2026",
    "sales@seasiderealty.com": "obx_vacation_q2_2026",
    "info@kotarides.com": "hr_property_mgmt_q2_2026",
    "dale@roseandwomble.com": "hr_property_mgmt_q2_2026",
    "info@rwtowne.com": "hr_residential_q2_2026",
    "tmrealty@tmrealty.com": "ne_nc_inland_q2_2026",
    "chris.todd@cbre.com": "hr_commercial_q2_2026",
    "chris.rouzie@thalhimer.com": "hr_commercial_q2_2026",
    "information@naidominion.com": "hr_commercial_q2_2026",
    "bspencer@midatlanticcommercial.com": "hr_commercial_q2_2026",
}

SEND_DATE = "2026-04-13"
NEXT_FOLLOWUP = "2026-04-16"


def load_sends_from_audit():
    """Parse gmail_send events from audit log."""
    sends = {}
    with AUDIT_LOG.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            if rec.get("event") == "gmail_send":
                sends[rec["to"]] = {
                    "messageId": rec["messageId"],
                    "threadId": rec["threadId"],
                    "subject": rec["subject"],
                    "ts": rec["ts"],
                }
    return sends


def main():
    url = os.environ.get("SENTINEL_CORE_SUPABASE_URL")
    key = os.environ.get("SENTINEL_CORE_SERVICE_KEY")
    if not url or not key:
        print("ERROR: SENTINEL_CORE_SUPABASE_URL and SENTINEL_CORE_SERVICE_KEY required.")
        print("  URL should be https://zysfnkbwyhrfnpvcnptp.supabase.co")
        print("  Key is the service_role key (Settings → API in Supabase dashboard).")
        return 2

    sb = create_client(url, key)

    sends = load_sends_from_audit()
    print(f"Loaded {len(sends)} sends from audit log")

    activities = []
    update_emails = []
    for email, info in sends.items():
        campaign = SEGMENT_CAMPAIGNS.get(email, "unknown")
        activities.append({
            "prospect_email": email,
            "activity_type": "cold_email",
            "channel": "email",
            "utm_source": "cold_email",
            "utm_medium": "email",
            "utm_campaign": campaign,
            "utm_content": "email_1_first_touch",
            "external_id": info["messageId"],
            "thread_id": info["threadId"],
            "subject": info["subject"],
            "sent_at": info["ts"],
            "notes": "tier1-monday-2026-04-13 owner-override batch send",
        })
        update_emails.append(email)

    # 1. Insert activities
    print(f"\nInserting {len(activities)} activities...")
    r1 = sb.table("outreach_activities").insert(activities).execute()
    print(f"  inserted: {len(r1.data)}")

    # 2. Update prospects status
    print(f"\nUpdating {len(update_emails)} prospects → status='contacted'...")
    for email in update_emails:
        sb.table("outreach_prospects").update({
            "status": "contacted",
            "first_contacted_at": f"{SEND_DATE}T00:00:00Z",
            "next_follow_up_at": f"{NEXT_FOLLOWUP}T00:00:00Z",
        }).eq("primary_email", email).execute()
        print(f"  updated: {email}")

    print("\nDone.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
