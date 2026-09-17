# From Dev to Prod

Based on https://github.com/Masterschool-SWE/Events-API (starter commit e2b4460).

## Session 1: Explore the API

Run python app.py; open /apidocs/ and /api/openapi.yaml.
GET /api/health returns 200 and {"status":"healthy"}.
Register and log in with /api/auth/register and /api/auth/login.
Send the returned token as Authorization: Bearer <token> to create events.
Public events accept anonymous RSVPs. Protected events require a login (401
without it). Admin events reject ordinary members with 403. Missing events
return 404; invalid dates or missing titles return 400.

## Session 2: Automated tests

    python -m pip install -r requirements-dev.txt
    python -m pytest --cov=app --cov=models --cov=routes --cov-fail-under=95

The unit tests cover password hashing and serialization. Integration tests
exercise routes, database, JWT authentication, roles, capacity and RSVP updates.
Fixtures create a fresh in-memory SQLite database per test. The suite exposed
and fixed the starter's full-event cancellation bug.

## Session 3: Docker

    docker build --target test -t events-api-tests .
    docker run --rm events-api-tests
    docker build -t events-api .
    docker run --rm -p 5000:5000 events-api
    python smoke_test.py http://127.0.0.1:5000 --exercise

The runtime uses Gunicorn as a non-root user, honors PORT, and exposes a health
check. The build excludes secrets, databases and local caches. Only use
--exercise against a disposable demo: it creates a user and event.

## Sessions 4 and 5: CI/CD

.github/workflows/ci.yml runs on pushes, pull requests and manual dispatch.
It runs pytest with a 95% coverage gate, tests inside Docker, builds the
production image and checks it over real HTTP. The exact tested image is tagged
with the Git commit SHA and latest before publishing to Docker Hub.
Render is triggered after successful publication. The deployment check waits
for the matching revision so an older deployment cannot produce a false pass.

Repository variables:

- DOCKERHUB_USERNAME: artemlavrent (enables publishing)
- RENDER_URL: the verified public service URL (enables deployment)

Repository secrets:

- DOCKERHUB_TOKEN: a Docker Hub token with read/write permission
- RENDER_DEPLOY_HOOK: the deploy hook for this Render service

Create a free Render Web Service from docker.io/artemlavrent/events-api:latest,
or use render.yaml. Configure independent random SECRET_KEY and JWT_SECRET_KEY
values in Render, FIRST_USER_ADMIN=false, PORT=10000 and /api/health as the
health check path. Never commit credentials. Public deployment disables the
starter's automatic admin grant to its first visitor.

The free service uses ephemeral SQLite: data can disappear on restart or
redeploy. This is a coursework demo, not a durable production data store.

## Submission

- GitHub: https://github.com/GCMS-support/Events-API
- Docker Hub: https://hub.docker.com/r/artemlavrent/events-api
- Render: record the actual URL only after deployment and smoke checks pass.

An empty Docker repository is not a published image. A prepared workflow is not
evidence that CI has passed. Submit the three links only after each is verified.
