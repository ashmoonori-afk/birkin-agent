# Tool Policy

The default model profile is `packet`; it generates a prompt packet and run record.
Configure a local CLI command or API profile in `birkin.json` before allowing a subagent
to call an external model. Keep runner commands as argv arrays, not shell strings.
Store secrets in the local CLI auth store or environment variables, not in `birkin.json`.
