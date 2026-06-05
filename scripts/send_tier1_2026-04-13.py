"""
Tier 1 Cold Outreach — Monday 2026-04-13 batch send

One-shot owner-override execution per RISK-2026-04-13-001 and ADR-008.
Sends 14 pre-approved first-touch emails via Gmail API using existing
credentials.json. Every send is appended to the audit log.

NOT a reusable pattern. CISO must re-review before Paula executes
autonomous sends again. This script is kept as evidence.
"""
import json
import base64
import hashlib
import os
import sys
from datetime import datetime, timezone
from email.mime.text import MIMEText
from pathlib import Path

# Windows cp1252 terminals can't print unicode checkmarks
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


HOME = Path(os.path.expanduser("~"))
CREDS_PATH = HOME / ".gmail-mcp" / "credentials.json"
KEYS_PATH = HOME / ".gmail-mcp" / "gcp-oauth.keys.json"
AUDIT_LOG = HOME / "agent-office-audit" / "email-processor-2026-04.jsonl"
RUN_ID = f"tier1-monday-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')}"
SCHEMA_VERSION = "1.0.0"

# 14 pre-approved email bodies from agent-office/reports/2026-04-13-tier1-outreach-drafts.md
EMAILS = [
    {"to": "sales@twiddy.com", "subject": "rental listing photos", "body": """Hi,

Twiddy manages over 1,000 vacation homes from Carova to Nags Head — that's a massive portfolio to keep marketed to guests year-round. The listings with drone aerials consistently get more clicks and bookings than ground-only photos, especially for oceanfront and soundside properties where the location context matters as much as the interior.

I'm a Part 107 pilot based in Chesapeake. I fly OBX properties and deliver edited photos within 48 hours. $225 per property, no contracts.

For a portfolio your size, I'd fly one of your Duck or Corolla properties free so you can see the quality before committing to anything.

Worth a conversation?

Adam Redler
Sentinel Aerial Inspections
https://sentinelaerialinspections.com/?utm_source=cold_email&utm_medium=email&utm_campaign=obx_vacation_q2_2026
"""},
    {"to": "info@villagerealtyobx.com", "subject": "rental listing photos", "body": """Hi,

Village Realty manages 900+ beach rentals across Nags Head and Corolla — that's a lot of properties competing for guest bookings. The listings with drone aerials consistently outperform ground-only shots, especially when guests are comparing oceanfront proximity and beach access between similar properties.

I'm a Part 107 pilot based in Chesapeake. I fly OBX properties and deliver 20 edited aerials within 48 hours. $225 per property, no contracts.

I'd fly one of your current properties free so you can see the quality.

Worth a conversation?

Adam Redler
Sentinel Aerial Inspections
https://sentinelaerialinspections.com/?utm_source=cold_email&utm_medium=email&utm_campaign=obx_vacation_q2_2026
"""},
    {"to": "vacations@resortrealty.com", "subject": "rental listing photos", "body": """Hi,

Resort Realty manages 615+ rentals across Corolla, Duck, and Kill Devil Hills. For properties at that price point, guests expect to see exactly what they're booking — and drone aerials show the beach access, pool layout, and neighborhood context that ground photos miss.

I'm a Part 107 pilot based in Chesapeake. $225 per property, 20 edited aerials, delivered in 48 hours. No contracts.

I'd fly one of your Corolla or Duck properties free so you can see the quality.

Interested?

Adam Redler
Sentinel Aerial Inspections
https://sentinelaerialinspections.com/?utm_source=cold_email&utm_medium=email&utm_campaign=obx_vacation_q2_2026
"""},
    {"to": "rentals@carolinadesigns.com", "subject": "rental listing photos", "body": """Hi,

Carolina Designs manages 350 properties in Duck — that's a competitive rental market where listing quality directly impacts bookings. Drone aerials show guests the oceanfront proximity, pool deck, and surrounding area in a way that ground photos can't.

I'm a Part 107 pilot based in Chesapeake. $225 per property, 20 edited aerials, 48-hour delivery. No contracts.

I'd fly one of your Duck properties free so you can evaluate the quality.

Worth trying?

Adam Redler
Sentinel Aerial Inspections
https://sentinelaerialinspections.com/?utm_source=cold_email&utm_medium=email&utm_campaign=obx_vacation_q2_2026
"""},
    {"to": "sunservices@sunrealtync.com", "subject": "rental listing photos", "body": """Hi,

Sun Realty has been on the Outer Banks for 43 years with 7 offices — you know better than anyone that listing presentation drives bookings. Drone aerials show guests the full property in context: beach access, pool, surrounding homes, parking. The listings that have them consistently outperform.

I'm a Part 107 pilot based in Chesapeake. $225 per property, 20 edited aerials, 48-hour delivery. No contracts.

With properties spread across that many offices, I can batch multiple shoots per trip to keep costs efficient. I'd fly the first one free.

Worth a conversation?

Adam Redler
Sentinel Aerial Inspections
https://sentinelaerialinspections.com/?utm_source=cold_email&utm_medium=email&utm_campaign=obx_vacation_q2_2026
"""},
    {"to": "sales@seasiderealty.com", "subject": "rental listing photos", "body": """Hi,

Seaside manages vacation rentals and handles sales across the Outer Banks — which means you're constantly marketing properties to both guests and buyers. The listings with drone aerials consistently outperform ground-only shots for engagement and bookings.

I'm a Part 107 pilot based in Chesapeake. $225 gets 20 professional aerials per property. No contracts, pay per property.

As a Coldwell Banker franchise, you've got brand standards to maintain — the aerial photography quality matches that level.

I'd fly one of your Kitty Hawk properties free so you can see the quality before committing to anything.

Worth a conversation?

Adam Redler
Sentinel Aerial Inspections
https://sentinelaerialinspections.com/?utm_source=cold_email&utm_medium=email&utm_campaign=obx_vacation_q2_2026
"""},
    {"to": "info@kotarides.com", "subject": "roof inspections", "body": """Hi,

Kotarides manages 6,000+ apartment homes across Virginia and North Carolina. That's a massive portfolio of roofs and exteriors to inspect, and doing it by ladder takes time, carries liability, and doesn't scale.

I fly drone roof inspections across Hampton Roads. A single flight captures the entire roof surface in high-res imagery, plus a stitched orthomosaic you can measure from. Takes about 30 minutes per building on-site.

For a portfolio your size, this could replace a significant chunk of your manual inspection schedule — and the imagery doubles as documentation for insurance and capital planning.

I'd fly one of your buildings free so your maintenance team can evaluate it.

Worth exploring?

Adam Redler
Sentinel Aerial Inspections
https://sentinelaerialinspections.com/?utm_source=cold_email&utm_medium=email&utm_campaign=hr_property_mgmt_q2_2026
"""},
    {"to": "dale@roseandwomble.com", "subject": "property inspections", "body": """Dale,

Rose & Womble is the #1 firm in Hampton Roads, and Chandler PM manages 750+ residential properties. That volume of roof and exterior inspections is a constant — and doing them by ladder doesn't scale.

I fly drone inspections across Hampton Roads. Each flight captures the full roof and exterior in high-res imagery, plus an orthomosaic map your maintenance team can measure from. 30 minutes per property on-site.

For a portfolio your size, this could streamline your inspection workflow significantly. $225 per property, or volume pricing for recurring programs.

I'd fly one of your properties free so your team can evaluate the output.

Interested?

Adam Redler
Sentinel Aerial Inspections
https://sentinelaerialinspections.com/?utm_source=cold_email&utm_medium=email&utm_campaign=hr_property_mgmt_q2_2026
"""},
    {"to": "info@rwtowne.com", "subject": "listing photos", "body": """Hi,

With 15 offices across SE Virginia and NE North Carolina, RW Towne agents are listing properties across a wide footprint — and the ones that include drone aerials consistently get more engagement and sell faster.

I'm a Part 107 pilot in Chesapeake. I handle everything — scheduling, flight, editing — and deliver 20 professional aerials within 48 hours. $225 per property. No contracts.

For a brokerage your size, your agents could use this as a listing presentation differentiator. Most competing agents in Hampton Roads still aren't offering aerial.

I'd shoot one of your current listings free so your team can see the quality.

Worth a conversation?

Adam Redler
Sentinel Aerial Inspections
https://sentinelaerialinspections.com/?utm_source=cold_email&utm_medium=email&utm_campaign=hr_residential_q2_2026
"""},
    {"to": "tmrealty@tmrealty.com", "subject": "aerial photos — NE NC", "body": """Hi,

Taylor Mueller covers six counties from Elizabeth City — that's a lot of ground, and most listings in NE North Carolina don't have aerial photography because there aren't many drone pilots working the area.

I'm a Part 107 pilot based in Chesapeake, about an hour from your office. I'm actively flying NE North Carolina and have availability to cover properties from Currituck to Chowan.

For your rural, waterfront, and land listings especially, the aerial perspective sells what ground photos can't — lot boundaries, water access, acreage in context.

$225 for 20 edited aerials, delivered in 48 hours. I'd do the first one free so you can see if it works for your listings.

Worth trying?

Adam Redler
Sentinel Aerial Inspections
https://sentinelaerialinspections.com/?utm_source=cold_email&utm_medium=email&utm_campaign=ne_nc_inland_q2_2026
"""},
    {"to": "chris.todd@cbre.com", "subject": "commercial aerial", "body": """Chris,

CBRE's Hampton Roads office covers the full market — office, industrial, retail, investment sales. For commercial listings, the bird's-eye context is what buyers and tenants actually evaluate: parking capacity, access roads, neighboring tenants, lot utilization.

I'm a Part 107 drone pilot in Chesapeake producing commercial aerial photography and georeferenced orthomosaic maps across Hampton Roads. The ortho product overlays onto GIS tools and gives your team measurable site data without scheduling a visit.

Standard marketing aerials are $225. Full orthomosaic with GeoTIFF is $850.

I'd fly one of your current listings as a demo — no charge.

Worth exploring?

Adam Redler
Sentinel Aerial Inspections
https://sentinelaerialinspections.com/?utm_source=cold_email&utm_medium=email&utm_campaign=hr_commercial_q2_2026
"""},
    {"to": "chris.rouzie@thalhimer.com", "subject": "commercial aerial", "body": """Chris,

Thalhimer has 30+ broker professionals covering retail, office, industrial, and hospitality across Hampton Roads. For each of those property types, drone aerials give prospective tenants and buyers the site context they need — parking, ingress/egress, neighboring tenants, lot layout — without a site visit.

I'm a Part 107 drone pilot in Chesapeake. Standard marketing aerials are $225. For larger sites, I produce georeferenced orthomosaic maps ($850) that overlay onto GIS tools for measurable site analysis.

I'd fly one of your current Newport News or Virginia Beach listings as a demo — no charge.

Worth a look?

Adam Redler
Sentinel Aerial Inspections
https://sentinelaerialinspections.com/?utm_source=cold_email&utm_medium=email&utm_campaign=hr_commercial_q2_2026
"""},
    {"to": "information@naidominion.com", "subject": "commercial aerial", "body": """Hi,

NAI Dominion is headquartered right here in Hampton Roads with a global network behind it. For your local listings, drone aerial photography adds the site context that closes deals — parking, access, neighboring uses, lot utilization — all visible in one shot.

I'm a Part 107 drone pilot in Chesapeake producing commercial aerials and georeferenced orthomosaic maps. Standard aerials are $225. Full ortho with GeoTIFF for site analysis is $850.

For a firm with NAI's reach, the aerial deliverables integrate directly into your marketing packages and offering memorandums.

I'd fly one of your current listings as a demo — no charge.

Worth exploring?

Adam Redler
Sentinel Aerial Inspections
https://sentinelaerialinspections.com/?utm_source=cold_email&utm_medium=email&utm_campaign=hr_commercial_q2_2026
"""},
    {"to": "bspencer@midatlanticcommercial.com", "subject": "commercial aerial", "body": """Buddy,

Mid-Atlantic Commercial has been in the Virginia market for 40+ years with specialty teams across every CRE property type. That depth of experience means you know what sells — and for commercial listings, the aerial perspective shows site context that ground photos can't: parking ratios, access points, adjacencies, overall site layout.

I'm a Part 107 drone pilot in Chesapeake. Standard commercial aerials are $225. For larger sites, I produce georeferenced orthomosaic maps ($850) that overlay onto GIS tools for measurable site analysis.

I'd fly one of your current listings as a demo — no charge.

Worth a conversation?

Adam Redler
Sentinel Aerial Inspections
https://sentinelaerialinspections.com/?utm_source=cold_email&utm_medium=email&utm_campaign=hr_commercial_q2_2026
"""},
]


