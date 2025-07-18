# Check and pull inside all git repos
function check_pull {
    if [ -d ".git" ]; then
        echo "Pulling updates in $(pwd)..."
        git pull -p
    else
        echo "$(pwd) is not a git repository."
    fi
}

# Check immediate subdirs
function check_subdirs {
    for dir in */; do
        cd "$dir" || continue
        check_pull
        cd .. || exit
    done
}

# Start checking from the current directory
check_subdirs
