#!/usr/bin/env python3
"""Print follower counts for the Tumblr blogs you own, via the Tumblr API (OAuth2).

One-time setup:
  1. Register an app at https://www.tumblr.com/oauth/apps and set its
     OAuth2 redirect URL to http://localhost:8765/callback
  2. ./tumblr-followers.py setup
     Prompts for the app's consumer key and secret, opens Tumblr to approve
     access, and stores the credentials in the macOS Keychain.

Usage:
  ./tumblr-followers.py              # every blog on the account, tab-separated
  ./tumblr-followers.py myblog       # one blog's count, number only
  ./tumblr-followers.py setup [--redirect-uri URI]

If your app uses a non-localhost redirect URL, pass it with --redirect-uri and
paste the URL Tumblr sends you to when prompted.

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

SERVICE = "tumblr-followers"
AUTHORIZE_URL = "https://www.tumblr.com/oauth2/authorize"
TOKEN_URL = "https://api.tumblr.com/v2/oauth2/token"
USER_INFO_URL = "https://api.tumblr.com/v2/user/info"
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
        detail = json.loads(error.read() or b"{}").get("error_description", "")
        sys.exit(f"Tumblr returned HTTP {error.code}: {detail}. Run setup again if this persists.")


def get_json(url, access_token):
    request = urllib.request.Request(url)
    request.add_header("Authorization", f"Bearer {access_token}")
    request.add_header("User-Agent", SERVICE)
    try:
        with urllib.request.urlopen(request) as response:
            return json.load(response)
    except urllib.error.HTTPError as error:
        sys.exit(f"Tumblr returned HTTP {error.code} from {url}.")


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
    client_id = input("Tumblr OAuth consumer key: ").strip()
    client_secret = getpass.getpass("Tumblr OAuth consumer secret (hidden): ").strip()
    if not client_id or not client_secret:
        sys.exit("Both the consumer key and secret are required.")

    state = secrets.token_urlsafe(16)
    authorize = AUTHORIZE_URL + "?" + urllib.parse.urlencode(
        {
            "client_id": client_id,
            "response_type": "code",
            "scope": "basic offline_access",
            "state": state,
            "redirect_uri": redirect_uri,
        }
    )
    print(f"\nApprove access in your browser. If it does not open, visit:\n{authorize}\n")
    webbrowser.open(authorize)

    if urllib.parse.urlparse(redirect_uri).hostname in ("localhost", "127.0.0.1"):
        params = wait_for_redirect(redirect_uri)
    else:
        pasted = input("Paste the full URL Tumblr redirected you to: ").strip()
        params = urllib.parse.parse_qs(urllib.parse.urlparse(pasted).query)

    if params.get("state", [None])[0] != state:
        sys.exit("State mismatch; aborting. Run setup again.")
    if "error" in params:
        sys.exit(f"Tumblr denied access: {params['error'][0]}")

    tokens = post_form(
        TOKEN_URL,
        {
            "grant_type": "authorization_code",
            "code": params["code"][0],
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": redirect_uri,
        },
    )
    if "refresh_token" not in tokens:
        sys.exit("Tumblr did not return a refresh token; check the app allows offline_access.")

    keychain_set("client_id", client_id)
    keychain_set("client_secret", client_secret)
    keychain_set("refresh_token", tokens["refresh_token"])
    print("Saved to the macOS Keychain. Run the script again to see follower counts.")


def fresh_access_token():
    client_id = keychain_get("client_id")
    client_secret = keychain_get("client_secret")
    refresh_token = keychain_get("refresh_token")
    if not (client_id and client_secret and refresh_token):
        sys.exit("No saved credentials. Run: ./tumblr-followers.py setup")

    tokens = post_form(
        TOKEN_URL,
        {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": client_id,
            "client_secret": client_secret,
        },
    )
    # Tumblr rotates the refresh token on every use.
    keychain_set("refresh_token", tokens["refresh_token"])
    return tokens["access_token"]


def followers(blog):
    blogs = get_json(USER_INFO_URL, fresh_access_token())["response"]["user"]["blogs"]
    if blog:
        match = next((b for b in blogs if b["name"] == blog), None)
        if not match:
            sys.exit(f"No blog named '{blog}' on this account.")
        print(match.get("followers", "n/a"))
        return
    for b in blogs:
        print(f"{b['name']}\t{b.get('followers', 'n/a')}")


def main():
    parser = argparse.ArgumentParser(
        description="Print follower counts for the Tumblr blogs you own.",
        epilog="Run 'setup' first. See the top of this file for details.",
    )
    parser.add_argument("blog", nargs="?", help="blog name, or 'setup' to authorize")
    parser.add_argument("--redirect-uri", default=DEFAULT_REDIRECT_URI, help="OAuth2 redirect URL used in setup")
    args = parser.parse_args()

    if args.blog == "setup":
        setup(args.redirect_uri)
    else:
        followers(args.blog)


if __name__ == "__main__":
    main()
