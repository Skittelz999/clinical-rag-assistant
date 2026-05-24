# Screenshots

Use these exact files for the README screenshots:

- `docs/assets/screenshots/home-page.png`
- `docs/assets/screenshots/documents-upload.png`
- `docs/assets/screenshots/document-ready.png`
- `docs/assets/screenshots/chat-answer-with-sources.png`

## Capture Flow

1. Start a fresh local stack:

   ```bash
   docker compose down -v
   docker compose up --build -d
   ```

2. Open `http://localhost:5173/` and capture `home-page.png`.
3. Open `http://localhost:5173/documents` before upload and capture `documents-upload.png`.
4. Upload `demo-data/synthetic-clinical-guideline.pdf`.
5. Wait until the document status is `Ready` and embeddings are `Embedded`, then capture `document-ready.png`.
6. Open `http://localhost:5173/chat`.
7. Ask `What is the first-line management pathway for Condition G?`.
8. Confirm the answer and source cards are visible, then capture `chat-answer-with-sources.png`.

The screenshots should show the visible disclaimer: `Demo only. Not for medical use.`
