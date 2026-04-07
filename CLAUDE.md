# GenSheet VCE — Claude Code Notes

## Python environment

Always use the project venv for all Python commands (install, run, test):

```bash
source venv/bin/activate && <command>
# or
venv/bin/python ...
venv/bin/uvicorn ...
venv/bin/pip ...
```

Never run `pip install` or `python` without activating the venv first.
