# Demo script

1. Start the app with Docker Compose.
2. Open the Home page and point out the demo-only safety disclaimer.
3. Go to Documents and upload `demo-data/synthetic-clinical-guideline.pdf`.
4. Wait for `Ready` document status and `Embedded` embedding status.
5. Use semantic search or the document debug question area to show retrieved chunks.
6. Go to Chat and ask: `What is the first-line management pathway for Condition G?`
7. Show the answer and source cards.
8. Ask: `What emergency warning signs require urgent escalation?`
9. Explain that deterministic mode is offline/demo-stable and OpenAI mode can be enabled through `.env`.
