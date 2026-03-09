# Image Platform

Serverless image upload, storage, and management platform on AWS.

## Architecture

```
Client
  ↓
API Gateway
  ↓
API Lambda
  ├── POST /images/upload-url    → S3 pre-signed PUT URL
  ├── GET  /images               → List with date/size filters + pagination
  ├── GET  /images/{id}          → S3 pre-signed GET URL
  └── DELETE /images/{id}        → Soft delete
         ↓
        S3
         ↓ (S3 event)
Metadata Lambda
  └── Extracts metadata → DynamoDB (status: COMPLETED)
```

## DynamoDB Table

| Key | Pattern |
|-----|---------|
| PK  | `USER#<user_id>` |
| SK  | `IMAGE#<timestamp>#<image_id>` |

## API

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/images/upload-url` | Get pre-signed upload URL |
| GET | `/images` | List images (supports filters) |
| GET | `/images/{image_id}` | Get image + download URL |
| DELETE | `/images/{image_id}` | Delete image |

### List filters

```
GET /images?from=2026-03-01&to=2026-03-05&min_size=100000&max_size=500000&limit=20&cursor=abc
```

