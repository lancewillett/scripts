#!/usr/bin/env python3
"""Print your Strava follower count, via the Strava API (OAuth2).

One-time setup:
  1. Create an app at https://www.strava.com/settings/api and set its
     Authorization Callback Domain to localhost
  2. ./strava-followers.py setup
     Prompts for the app's Client ID and Client Secret, opens Strava to approve
     access, and stores the credentials in the macOS Keychain.

Usage:
  ./strava-followers.py              # follower count, number only
  ./strava-followers.py --following  # also print the following count
  ./strava-followers.py setup [--redirect-uri URI]

Requires macOS (Keychain via /usr/bin/security) and Python 3.8+. No extra packages.
"""

import argparse
import getpass
import http.server
import json
import secrets
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
import webbrowser

SERVICE = "strava-followers"
AUTHORIZE_URL = "https://www.strava.com/oauth/authorize"
TOKEN_URL = "https://www.strava.com/oauth/token"
ATHLETE_URL = "https://www.strava.com/api/v3/athlete"
SCOPE = "read,profile:read_all"
DEFAULT_REDIRECT_URI = "http://localhost:8765/callback"


def keychain_get(account):
    result = subprocess.run(
        ["security", "find-generic-password", "-s", SERVICE, "-a", account, "-w"],
        capture_output=True,
        text=True,
    )
    return result.stdout.strip() if result.returncode == 0 else None


def keychain_set(account, value):
    # Sent over stdin so the secret never appears in the process list.
    command = f'add-generic-password -U -s {SERVICE} -a {account} -w "{value}"\n'
    result = subprocess.run(["security", "-i"], input=command, capture_output=True, text=True)
    if result.returncode != 0 or "error" in result.stderr.lower():
        sys.exit(f"Could not save {account} to the Keychain.")


def post_form(url, fields):
    data = urllib.parse.urlencode(fields).encode()
    request = urllib.request.Request(url, data=data, method="POST")
    request.add_header("User-Agent", SERVICE)
    try:
        with urllib.request.urlopen(request) as response:
            return json.load(response)
    except urllib.error.HTTPError as error:
        detail = json.loads(error.read() or b"{}").get("message", "")
        sys.exit(f"Strava returned HTTP {error.code}: {detail}. Run setup again if this persists.")


def get_json(url, access_token):
    request = urllib.request.Request(url)
    request.add_header("Authorization", f"Bearer {access_token}")
    request.add_header("User-Agent", SERVICE)
    try:
        with urllib.request.urlopen(request) as response:
            return json.load(response)
    except urllib.error.HTTPError as error:
        body = error.read().decode(errors="replace")
        try:
            detail = json.loads(body)
        except ValueError:
            detail = body[:300]
        sys.exit(f"Strava returned HTTP {error.code} from {url}: {detail}")


def wait_for_redirect(redirect_uri):
    parsed = urllib.parse.urlparse(redirect_uri)
    captured = {}

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            url = urllib.parse.urlparse(self.path)
            if url.path != parsed.path:
                self.send_response(404)
                self.end_headers()
                return
            captured.update(urllib.parse.parse_qs(url.query))
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"Done. You can close this tab and return to the terminal.")

        def log_message(self, *args):
            pass

    server = http.server.HTTPServer((parsed.hostname, parsed.port or 80), Handler)
    while not captured:
        server.handle_request()
    server.server_close()
    return captured


def setup(redirect_uri):
    client_id = input("Strava Client ID: ").strip()
    client_secret = getpass.getpass("Strava Client Secret (hidden): ").strip()
    if not client_id or not client_secret:
        sys.exit("Both the Client ID and Client Secret are required.")

    state = secrets.token_urlsafe(16)
    authorize = AUTHORIZE_URL + "?" + urllib.parse.urlencode(
        {
            "client_id": client_id,
            "response_type": "code",
            "redirect_uri": redirect_uri,
            "approval_prompt": "auto",
            "scope": SCOPE,
            "state": state,
        }
    )
    print(f"\nApprove access in your browser. If it does not open, visit:\n{authorize}\n")
    webbrowser.open(authorize)
    params = wait_for_redirect(redirect_uri)

    if params.get("state", [None])[0] != state:
        sys.exit("State mismatch; aborting. Run setup again.")
    if "error" in params:
        sys.exit(f"Strava denied access: {params['error'][0]}")
    if "profile:read_all" not in params.get("scope", [""])[0]:
        sys.exit("Follower counts need the 'View data about your private profile' box checked. Run setup again.")

    tokens = post_form(
        TOKEN_URL,
        {
            "grant_type": "authorization_code",
            "code": params["code"][0],
            "client_id": client_id,
            "client_secret": client_secret,
        },
    )

    keychain_set("client_id", client_id)
    keychain_set("client_secret", client_secret)
    keychain_set("refresh_token", tokens["refresh_token"])
    print("Saved to the macOS Keychain. Run the script again to see your follower count.")


def fresh_access_token():
    client_id = keychain_get("client_id")
    client_secret = keychain_get("client_secret")
    refresh_token = keychain_get("refresh_token")
    if not (client_id and client_secret and refresh_token):
        sys.exit("No saved credentials. Run: ./strava-followers.py setup")

    tokens = post_form(
        TOKEN_URL,
        {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": client_id,
            "client_secret": client_secret,
        },
    )
    # Strava may issue a new refresh token on any refresh.
    keychain_set("refresh_token", tokens["refresh_token"])
    return tokens["access_token"]


def followers(show_following):
    athlete = get_json(ATHLETE_URL, fresh_access_token())
    if "follower_count" not in athlete:
        sys.exit("Strava did not return a follower count; run setup again and allow private profile access.")
    if show_following:
        print(f"followers\t{athlete['follower_count']}")
        print(f"following\t{athlete.get('friend_count', 'n/a')}")
    else:
        print(athlete["follower_count"])


def main():
    parser = argparse.ArgumentParser(
        description="Print your Strava follower count.",
        epilog="Run 'setup' first. See the top of this file for details.",
    )
    parser.add_argument("command", nargs="?", choices=["setup"], help="'setup' to authorize")
    parser.add_argument("--following", action="store_true", help="also print the following count")
    parser.add_argument("--redirect-uri", default=DEFAULT_REDIRECT_URI, help="OAuth2 redirect URL used in setup")
    args = parser.parse_args()

    if args.command == "setup":
        setup(args.redirect_uri)
    else:
        followers(args.following)


if __name__ == "__main__":
    main()
