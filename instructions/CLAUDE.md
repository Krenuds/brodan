# Project Instructions

This file contains specific instructions and guidelines for developing this project.

## Project Overview

This is a Docker-based Python development environment starter template designed for rapid application development.

## Development Guidelines

### Setup and Environment
- Use Docker Compose for all development work
- Python 3.11-slim base image
- Port 8000 for local development
- Volume mounting for live code reloading

### Architecture Decisions
- Containerized development environment
- Minimal starter template ready for extension
- Standard Python project structure

### Development Workflow
1. Make changes to code
2. Changes are automatically reflected via volume mounting
3. Add dependencies to requirements.txt as needed
4. Rebuild container when dependencies change

## Future Considerations
- Framework selection (Flask, FastAPI, Django, etc.)
- Testing strategy
- Linting and code quality tools
- Production deployment strategy