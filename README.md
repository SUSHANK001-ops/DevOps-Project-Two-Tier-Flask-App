# Two-Tier Flask Application

This repository contains the container and CI/CD configuration for a two-tier
application made up of:

- **Flask**: the web application, exposed on port `5000`.
- **MySQL**: the database, exposed on port `3306` for local development.

Docker Compose creates a private `two-tier` network so that the Flask
container can reach MySQL by the service name `mysql`. A named Docker volume
keeps the database data across container restarts.

## Repository contents

| File | Purpose |
| --- | --- |
| [`app.py`](./app.py) | Flask web application with task creation, deletion, and database health checks. |
| [`requirements.txt`](./requirements.txt) | Python dependencies installed into the Flask image. |
| [`templates/index.html`](./templates/index.html) | User interface for the task board. |
| [`static/style.css`](./static/style.css) | Styling for the web interface. |
| [`Dockerfile`](./Dockerfile) | Builds the Flask application image with Python 3.9. |
| [`docker-compose.yml`](./docker-compose.yml) | Runs the Flask and MySQL services together. |
| [`Jenkinsfile`](./Jenkinsfile) | Defines the Jenkins build and deployment pipeline. |

## Prerequisites

Install the following on a local machine used for development:

- Git
- Docker Engine or Docker Desktop
- Docker Compose v2 (`docker compose`)

For Jenkins deployments, the Jenkins agent must also have:

- Permission to run Docker commands
- Docker Compose v2 available on the agent `PATH`
- Network access to clone this repository
- A Linux-based agent, because the pipeline uses the `sh` step

## Run locally with Docker Compose

Clone the repository and start the services:

```bash
git clone https://github.com/SUSHANK001-ops/DevOps-Project-Two-Tier-Flask-App.git
cd DevOps-Project-Two-Tier-Flask-App
docker compose up -d --build
```

The `--build` option rebuilds the Flask image from the current source. To
start the services without rebuilding, use:

```bash
docker compose up -d
```

### Access and verify the application

- Flask application: <http://localhost:5000>
- Flask health endpoint: <http://localhost:5000/health>
- MySQL from the host: `localhost:3306`

Check the service state and logs:

```bash
docker compose ps
docker compose logs -f flask
docker compose logs -f mysql
```

The Flask service health check calls `/health`. The MySQL service health check
uses `mysqladmin ping`. Both checks may take up to a minute after the first
startup because their `start_period` is set to 60 seconds.

### Stop the application

Stop and remove the containers and network while keeping the database volume:

```bash
docker compose down
```

To remove the database volume as well (this permanently deletes local MySQL
data), run:

```bash
docker compose down -v
```

## Service configuration

The Compose file currently uses these development credentials and connection
settings:

| Setting | Value |
| --- | --- |
| MySQL database | `devops` |
| MySQL user | `root` |
| MySQL password | `root` |
| MySQL host from Flask | `mysql` |
| Flask port | `5000` |
| MySQL port | `3306` |

These default credentials are intended for local development only. Use
secrets or environment-specific configuration before deploying to a shared or
production environment. In particular, do not expose the MySQL port or use
the MySQL root account in production.

The Flask container receives its database settings through:

```text
MYSQL_HOST=mysql
MYSQL_USER=root
MYSQL_PASSWORD=root
MYSQL_DB=devops
```

## Jenkins pipeline

The [`Jenkinsfile`](./Jenkinsfile) defines a three-stage declarative pipeline:

### 1. Clone Code

Jenkins checks out the `main` branch from:

```text
https://github.com/SUSHANK001-ops/DevOps-Project-Two-Tier-Flask-App.git
```

### 2. Build Docker Image

The agent builds the application image:

```bash
docker build -t flask-app:latest .
```

The image is tagged as `flask-app:latest`. It is used locally by the
deployment environment and is not pushed to a container registry by this
pipeline.

### 3. Deploy with Docker Compose

The pipeline first attempts to stop any existing deployment:

```bash
docker compose down || true
```

The `|| true` allows the pipeline to continue when no previous Compose stack
exists. It then rebuilds and starts the services in detached mode:

```bash
docker compose up -d --build
```

This means a successful Jenkins build leaves the Flask and MySQL containers
running on the Jenkins agent itself. The Jenkins agent must therefore be the
machine intended to host the application.

## Configure Jenkins

1. Install Jenkins on a machine with Docker and Docker Compose v2.
2. Ensure the Jenkins service account can access the Docker daemon. On Linux,
   this commonly means adding the account to the `docker` group and restarting
   the Jenkins service.
3. Create a **Pipeline** job.
4. Select **Pipeline script from SCM**.
5. Select **Git** and enter:
   `https://github.com/SUSHANK001-ops/DevOps-Project-Two-Tier-Flask-App.git`.
6. Set the branch to `*/main`.
7. Set the script path to `Jenkinsfile`.
8. Run **Build Now** or enable a suitable SCM webhook/trigger.

For a private repository, configure Jenkins credentials and select them in the
SCM configuration. The current Jenkinsfile does not define registry
authentication, image publishing, rollback, or automated tests.

## Troubleshooting

### The Flask container exits during build or startup

Rebuild and inspect the logs:

```bash
docker compose build --no-cache flask
docker compose logs flask
```

### Flask cannot connect to MySQL

Use `mysql` as the database hostname inside Compose, not `localhost`.
Check the MySQL logs and wait for its health check to pass:

```bash
docker compose ps
docker compose logs mysql
```

If the database volume contains invalid or incomplete local data, recreate it
with `docker compose down -v` followed by `docker compose up -d --build`.

### Jenkins cannot run Docker

Verify Docker access using the same account that runs the Jenkins agent:

```bash
docker version
docker compose version
```

Also confirm that the agent is Linux-based and that the Docker daemon is
running.

## Development notes

- The Compose `mysql-data` volume is deliberately persistent.
- Both services use `restart: always`.
- The Flask image installs `gcc`, `default-libmysqlclient-dev`, and `pkg-config`
  to support packages that require `mysqlclient`.
-   - `app.py` creates the `tasks` table automatically when the container starts.
  - The `/` route displays tasks and accepts new tasks through the form.
  - The `/tasks/<id>/delete` route removes a task.
  - The `/health` route checks both the Flask process and its MySQL connection.