def now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def audit_append(event_dict):
    AUDIT_LOG.parent.mkdir(parents=True, exist_ok=True)
    # Emit schema_version as first line if file is new/empty
    if not AUDIT_LOG.exists() or AUDIT_LOG.stat().st_size == 0:
        first = {
            "ts": now_iso(),
            "event": "schema_version",
            "version": SCHEMA_VERSION,
            "agent": "email-processor",
            "canonicalization": "python-json-sort-keys",
            "hash_algo": "sha256",
            "hash_truncate": 16,
            "note": "written by one-shot tier1 sender, not Paula runtime",
        }
        with AUDIT_LOG.open("a", encoding="utf-8") as f:
            f.write(json.dumps(first) + "\n")
    with AUDIT_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event_dict) + "\n")


def arg_hash_simple(d):
    return hashlib.sha256(
        json.dumps(d, sort_keys=True, ensure_ascii=False).encode("utf-8")
    ).hexdigest()[:16]


def load_creds():
    with KEYS_PATH.open() as f:
        keys = json.load(f)["installed"]
    with CREDS_PATH.open() as f:
        tok = json.load(f)
    expiry = tok.get("expiry_date")
    creds = Credentials(
        token=tok["access_token"],
        refresh_token=tok["refresh_token"],
        token_uri=keys["token_uri"],
        client_id=keys["client_id"],
        client_secret=keys["client_secret"],
        scopes=tok.get("scope", "").split() if isinstance(tok.get("scope"), str) else tok.get("scope"),
    )
    if not creds.valid:
        creds.refresh(Request())
    return creds


