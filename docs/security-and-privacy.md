# Security and privacy notes

This portfolio project must avoid real patient data.

## Demo-safe rules

- Use synthetic PDFs only for the portfolio demo.
- Add a visible disclaimer in the UI.
- Do not upload real patient data or private clinical material.
- Keep `.env` files out of Git and publish only placeholder values in `.env.example`.
- Treat uploaded PDFs as runtime data, not repository content.

## Future production concerns

- HIPAA/GDPR compliance review
- audit logging and retention policy
- encrypted object storage
- organization-level access controls
- prompt-injection filtering
- signed document provenance
