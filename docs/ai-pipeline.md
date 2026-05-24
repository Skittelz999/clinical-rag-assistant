# AI pipeline

## Ingestion pipeline

```text
PDF upload -> extract text -> clean text -> chunk -> embed -> store chunks + vectors
```

## Question answering pipeline

```text
question -> retrieve chunks -> build grounded prompt -> generate answer -> validate citations -> return response
```

## Grounding rules

The assistant should:

- answer only from retrieved document chunks
- cite every factual claim
- refuse when evidence is insufficient
- separate clinical facts from generated summaries
- never claim to diagnose or replace professional judgement
