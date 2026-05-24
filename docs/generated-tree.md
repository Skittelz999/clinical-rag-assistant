# Generated scaffold tree

```text
clinical-rag-assistant/
├── backend/
│   ├── scripts/
│   │   ├── ingest_demo_docs.py
│   │   └── seed_demo.py
│   ├── src/
│   │   └── app/
│   │       ├── ai/
│   │       │   ├── clients/
│   │       │   │   ├── __init__.py
│   │       │   │   └── openai_client.py
│   │       │   ├── prompts/
│   │       │   │   ├── __init__.py
│   │       │   │   ├── clinical_qa.py
│   │       │   │   └── summarization.py
│   │       │   ├── __init__.py
│   │       │   └── guards.py
│   │       ├── api/
│   │       │   ├── v1/
│   │       │   │   ├── endpoints/
│   │       │   │   │   ├── __init__.py
│   │       │   │   │   ├── auth.py
│   │       │   │   │   ├── cases.py
│   │       │   │   │   ├── chat.py
│   │       │   │   │   ├── documents.py
│   │       │   │   │   ├── health.py
│   │       │   │   │   └── users.py
│   │       │   │   ├── __init__.py
│   │       │   │   ├── deps.py
│   │       │   │   └── router.py
│   │       │   └── __init__.py
│   │       ├── core/
│   │       │   ├── __init__.py
│   │       │   ├── config.py
│   │       │   ├── exceptions.py
│   │       │   ├── logging.py
│   │       │   └── security.py
│   │       ├── db/
│   │       │   ├── __init__.py
│   │       │   ├── base.py
│   │       │   └── session.py
│   │       ├── models/
│   │       │   ├── __init__.py
│   │       │   ├── audit_event.py
│   │       │   ├── chunk.py
│   │       │   ├── citation.py
│   │       │   ├── conversation.py
│   │       │   ├── document.py
│   │       │   ├── message.py
│   │       │   ├── patient_case.py
│   │       │   └── user.py
│   │       ├── repositories/
│   │       │   ├── __init__.py
│   │       │   ├── case_repository.py
│   │       │   ├── chunk_repository.py
│   │       │   ├── conversation_repository.py
│   │       │   ├── document_repository.py
│   │       │   └── user_repository.py
│   │       ├── schemas/
│   │       │   ├── __init__.py
│   │       │   ├── auth.py
│   │       │   ├── case.py
│   │       │   ├── chat.py
│   │       │   ├── common.py
│   │       │   ├── document.py
│   │       │   └── user.py
│   │       ├── services/
│   │       │   ├── __init__.py
│   │       │   ├── audit_service.py
│   │       │   ├── auth_service.py
│   │       │   ├── case_service.py
│   │       │   ├── chat_service.py
│   │       │   ├── chunking_service.py
│   │       │   ├── citation_service.py
│   │       │   ├── document_service.py
│   │       │   ├── embedding_service.py
│   │       │   ├── pdf_service.py
│   │       │   ├── rag_service.py
│   │       │   └── retrieval_service.py
│   │       ├── workers/
│   │       │   ├── __init__.py
│   │       │   └── tasks.py
│   │       ├── __init__.py
│   │       └── main.py
│   ├── storage/
│   │   ├── processed/
│   │   │   └── .gitkeep
│   │   └── uploads/
│   │       └── .gitkeep
│   ├── tests/
│   │   ├── __init__.py
│   │   └── test_health.py
│   ├── alembic.ini
│   ├── Dockerfile
│   ├── pyproject.toml
│   └── README.md
├── data/
│   ├── demo_pdfs/
│   │   └── .gitkeep
│   └── local/
│       └── .gitkeep
├── docs/
│   ├── ai-pipeline.md
│   ├── architecture.md
│   ├── demo-script.md
│   ├── generated-tree.md
│   ├── project-structure.md
│   └── security-and-privacy.md
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── cases/
│   │   │   │   ├── CaseEditor.vue
│   │   │   │   └── CaseSummaryCard.vue
│   │   │   ├── chat/
│   │   │   │   ├── ChatMessage.vue
│   │   │   │   ├── CitationPanel.vue
│   │   │   │   └── QuestionInput.vue
│   │   │   ├── documents/
│   │   │   │   ├── DocumentList.vue
│   │   │   │   └── DocumentUploader.vue
│   │   │   ├── layout/
│   │   │   │   ├── Sidebar.vue
│   │   │   │   └── TopBar.vue
│   │   │   └── ui/
│   │   │       ├── AppButton.vue
│   │   │       └── AppCard.vue
│   │   ├── layouts/
│   │   │   └── AppLayout.vue
│   │   ├── router/
│   │   │   └── index.ts
│   │   ├── services/
│   │   │   ├── api.ts
│   │   │   ├── authService.ts
│   │   │   ├── caseService.ts
│   │   │   ├── chatService.ts
│   │   │   └── documentService.ts
│   │   ├── stores/
│   │   │   ├── authStore.ts
│   │   │   ├── caseStore.ts
│   │   │   ├── chatStore.ts
│   │   │   └── documentStore.ts
│   │   ├── styles/
│   │   │   └── main.css
│   │   ├── types/
│   │   │   ├── case.ts
│   │   │   ├── chat.ts
│   │   │   └── document.ts
│   │   ├── utils/
│   │   │   └── formatDate.ts
│   │   ├── views/
│   │   │   ├── CasesView.vue
│   │   │   ├── ChatView.vue
│   │   │   ├── DocumentsView.vue
│   │   │   ├── LoginView.vue
│   │   │   └── SettingsView.vue
│   │   ├── App.vue
│   │   └── main.ts
│   ├── tests/
│   │   └── .gitkeep
│   ├── Dockerfile
│   ├── index.html
│   ├── package.json
│   ├── postcss.config.js
│   ├── README.md
│   ├── tailwind.config.js
│   ├── tsconfig.json
│   └── vite.config.ts
├── infra/
│   ├── db/
│   │   └── init.sql
│   └── docker/
│       └── README.md
├── .env.example
├── .gitignore
├── docker-compose.yml
├── Makefile
└── README.md
```
