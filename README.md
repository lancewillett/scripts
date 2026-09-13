# scripts

A collection of generic development utility scripts.

## Scripts

### git-pull-all.sh
Pulls updates from all git repositories in subdirectories.

```bash
./git-pull-all.sh
```

### git.sh
Git workflow reference covering common operations:
- Rebase to keep branches updated
- Squash commits before merging
- Co-author commits with collaborators
- Sync forks with upstream
- Word diffs for reviewing changes

### cli.sh
Simple CLI utilities:
- SHA-256 checksum generation

### tumblr-followers.py
Prints follower counts for the Tumblr blogs you own, using the Tumblr API with OAuth2. Credentials live in the macOS Keychain.

```bash
# One time: register an app at https://www.tumblr.com/oauth/apps
# with redirect URL http://localhost:8765/callback, then:
./tumblr-followers.py setup

# Every blog on the account, or one blog's count
./tumblr-followers.py
./tumblr-followers.py myblog
```

### strava-followers.py
Prints your Strava follower count, using the Strava API with OAuth2. Credentials live in the macOS Keychain.

```bash
# One time: create an app at https://www.strava.com/settings/api
# with Authorization Callback Domain set to localhost, then:
./strava-followers.py setup

# Follower count, or followers and following
./strava-followers.py
./strava-followers.py --following
```

## Usage

These are primarily reference files. Copy commands as needed, or source them:

```bash
# View available commands
cat git.sh

# Generate a checksum
openssl sha1 -sha256 myfile.txt
```

## License

GPL v3 - See [LICENSE](LICENSE) for details.
