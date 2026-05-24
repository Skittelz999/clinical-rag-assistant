# AI pipeline

## Ingestion pipeline

```text
PDF upload -> extract text -> clean text -> chunk -> embed -> store chunks + vectors
```

## Question answering pipeline

```text
question -> retrieve chunks -> clean context -> build grounded prompt -> generate answer -> return answer with source cards
```

## Grounding rules

The assistant should:

- answer only from retrieved document chunks
- show source cards for grounded answers
- refuse when evidence is insufficient
- never claim to diagnose or replace professional judgement
