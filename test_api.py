#!/usr/bin/env python3
"""Simple smoke test for the FastAPI backend."""

import json
import urllib.request

API_URL = "http://127.0.0.1:8000/api/query"
PAYLOAD = {"query": "Show me the non-compete clause", "stream": False}


def main() -> None:
    request = urllib.request.Request(
        API_URL,
        data=json.dumps(PAYLOAD).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with urllib.request.urlopen(request, timeout=30) as response:
        body = response.read().decode("utf-8")
        data = json.loads(body)

    print(f"Status: {response.status}")
    print("Keys:", ", ".join(sorted(data.keys())))

    if data.get("results"):
        first = data["results"][0]
        document = first.get("document") or {}
        chunk = first.get("chunk") or {}
        print("\nTop Result")
        print(f"  Document: {document.get('title') or document.get('file_path')}")
        print(f"  Section : {chunk.get('section_title', 'N/A')}")
        preview = (chunk.get("text") or "")[:160].replace("\n", " ")
        print(f"  Preview : {preview}...")
    else:
        print("\nNo results returned. Make sure documents are indexed.")


if __name__ == "__main__":
    main()
