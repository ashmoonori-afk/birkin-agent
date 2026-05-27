# Tool Policy

The default model profile is `packet`; it generates a prompt packet and run record.
Configure `models.profiles.<id>.command` in `birkin.json` before allowing a subagent
to call an external model CLI. Keep runner commands as argv arrays, not shell strings.
