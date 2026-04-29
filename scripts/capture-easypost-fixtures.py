#!/usr/bin/env python3
"""Capture shipping fixtures for enablements-api.

This script is intentionally offline-only for fixture maintenance. Runtime workshop
code must use enablements-api and must not call EasyPost directly.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any


DEFAULT_OUTPUT = Path(
    "java/enablements/enablements-api/src/main/resources/fixtures/shipping-fixtures.json"
)


@dataclass(frozen=True)
class AddressSeed:
    id: str
    street1: str
    city: str
    state: str
    zip: str
    country: str = "US"
    company: str = ""
    residential: bool = False


WAREHOUSES = [
    {
        "warehouse_id": "WH-EAST-01",
        "address_id": "adr_wh_east_01",
        "sku_prefixes": ["ELEC-", "GADG-", "TECH-"],
    },
    {
        "warehouse_id": "WH-WEST-01",
        "address_id": "adr_wh_west_01",
        "sku_prefixes": ["APRL-", "HOME-", "SPRT-"],
    },
    {
        "warehouse_id": "WH-EAST-02",
        "address_id": "adr_wh_east_02",
        "sku_prefixes": ["ELEC-", "GADG-"],
    },
    {
        "warehouse_id": "WH-WEST-02",
        "address_id": "adr_wh_west_02",
        "sku_prefixes": ["APRL-", "SPRT-"],
    },
    {
        "warehouse_id": "WH-CENT-01",
        "address_id": "adr_wh_cent_01",
        "sku_prefixes": ["TECH-", "HOME-"],
    },
]


ADDRESS_SEEDS = [
    AddressSeed("adr_wh_east_01", "540 Broad St", "Newark", "NJ", "07102", company="acme"),
    AddressSeed("adr_wh_west_01", "388 Townsend St", "San Francisco", "CA", "94107", company="acme"),
    AddressSeed("adr_wh_east_02", "417 Montgomery St", "San Francisco", "CA", "94104", company="acme"),
    AddressSeed("adr_wh_west_02", "1600 Amphitheatre Pkwy", "Mountain View", "CA", "94043", company="acme"),
    AddressSeed("adr_wh_cent_01", "1901 W Madison St", "Chicago", "IL", "60612", company="acme"),
    AddressSeed("adr_dest_nyc_01", "11 Wall St", "New York", "NY", "10005"),
    AddressSeed("adr_dest_boston_01", "1 Cambridge Center", "Cambridge", "MA", "02142"),
    AddressSeed("adr_dest_austin_01", "301 Congress Ave", "Austin", "TX", "78701"),
    AddressSeed("adr_dest_denver_01", "1600 Broadway", "Denver", "CO", "80202"),
    AddressSeed("adr_dest_seattle_01", "401 5th Ave", "Seattle", "WA", "98104"),
    AddressSeed("adr_dest_miami_01", "1111 Lincoln Rd", "Miami Beach", "FL", "33139"),
    AddressSeed("adr_dest_los_angeles_01", "200 N Spring St", "Los Angeles", "CA", "90012"),
    AddressSeed("adr_dest_phoenix_01", "400 E Van Buren St", "Phoenix", "AZ", "85004"),
    AddressSeed("adr_dest_atlanta_01", "600 Peachtree St NE", "Atlanta", "GA", "30308"),
    AddressSeed("adr_dest_portland_01", "1120 SW 5th Ave", "Portland", "OR", "97204"),
]


ROUTES = [
    ("adr_wh_east_01", "adr_dest_nyc_01"),
    ("adr_wh_east_02", "adr_dest_nyc_01"),
    ("adr_wh_west_01", "adr_dest_nyc_01"),
    ("adr_wh_west_02", "adr_dest_nyc_01"),
    ("adr_wh_cent_01", "adr_dest_nyc_01"),
    ("adr_wh_east_01", "adr_dest_boston_01"),
    ("adr_wh_east_01", "adr_dest_austin_01"),
    ("adr_wh_east_01", "adr_dest_denver_01"),
    ("adr_wh_west_01", "adr_dest_seattle_01"),
    ("adr_wh_west_01", "adr_dest_los_angeles_01"),
    ("adr_wh_cent_01", "adr_dest_atlanta_01"),
]


PARCEL = {"weight": 16, "length": 6, "width": 6, "height": 4}
PARCEL_FIXTURE = {"weight_oz": 16, "length_in": 6, "width_in": 6, "height_in": 4}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--api-key", default=os.environ.get("EASYPOST_API_KEY", ""))
    args = parser.parse_args()

    if not args.api_key:
        raise SystemExit("EASYPOST_API_KEY or --api-key is required for offline fixture capture")

    import easypost  # type: ignore

    client = easypost.EasyPostClient(args.api_key)

    verified_by_fixture_id = {
        seed.id: verify_address(client, seed)
        for seed in ADDRESS_SEEDS
    }

    shipments = [
        capture_shipment(client, verified_by_fixture_id, from_id, to_id)
        for from_id, to_id in ROUTES
    ]

    fixture = {
        "addresses": list(verified_by_fixture_id.values()),
        "warehouses": WAREHOUSES,
        "shipments": shipments,
        "location_events": {"mode": "empty", "seeds": []},
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(fixture, indent=2) + "\n", encoding="utf-8")


def verify_address(client: Any, seed: AddressSeed) -> dict[str, Any]:
    verified = client.address.create_and_verify(
        street1=seed.street1,
        city=seed.city,
        state=seed.state,
        zip=seed.zip,
        country=seed.country,
        company=seed.company or None,
    )
    fixture = {
        "id": seed.id,
        "street1": getattr(verified, "street1", None) or seed.street1,
        "city": getattr(verified, "city", None) or seed.city,
        "state": getattr(verified, "state", None) or seed.state,
        "zip": getattr(verified, "zip", None) or seed.zip,
        "country": getattr(verified, "country", None) or seed.country,
        "residential": bool(getattr(verified, "residential", seed.residential)),
    }
    if seed.company:
        fixture["company"] = seed.company
    coordinate = extract_coordinate(verified)
    if coordinate:
        fixture["coordinate"] = coordinate
    timezone = extract_timezone(verified)
    if timezone:
        fixture["timezone"] = timezone
    fixture["_captured_easypost_id"] = verified.id
    return fixture


def capture_shipment(
    client: Any,
    addresses: dict[str, dict[str, Any]],
    from_fixture_id: str,
    to_fixture_id: str,
) -> dict[str, Any]:
    shipment = client.shipment.create(
        from_address={"id": addresses[from_fixture_id]["_captured_easypost_id"]},
        to_address={"id": addresses[to_fixture_id]["_captured_easypost_id"]},
        parcel=PARCEL,
    )
    shipment_id = f"shp_{from_fixture_id}_to_{to_fixture_id}"
    rates = [rate_fixture(from_fixture_id, to_fixture_id, rate) for rate in getattr(shipment, "rates", [])]
    return {
        "shipment_id": shipment_id,
        "from_address_id": from_fixture_id,
        "to_address_id": to_fixture_id,
        "parcel": PARCEL_FIXTURE,
        "rates": rates,
        "labels": [label_fixture(shipment_id, rate["rate_id"]) for rate in rates],
    }


def rate_fixture(from_fixture_id: str, to_fixture_id: str, rate: Any) -> dict[str, Any]:
    carrier = str(getattr(rate, "carrier", "carrier")).lower().replace(" ", "_")
    service = str(getattr(rate, "service", "service")).lower().replace(" ", "_")
    suffix = stable_suffix(f"{from_fixture_id}:{to_fixture_id}:{carrier}:{service}")
    cost_units = int(float(getattr(rate, "rate", "0") or 0) * 100)
    days = int(getattr(rate, "est_delivery_days", 0) or 0)
    return {
        "rate_id": f"rate_{carrier}_{service}_{suffix}",
        "carrier": getattr(rate, "carrier", ""),
        "service_level": getattr(rate, "service", ""),
        "cost": {"currency": getattr(rate, "currency", "USD") or "USD", "units": cost_units},
        "estimated_days": days,
        "delivery_days": days,
        "_captured_easypost_rate_id": getattr(rate, "id", ""),
    }


def label_fixture(shipment_id: str, rate_id: str) -> dict[str, str]:
    digest = stable_suffix(f"{shipment_id}:{rate_id}", length=16).upper()
    return {
        "rate_id": rate_id,
        "source": "synthetic",
        "tracking_number": f"1ZFIXTURE{digest}",
        "label_url": f"https://example.invalid/labels/{shipment_id}/{rate_id}.pdf",
    }


def extract_coordinate(address: Any) -> dict[str, float] | None:
    lat = getattr(address, "latitude", None)
    lng = getattr(address, "longitude", None)
    if lat is None:
        verifications = getattr(address, "verifications", None)
        for key in ("delivery", "zip4"):
            details = getattr(getattr(verifications, key, None), "details", None)
            if details and getattr(details, "latitude", None) is not None:
                lat = getattr(details, "latitude")
                lng = getattr(details, "longitude", None)
                break
    if lat is None:
        return None
    return {"latitude": float(lat), "longitude": float(lng or 0.0)}


def extract_timezone(address: Any) -> str:
    verifications = getattr(address, "verifications", None)
    for key in ("delivery", "zip4"):
        details = getattr(getattr(verifications, key, None), "details", None)
        if details and getattr(details, "time_zone", None):
            return str(getattr(details, "time_zone"))
    return ""


def stable_suffix(value: str, length: int = 8) -> str:
    return hashlib.sha256(value.encode()).hexdigest()[:length]


if __name__ == "__main__":
    main()
