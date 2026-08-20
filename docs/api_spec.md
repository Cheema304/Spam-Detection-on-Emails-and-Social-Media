# SpamShield AI API Specification

## GET `/api/health`
Returns runtime health, real-data status and the currently active model/vectorizer.

## GET `/api/stats`
Returns aggregate local prediction statistics plus current model version.

## GET `/api/model-evaluation`
Returns:
- real-data training metadata
- all eight current model benchmark rows
- confusion matrix, ROC data and channel metrics for the active model

This endpoint is useful for proving the web graphs are backed by live computed evaluation data.

## POST `/api/predict`
Content-Type: `application/json`

```json
{
  "text": "message to classify",
  "source_type": "Email"
}
```

Accepted source values: `Email`, `Social Media`, `API`.

Successful response includes:
- `prediction`
- `confidence`
- `spam_probability`
- `risk_level`
- `signals` when supported by the active classifier
- `processing_ms`
- `model_version`
- `active_model_key`
- `active_model`
- `active_vectorizer`

Validation rules:
- empty messages: HTTP 400
- messages above 8,000 characters: HTTP 400
- non-JSON prediction requests: HTTP 415
- request bodies above 64 KB: HTTP 413
