import configparser
import os
from pathlib import Path


class Config:
    def __init__(self, config_path: str = "config.ini"):
        config = configparser.ConfigParser()
        ini_file = Path(config_path)
        if ini_file.exists():
            config.read(config_path)

        api_section = config["API"] if "API" in config else {}

        # 1. Szurubooru backend URL
        backend_url = os.environ.get(
            "SZURUBOORU_URL",
            api_section.get("backend_url", "http://127.0.0.1:8080/"),
        )
        if not backend_url.endswith("/"):
            backend_url += "/"
        self.SZURUBOORU_URL = backend_url

        # API base endpoint
        if self.SZURUBOORU_URL.endswith("/api/"):
            self.SZURUBOORU_API_URL = self.SZURUBOORU_URL[:-1]
        elif self.SZURUBOORU_URL.endswith("/api"):
            self.SZURUBOORU_API_URL = self.SZURUBOORU_URL
        else:
            self.SZURUBOORU_API_URL = f"{self.SZURUBOORU_URL}api"

        # 2. Reverse proxy mode
        env_reverse_proxy = os.environ.get("REVERSE_PROXY_MODE")
        if env_reverse_proxy is not None:
            self.REVERSE_PROXY_MODE = env_reverse_proxy.lower() in (
                "true",
                "1",
                "yes",
            )
        else:
            self.REVERSE_PROXY_MODE = api_section.get(
                "reverse_proxy_mode", "false"
            ).lower() in ("true", "1", "yes")

        # 3. Enable timing logs
        env_timing = os.environ.get("ENABLE_TIMING_LOGS")
        if env_timing is not None:
            self.ENABLE_TIMING_LOGS = env_timing.lower() in ("true", "1", "yes")
        else:
            self.ENABLE_TIMING_LOGS = api_section.get(
                "enable_timing_logs", "false"
            ).lower() in ("true", "1", "yes")

        # 4. Domain URL for ordinary mode
        if not self.REVERSE_PROXY_MODE:
            domain = os.environ.get("DOMAIN_URL", api_section.get("domain_url", ""))
            if domain and not domain.endswith("/"):
                domain += "/"
            self.DOMAIN_URL = domain or self.SZURUBOORU_URL
        else:
            self.DOMAIN_URL = ""

        # 5. Service Port
        env_port = os.environ.get("PORT")
        if env_port:
            try:
                self.SERVICE_PORT = int(env_port)
            except ValueError:
                self.SERVICE_PORT = 9000
        else:
            try:
                self.SERVICE_PORT = int(api_section.get("port", 9000))
            except ValueError:
                self.SERVICE_PORT = 9000

        # 6. Debug mode
        env_debug = os.environ.get("DEBUG")
        if env_debug is not None:
            self.DEBUG = env_debug.lower() in ("true", "1", "yes")
        else:
            self.DEBUG = api_section.get("debug", "false").lower() in (
                "true",
                "1",
                "yes",
            )


# Global config instance
config = Config()
