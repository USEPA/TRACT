## Known issues

- Distrubted .exe loads v. slowly.
- New file can only be created as the first action, not
  after an existing file has been loaded.
- Data file name *must* end in .xlsx, but not enforced.
- No way to un-link incorrectly linked (related) images other
  than editing .xlsx file directly.
- Having to resize the feedback panel everytime.
- Distributed .exe is large.

## dev notes

```shell
python -m venv venv_monexif
. venv_monexif/bin/activate
pip install -r requirements.txt
# see pre-commit
mkdir -p .git/hooks; cp pre-commit .git/hooks; chmod +x .git/hooks/pre-commit
```

