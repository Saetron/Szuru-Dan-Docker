# Szuru-Dan Docker

A Flask-based API translation proxy that maps Szurubooru API endpoints into Danbooru-style responses, allowing third-party Danbooru mobile and desktop clients to connect directly to your Szurubooru server.

---

## Getting Started

### Option 1: Running with Docker (Recommended)

#### 1. Using Docker Compose
Create a `docker-compose.yml` file:

```yaml
services:
  szuru-dan:
    image: ghcr.io/saetron/szuru-dan-docker:latest
    container_name: szuru-dan
    ports:
      - "9000:9000"
    volumes:
      - ./config.ini:/app/config.ini:ro
    restart: unless-stopped
  ```

Start the container:

```bash
docker compose up -d
```

#### 2. Using Docker CLI

```bash
docker run -d \
  --name szuru-dan \
  -p 9000:9000 \
  -v $(pwd)/config.ini:/app/config.ini:ro \
  ghcr.io/saetron/szuru-dan-docker:latest
```

### Option 2: Local Installation
#### 1. Clone the repository
```bash
git clone https://github.com/Saetron/Szuru-Dan-Docker.git
cd Szuru-Dan-Docker
```
#### 2. Install dependencies
```bash
pip install -r requirements.txt
```
#### 3. Run the server
```bash
python app.py
```

## Configuration
Copy or rename `config_.ini` to `config.ini` in the root directory:
```toml
[API]
# The base URL of your Szurubooru server API instance
backend_url = http://127.0.0.1:8080/

# Port on which this API translator runs
port = 9000

# Enable reverse proxy mode
# Rewrites image URLs to point to this proxy server
reverse_proxy_mode = false

# Enable performance timing logs (for debugging)
enable_timing_logs = false
```

## Supported API
- `/posts.json`
- `/posts/{id}.json`
- `/favorites.json`
- `/favorites/{id}.json`
- `/post_votes.json`
- `/users/{id}.json`
- `/profile.json`
- `/tags/autocomplete.json`

## Tested Clients

Android:
- [BooruHub(Flexbooru)](https://github.com/flexbooru/flexbooru)
- [Boorusama](https://github.com/khoadng/Boorusama)

IOS:
- [AnimeBoxes](https://www.animebox.es/) (Also validated with the docker version)
