#!/usr/bin/env python3
"""Nebius Token Factory Smoke Test & Model Discovery Script.

Usage:
    python scripts/smoke_nebius.py

This script reads your local gitignored .env configuration, checks account
authentication against Nebius Token Factory, lists active models, and executes
a lightweight smoke test across Nemotron tiers.
"""
# ruff: noqa: BLE001
# pyright: reportMissingImports=false
import asyncio
import os
import sys

# Ensure backend package is in python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

import importlib

import httpx

# Dynamically import backend modules after sys.path is configured
_app_config = importlib.import_module("app.core.config")
_app_client = importlib.import_module("app.inference.client")
_app_router = importlib.import_module("app.inference.router")

settings = _app_config.settings
NebiusTokenFactoryClient = _app_client.NebiusTokenFactoryClient
Tier = _app_router.Tier
model_router = _app_router.model_router


async def run_smoke_test():
    print("=" * 60)
    print("ClaimGuard — Nebius Token Factory Smoke Test")
    print("=" * 60)

    if not settings.INFERENCE_ENABLED:
        print("[!] Note: INFERENCE_ENABLED is currently set to False in .env")
        print("    To run live inference, set INFERENCE_ENABLED=true in .env")
        return

    if not settings.NEBIUS_API_KEY or not settings.NEBIUS_API_KEY.get_secret_value().strip():
        print("[!] Error: NEBIUS_API_KEY is missing or empty in .env.")
        print("    Please set NEBIUS_API_KEY=<your-key> in your .env file.")
        return

    key = settings.NEBIUS_API_KEY.get_secret_value()
    base_url = settings.NEBIUS_BASE_URL.rstrip("/")

    print(f"[*] Base URL: {base_url}")
    print("[*] Verifying connectivity and listing available models...")

    headers = {
        "Authorization": f"Bearer {key}",
        "Accept": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(f"{base_url}/models", headers=headers)

        if resp.status_code == 200:
            models_data = resp.json().get("data", [])
            print(f"[+] Authentication successful! Found {len(models_data)} models.")
            print("[*] Active Models on Account:")
            for m in models_data[:10]:
                print(f"    - {m.get('id')}")
            if len(models_data) > 10:
                print(f"    ... and {len(models_data) - 10} more.")
        else:
            print(f"[-] Authentication failed with status {resp.status_code}: {resp.text}")
            return
    except Exception as e:
        print(f"[-] Network error connecting to Nebius: {e}")
        return

    print("\n[*] Testing Chat Completion across Nemotron Tiers:")
    client = NebiusTokenFactoryClient()

    for tier in [Tier.NANO, Tier.SUPER, Tier.ULTRA]:
        model_id = model_router.resolve_model(tier)
        print(f"\n[*] Probing {tier.value.upper()} tier (model: {model_id})...")
        try:
            start_t = asyncio.get_event_loop().time()
            res = await client.chat_completion(
                messages=[{"role": "user", "content": "Respond with the single word 'READY'."}],
                model=model_id,
                temperature=0.0,
                max_tokens=10,
            )
            elapsed = (asyncio.get_event_loop().time() - start_t) * 1000
            content = res["choices"][0]["message"]["content"].strip()
            usage = res.get("usage", {})
            print(
                f"    [+] Success! Latency: {elapsed:.1f}ms | Output: {content!r} | Tokens: {usage.get('total_tokens')}"
            )
        except Exception as tier_err:
            print(f"    [-] Tier {tier.value.upper()} returned error: {tier_err}")

    print("\n[+] Smoke test completed.")


if __name__ == "__main__":
    asyncio.run(run_smoke_test())
