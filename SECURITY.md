# Security policy

Please report vulnerabilities privately through GitHub's
"Report a vulnerability" (Security → Advisories) on this repository. Do not open
public issues for security problems.

Design principles:

- Customer data stays in the customer's network; agents connect outbound only.
- Credentials are referenced (`vault:...`), never stored by the control plane.
- Every user and system action is written to an append-only audit log.