def send_one(service, to, subject, body):
    msg = MIMEText(body, "plain", "utf-8")
    msg["to"] = to
    msg["from"] = "dradamopierce@gmail.com"
    msg["subject"] = subject
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode("utf-8")
    resp = service.users().messages().send(
        userId="me", body={"raw": raw}
    ).execute()
    return resp


def main():
    print(f"RUN_ID: {RUN_ID}")
    print(f"AUDIT_LOG: {AUDIT_LOG}")
    print(f"EMAILS: {len(EMAILS)}")

    # Pre-run override acknowledgement event
    audit_append({
        "ts": now_iso(),
        "event": "owner_override_invoked",
        "risk_id": "RISK-2026-04-13-001",
        "adr": "ADR-008",
        "run_id": RUN_ID,
        "batch": "tier1-monday-2026-04-13",
        "email_count": len(EMAILS),
        "notes": "Adam directed send; CISO draft-only rule overridden for this batch only.",
    })

    creds = load_creds()
    service = build("gmail", "v1", credentials=creds)

    # Resume from where the first run crashed: email #1 to Twiddy already sent
    # (msgId 19d8858bd4084089). Skip it to avoid duplicate.
    start_index = int(os.environ.get("TIER1_START", "2"))

    results = []
    for i, email in enumerate(EMAILS, 1):
        if i < start_index:
            print(f"[{i:2d}/14] -- SKIPPED (already sent in prior run) -- {email['to']}")
            continue
        arg = {"to": email["to"], "subject": email["subject"], "body_sha256": hashlib.sha256(email["body"].encode("utf-8")).hexdigest()[:16]}
        try:
            resp = send_one(service, email["to"], email["subject"], email["body"])
            evt = {
                "ts": now_iso(),
                "event": "gmail_send",
                "run_id": RUN_ID,
                "sequence": i,
                "to": email["to"],
                "subject": email["subject"],
                "messageId": resp.get("id"),
                "threadId": resp.get("threadId"),
                "arg_hash": arg_hash_simple(arg),
                "labelIds": resp.get("labelIds", []),
            }
            audit_append(evt)
            results.append({"i": i, "to": email["to"], "ok": True, "messageId": resp.get("id"), "threadId": resp.get("threadId")})
            print(f"[{i:2d}/14] ✓ {email['to']:40s} msgId={resp.get('id')}")
        except HttpError as e:
            err_class = type(e).__name__
            audit_append({
                "ts": now_iso(),
                "event": "gmail_send_failed",
                "run_id": RUN_ID,
                "sequence": i,
                "to": email["to"],
                "subject": email["subject"],
                "error": err_class,
                "error_detail": str(e)[:200],
                "arg_hash": arg_hash_simple(arg),
            })
            results.append({"i": i, "to": email["to"], "ok": False, "error": str(e)[:200]})
            print(f"[{i:2d}/14] ✗ {email['to']:40s} ERROR: {e}")

    # Batch summary event
    audit_append({
        "ts": now_iso(),
        "event": "batch_complete",
        "run_id": RUN_ID,
        "batch": "tier1-monday-2026-04-13",
        "sent_ok": sum(1 for r in results if r["ok"]),
        "sent_failed": sum(1 for r in results if not r["ok"]),
    })

    # Write summary JSON for COO follow-up
    summary_path = Path(os.path.expanduser("~")) / "agent-office-audit" / f"tier1-send-summary-{RUN_ID}.json"
    with summary_path.open("w", encoding="utf-8") as f:
        json.dump({"run_id": RUN_ID, "results": results}, f, indent=2)
    print(f"\nSUMMARY: {summary_path}")
    return 0 if all(r["ok"] for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())
