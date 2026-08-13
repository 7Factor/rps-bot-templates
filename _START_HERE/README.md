# Start here

This is the short version: choose a language, make your Team branch, edit one
strategy file, test it, and push your branch.

Run every command below from the top of this repository.

## 1. See the available languages

```sh
./_START_HERE/start-team-template.sh --list
```

## 2. Start your Team branch

Pick a short lowercase Team name. Replace `python` and `red-rockets` in this
example with your language and Team name:

```sh
./_START_HERE/start-team-template.sh --language python --team red-rockets
```

The script does two important things for you:

1. It creates and checks out a branch named `team/red-rockets`.
2. It creates `team-submission.json`, which records your language choice.

Do not delete or edit `team-submission.json` by hand.

## 3. Edit your strategy

The start script prints the exact strategy file your Team should edit. For
Python, that file is:

```text
templates/python/team_source/strategy.py
```

Other languages have their own file under `templates/<language>/team_source/`.
Only change files inside your language's `team_source` directory. The script
also prints the path to your language's guide if you need more detail.

## 4. Test locally

Start Docker, then run:

```sh
./_START_HERE/test-team-template.sh
```

This runs the repository's official Docker check and Advisory Validation for
the language recorded in `team-submission.json`. Local validation needs Docker
and Python 3 because the repository's official validation commands are written
in Python.

If you expect unreliable Wi-Fi, download every pinned Docker image while you
are still online:

```sh
./_START_HERE/prepare-team-laptop.sh
```

You normally do not need that extra step; the test script pulls missing pinned
images when needed.

## 5. Commit and push your Team branch

First, check which files changed:

```sh
git status
```

Add `team-submission.json` and your language's `team_source` directory. For
Python:

```sh
git add team-submission.json templates/python/team_source
git commit -m "Add red-rockets strategy"
git push -u origin team/red-rockets
```

Replace `python` and `red-rockets` with your language and Team name. After the
first push, later changes can be pushed with just `git push`.
