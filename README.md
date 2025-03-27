# Natal Astrology Engine API

A sophisticated FastAPI-based Natal Astrology Engine that generates comprehensive astrological birth charts with advanced interpretation capabilities.

## Overview

This API service provides powerful astrological chart generation and interpretation capabilities. It calculates planetary positions, houses, aspects, and other astrological factors based on birth information, and offers detailed interpretations of these elements.

## Key Features

- **Comprehensive Chart Calculation**: Generate detailed natal charts with accurate planetary positions, house cusps, aspects, and more.
- **Multiple House Systems**: Support for seven house systems including Placidus, Koch, Regiomontanus, Campanus, Equal, Whole Sign, and Porphyry.
- **Interpretation Engine**: Template-based interpretation system that provides personalized readings of chart elements.
- **Enhanced Timezone Detection**: Improved algorithm for determining timezone from geographic coordinates with better accuracy.
- **Intelligent Health Monitoring**: Advanced health check with exponential backoff and automatic retry mechanism.
- **Graceful Service Degradation**: Maintenance mode that activates automatically when the API is starting up.
- **Caching Mechanism**: Efficient caching of calculations to optimize performance.
- **API Key Authentication**: Secure access control with API key authentication.
- **Rate Limiting**: Built-in rate limiting to prevent abuse.
- **Comprehensive Logging**: Structured logging for better observability and debugging.

## Technical Architecture

The API is built with:

- **FastAPI**: High-performance web framework
- **SQLAlchemy**: ORM for database operations
- **PostgreSQL**: Robust relational database
- **Flatlib**: Astrological calculation library
- **Timezonefinder & Pytz**: Location-based timezone resolution

The architecture follows a clean, modular design with clear separation of concerns:

- **API Layer**: Request handling, validation, and response formatting
- **Core Layer**: Astrological calculations and chart generation
- **Database Layer**: Data persistence and caching
- **Utilities**: Shared functionality like logging and error handling

## API Endpoints

- **`/api/chart`**: Generate a complete natal chart
- **`/api/interpret`**: Generate a textual interpretation of a natal chart
- **`/api/house-systems`**: Get available house systems with descriptions
- **`/api/health`**: Check API health status
- **`/api/admin/keys`**: (Admin only) Manage API keys

## Documentation

- [API Documentation](static/api_docs.md): Details on all endpoints
- [Setup Guide](SETUP.md): Instructions for setting up development and production environments

## Getting Started

See [SETUP.md](SETUP.md) for detailed instructions on how to set up and run the API.

Quick start:

```bash
# Clone repository
git clone https://github.com/yourusername/natal-astrology-api.git
cd natal-astrology-api

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export DATABASE_URL="postgresql://username:password@localhost:5432/dbname"

# Run the API
python run.py
```

## Testing

The repository includes several test scripts to verify functionality:

```bash
# Test API endpoints
python test_api.py

# Test flatlib integration
python test_flatlib.py

# Test house system calculations
python test_house.py
```

## License

[MIT License](LICENSE)

## Acknowledgements

This project uses the following open-source libraries:

- [flatlib](https://github.com/flatangle/flatlib) - Astrological calculation library
- [FastAPI](https://fastapi.tiangolo.com/) - Web framework
- [SQLAlchemy](https://www.sqlalchemy.org/) - ORM
- [Timezonefinder](https://github.com/MrMinimal64/timezonefinder) - Timezone lookup library
- [Pytz](https://pythonhosted.org/pytz/) - Timezone library