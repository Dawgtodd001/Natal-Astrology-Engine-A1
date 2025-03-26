# Natal Astrology API Documentation

## Overview

The Natal Astrology API provides astrological chart analysis and interpretations based on birth information. It offers endpoints for generating natal charts, interpreting charts with various templates, and retrieving information about supported house systems.

## Authentication

All API endpoints require authentication via API key. Include your API key in the HTTP header:

```
X-API-Key: your_api_key
```

If you don't have an API key, contact the API administrator to request one.

## Rate Limiting

API usage is limited according to your API key's configuration. Default limits are:
- 60 requests per minute
- 1,000 requests per day

## Endpoints

### 1. Generate Natal Chart

Generates a complete astrological birth chart based on birth information.

**URL**: `/api/chart`  
**Method**: `POST`  
**Auth required**: Yes  

**Request Body**:
```json
{
  "birth_date": "YYYY-MM-DD",
  "birth_time": "HH:MM",
  "latitude": float,
  "longitude": float,
  "timezone": "string (optional)",
  "house_system": "string (default: placidus)",
  "zodiac_type": "string (default: tropical)"
}
```

| Parameter | Type | Description |
|-----------|------|-------------|
| birth_date | string | Birth date in YYYY-MM-DD format |
| birth_time | string | Birth time in 24-hour format (HH:MM) |
| latitude | float | Birth latitude (-90 to 90) |
| longitude | float | Birth longitude (-180 to 180) |
| timezone | string | IANA timezone name (e.g., "America/New_York"). If not provided, will be auto-detected based on coordinates |
| house_system | string | House system to use (default: "placidus"). See the /api/house-systems endpoint for available options |
| zodiac_type | string | Zodiac type: "tropical" or "sidereal" (default: "tropical") |

**Success Response**:
- **Code**: 200 OK
- **Content**: JSON object containing the complete chart data including planets, houses, aspects, and angles

**Example Response**:
```json
{
  "planets": [
    {
      "name": "Sun",
      "sign": "Taurus",
      "degree": 15,
      "minutes": 30,
      "house": 10,
      "retrograde": false,
      "speed": 0.98
    },
    // ... other planets
  ],
  "houses": [
    {
      "number": 1,
      "sign": "Leo",
      "degree": 12,
      "minutes": 45
    },
    // ... other houses
  ],
  "aspects": [
    {
      "planet1": "Sun",
      "planet2": "Moon",
      "aspect_type": "trine",
      "orb": 0.5,
      "applying": true
    },
    // ... other aspects
  ],
  "angles": {
    "ascendant": {
      "sign": "Leo",
      "degree": 12,
      "minutes": 45
    },
    "midheaven": {
      "sign": "Taurus",
      "degree": 3,
      "minutes": 21
    },
    "descendant": {
      "sign": "Aquarius",
      "degree": 12,
      "minutes": 45
    },
    "imum_coeli": {
      "sign": "Scorpio",
      "degree": 3,
      "minutes": 21
    }
  }
}
```

**Error Responses**:
- **Code**: 400 Bad Request
  - **Content**: `{"detail": {"error_code": "INVALID_INPUT", "message": "Invalid chart parameters: [error details]", "type": "ValueError"}}`
- **Code**: 401 Unauthorized
  - **Content**: `{"detail": "Invalid API key"}`
- **Code**: 429 Too Many Requests
  - **Content**: `{"detail": "Rate limit exceeded: [limit details]"}`
- **Code**: 500 Internal Server Error
  - **Content**: `{"detail": {"error_code": "CALCULATION_ERROR", "message": "Chart calculation failed: [error details]", "type": "Exception"}}`

### 2. Interpret Chart

Generates a text interpretation of a natal chart based on birth information and a template.

**URL**: `/api/interpret`  
**Method**: `POST`  
**Auth required**: Yes  

**Request Body**:
```json
{
  "birth_date": "YYYY-MM-DD",
  "birth_time": "HH:MM",
  "latitude": float,
  "longitude": float,
  "timezone": "string (optional)",
  "house_system": "string (default: placidus)",
  "zodiac_type": "string (default: tropical)",
  "template_name": "string (default: basic_text)"
}
```

Parameters are the same as the `/api/chart` endpoint with the addition of:

| Parameter | Type | Description |
|-----------|------|-------------|
| template_name | string | Name of interpretation template to use (default: "basic_text") |

**Success Response**:
- **Code**: 200 OK
- **Content**: Text interpretation of the chart (format depends on the template)

**Example Response**:
```
NATAL CHART INTERPRETATION

Birth Information:
Date: 1990-05-01
Time: 12:30
Location: 40.7128° N, 74.0060° W (New York, NY)

Astrological Profile:

Sun in Taurus: You are practical, determined, and reliable. You value stability and security...

[More interpretation text...]
```

**Error Responses**:
Same as the `/api/chart` endpoint.

### 3. Get House Systems

Retrieves a list of available house systems with descriptions.

**URL**: `/api/house-systems`  
**Method**: `GET`  
**Auth required**: Yes  

**Success Response**:
- **Code**: 200 OK
- **Content**: JSON object mapping house system IDs to descriptions

**Example Response**:
```json
{
  "placidus": "The most commonly used house system in Western astrology",
  "koch": "A time-based house system developed by Walter Koch",
  "regiomontanus": "A space-based house system using a great circle through the east and west points",
  "campanus": "A space-based house system using a great circle through the north and south points",
  "equal": "A system where each house is exactly 30 degrees",
  "whole_sign": "Each house corresponds to a complete sign of the zodiac",
  "porphyry": "Houses are determined by trisecting the arcs between the angles"
}
```

**Error Responses**:
- **Code**: 401 Unauthorized
  - **Content**: `{"detail": "Invalid API key"}`
- **Code**: 429 Too Many Requests
  - **Content**: `{"detail": "Rate limit exceeded: [limit details]"}`
- **Code**: 500 Internal Server Error
  - **Content**: `{"detail": {"error_code": "INTERNAL_ERROR", "message": "Failed to retrieve house systems", "type": "Exception"}}`

### 4. Health Check

Checks the health status of the API and its dependencies.

**URL**: `/api/health`  
**Method**: `GET`  
**Auth required**: No  

**Success Response**:
- **Code**: 200 OK
- **Content**: JSON object with health check results

**Example Response**:
```json
{
  "status": "healthy",
  "timestamp": "2025-03-26T12:34:56.789Z",
  "version": "1.0.0",
  "components": {
    "database": {
      "status": "healthy",
      "error": null
    },
    "api_keys": {
      "status": "healthy",
      "count": 5
    }
  },
  "response_time_seconds": 0.123
}
```

## Error Codes

The API uses the following error codes in responses:

| Error Code | Description |
|------------|-------------|
| INVALID_INPUT | Invalid input parameters |
| CALCULATION_ERROR | Error during chart calculation |
| DATABASE_ERROR | Database-related error |
| AUTHENTICATION_ERROR | Authentication failure |
| RATE_LIMIT_ERROR | Rate limit exceeded |
| INTERNAL_ERROR | Unexpected internal server error |

## Best Practices

1. Always specify the exact birth time in 24-hour format for accurate charts
2. Use IANA timezone names where possible, but the API can auto-detect them from coordinates
3. For the best accuracy, provide latitude and longitude to at least 4 decimal places
4. Cache API responses when practical to minimize API calls
5. When implementing client applications, include proper error handling for all API responses

## Contact

For API access requests or technical support, contact the API administrator at [contact information].