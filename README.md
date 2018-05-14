# Sawtooth Simple Supply

## Usage

After cloning the repository, ensure that you have `docker` and
`docker-compose` installed on your machine. To run the application,
navigate to the project root directory and run:

```bash
docker-compose up
```

This will start up all Simple Supply components in separate containers.
The available HTTP endpoints are:
- Simple Supply REST API: **http://localhost:8000**
- PostgreSQL Admin Panel: **http://localhost:8080**
- Sawtooth REST API: **http://localhost:8008**
