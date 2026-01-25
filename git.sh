## Git Workflow Reference

## Rebase to keep working in local branch
git checkout main
git pull
git checkout -
git rebase main

# create new branch
git checkout -b <your-branch-name>
git status
git diff

# Add the files and commit the changes on your local branch:

git add file.php
git commit -m "Describe the changes here"

# Push
git push --set-upstream origin <your-branch-name>
# go to GitHub to create the PR

# keep branch updated, especially if stale
# switch to branch
git pull # make sure updated
git rebase main # solve on your side any conflicts that may arise here
git push --force-with-lease # update your PR if needed



# https://themejanitor.wordpress.com/2012/02/04/github-setup-for-_s/
# http://git.or.cz/course/svn.html
# random!
# http://git-man-page-generator.lokaltog.net/ via Jack


# switching branches a lot
https://coreappso2.wordpress.com/2015/05/12/if-you-switch-branches-a-lot/

# fixing things
https://sethrobertson.github.io/GitFixUm/fixup.html
https://git-scm.com/blog/2010/03/02/undoing-merges.html

# Remote URL
git remote -v

# Remote branches
git branch -r

# Remove old branches
git fetch -p
git pull -p

# to avoid the merge clean thing
# Drew says
# It's the way Git merges without a clean history
# To avoid it:
# 1. Always pull before you start work
# 2. If you know commits are going in while you're working: Before you commit, stash your changes, pull, and then re-apply.
# Example:
# work, work, work
# (I know Drew is pushing commits). OK, I'm ready to commit
git stash
# This "stashes" away all your work and goes back to a clean tree
git pull
# This pulls in any work that's been pushed
git stash pop
# This re-applies my changes to the new tree, and no merge is required

# reset last change
git reset HEAD~1

# undo local changes to catch up and reset local master
git reset --hard origin/main

# keep my fork up to date
# Fetch any new changes from the original repository
# might have do this first: https://help.github.com/articles/configuring-a-remote-for-a-fork
# https://help.github.com/articles/fork-a-repo
git fetch upstream -p
# or origin, depending on the name

# Merge any changes fetched into your working files
git merge upstream/main
# or origin, depending on the name

# revert local changes
git checkout .

# switch branch
git checkout main

# make a git patch w/o the a/b stuff at the top
git diff --no-prefix

# amend the last commit
git commit --amend [options]
git commit --amend --author "Your Name <you@example.com>"
# then, edit the file, save it (vim)
# then, push
git push -f

# do a pull request
# fork the repo, and git clone it to local
# make fixes
git commit -am 'My fix'
# then via website make the pull request
https://help.github.com/articles/creating-a-pull-request

# word diff
git diff --word-diff
# word diff
git -c color.diff.old='white red bold' -c color.diff.new='black green bold' diff --no-index --color-words=. --no-prefix
# The extra -c flags colorize the diffs to make them a little easier to read in my terminal's color scheme.

# delete merged branches
git branch --merged | grep -v "\*" | xargs -n 1 git branch -d

# rebase and squash
# Make sure main is up to date.
git pull -p
# In branch...
git rebase -i main
# this opens an editor
# pick the commits to keep, change pick to squash or just delete lines (edit commit msg if needed)
# for example, change prefix for all but first item to "fixup"
# save the file
git push --force-with-lease
# to force the history rewrite

## See also https://codep2.wordpress.com/2020/05/05/fixing-local-git-branches-after-the-remote-was-rebased/

## For OSS contributions
git fetch origin
# don't use the -i (interactive mode)
git rebase origin/main
git push --force-with-lease

# Git branches from remote
# https://hub.github.com/

# check out a pull request for review
$ hub checkout https://github.com/owner/repo/pull/1337
# → (creates a new branch with the contents of the pull request)
# https://codemebaby.wordpress.com/2016/04/26/github-magic-checking-out-pull-requests/
# Co-author with contributor? Use:
# https://github.blog/2018-01-29-commit-together-with-co-authors/

# Include your trailers at the end of your commit message, and have at least one line of white space before them.
# start
<Commit message here, keep the extra line after>

Co-authored-by: Name <email@example.com>
# end
