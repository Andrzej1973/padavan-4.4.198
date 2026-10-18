# Instructions for every project agent

Before any Git, GitHub, GitLab, or other network command, clear proxy variables
in the same shell/process that will run the command. This prevents an inherited
unavailable proxy from breaking direct network access. Use the PowerShell or
Bash snippet in `docs/AGENT-HANDOFF-RULES-SOL-DEEPSEEK.md`, section 14.

This is process-local cleanup only. Do not print proxy URLs, change Windows or
global Git proxy settings, or remove saved proxy configuration. If access still
fails, inspect Git proxy/URL rewrite configuration without exposing credentials
and report a network-environment restriction when direct access is blocked.

For project context and the current executor, start with
`docs/AGENT-BOOTSTRAP.md` and `docs/EXECUTION-ROLE.md`.
