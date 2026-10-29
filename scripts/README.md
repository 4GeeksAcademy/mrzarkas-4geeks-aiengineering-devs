# `scripts` folder

## Frontend audit

`frontend-audit.mjs OUTPUT website|backoffice|summary desktop|mobile [1-3]`
runs Lighthouse 12.8.2 against local production servers, with three independent
cold runs by default. Set `AUDIT_TOOLS_DIR` to its temporary `node_modules`, or
pass that directory as the last argument. See `../audit/README.md` for setup,
artifacts, authentication and limitations.

`frontend-checks.mjs TOOLS_DIR [OUTPUT_JSON]` checks desktop/mobile home,
keyboard skip navigation, tool links, actual catalog filters, jurisdiction/
clinic controls without submitting, and disconnect. It obtains an ephemeral
synthetic development token; it performs no operational data writes. It needs
the same temporary puppeteer-core as Lighthouse and local Chrome. No permanent
application dependencies are added. Output defaults to `/private/tmp/`.

This folder contains **helper scripts** for the monorepo: development automation, maintenance utilities, repetitive tasks (setup, lint, migrations, data generation, etc.), and internal tooling.

- **Main purpose**: group support tools that do not belong to a specific app, agent, or pipeline but make the team’s work easier.
- **Recommendation**: document each script (what it does, parameters, requirements, usage examples) and keep them reproducible (and safe) across environments.

> _Spanish version: [README.es.md](./README.es.md)._
