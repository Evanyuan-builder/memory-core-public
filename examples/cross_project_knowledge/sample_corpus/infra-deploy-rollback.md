---
project: infra
type: decision
description: deploys build an image once, then promote the same artifact
---
We never rebuild between environments. CI builds one image, tags it by content
digest, and staging/prod both promote that exact digest. Rollback is just
re-pointing the deployment at the previous digest — no rebuild, no "works on
my machine" drift between stage and prod. The artifact that passed staging is
byte-for-byte the artifact that serves prod.
