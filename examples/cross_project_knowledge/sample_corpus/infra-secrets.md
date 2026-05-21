---
project: infra
type: learning
description: a leaked token must be revoked, not just rotated out of git
---
Someone pasted a cloud token into a chat log. Removing it from history is not
enough — once a secret has touched an untrusted surface, treat it as public:
revoke it immediately, then issue a fresh least-privilege token scoped to the
one job that needed it. Rotation without revocation leaves the old token live.
The clock starts at exposure, not at discovery.
