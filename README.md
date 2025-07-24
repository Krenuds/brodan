# Docker Python Environment

## Setup

1. Build and run the container:
   ```bash
   docker-compose up --build
   ```

2. Access the application at http://localhost:8000

## Development

- Your code is mounted as a volume, so changes are reflected immediately
- Add Python dependencies to `requirements.txt` and rebuild the container

## Commands

- Start container: `docker-compose up`
- Stop container: `docker-compose down`
- Rebuild container: `docker-compose up --build`
- Run shell in container: `docker-compose exec app bash`