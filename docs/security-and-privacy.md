# Security and privacy notes

This portfolio project must avoid real patient data.

## Demo-safe rules

- Use fictional patient cases only.
- Use public medical guidelines or synthetic PDFs only.
- Add a visible disclaimer in the UI.
- Log document and chunk IDs, not sensitive free-text content.
- Keep role-based access enforcement in backend services, not only frontend views.

## Future production concerns

- HIPAA/GDPR compliance review
- audit logging and retention policy
- encrypted object storage
- organization-level access controls
- prompt-injection filtering
- signed document provenance
