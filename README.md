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
