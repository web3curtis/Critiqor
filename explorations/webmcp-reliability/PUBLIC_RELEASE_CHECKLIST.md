# Public judge release checklist

This checklist preserves the localhost presentation while replacing every loopback dependency with a durable HTTPS service.

## Build and hosting

- [ ] Publish the combined experiment presentation at one stable public HTTPS URL.
- [ ] Publish the genuine Crema & Co. frontend, API, and database; do not substitute a screenshot or static mock.
- [ ] Publish the anonymous baseline Critiqor `run_001` dashboard at a stable HTTPS URL.
- [ ] Publish the anonymous playbook-guided Critiqor `run_001` dashboard at a stable HTTPS URL.
- [ ] Configure the combined site with the three public child-service URLs at build time.
- [ ] Remove all `localhost`, `127.0.0.1`, temporary tunnel, and workstation-path references from the public build.

## Privacy and security

- [ ] Keep both Critiqor dashboards in anonymous mode.
- [ ] Scan the published HTML, JavaScript, API responses, and run evidence for names, absolute paths, tokens, keys, and local hostnames.
- [ ] Store deployment credentials only in the hosting provider's encrypted secret store; never commit them or place them in client-side variables.
- [ ] Confirm no checkout or real purchase can be triggered by the judge demo.

## Cross-site functionality

- [ ] Allow the three child apps to be embedded by the presentation origin using `Content-Security-Policy: frame-ancestors`.
- [ ] Configure Crema API CORS for the public Crema origin.
- [ ] Confirm cookies/session state work in the judge's browser policy, or use a same-site proxy where third-party cookies are blocked.
- [ ] Verify agent playback starts in Catalog, applies the exact cart task, opens Compare, and supports Skip to result.
- [ ] Verify expandable experiment cards, table navigation, the baseline playbook, and both dashboard deep links.
- [ ] Verify the public Crema origin still exposes the intended WebMCP tools.

## Independent judge test

- [ ] Stop every localhost server and temporary tunnel before the final test.
- [ ] Open the public URL in a clean browser profile on a different network or mobile hotspot.
- [ ] Test at desktop and laptop widths; ensure key text remains readable without browser zoom.
- [ ] Reload every deep link directly and confirm there are no authentication prompts or deployment-protection screens.
- [ ] Check service health and logs, then record the final public URL in Devpost.

## Durability

- [ ] Use production deployments with stable project names and domains, not preview URLs or quick tunnels.
- [ ] Enable automatic restart/health checks for Crema and its API.
- [ ] Keep the database persistent across deploys.
- [ ] Document a single redeploy command for each service and retain the sanitized experiment bundles used for the two dashboards.
