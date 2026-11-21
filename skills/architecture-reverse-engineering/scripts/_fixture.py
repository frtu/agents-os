"""Shared test fixture: a tiny synthetic repo built in a temp dir (no real data)."""

from __future__ import annotations

from pathlib import Path

FILES = {
    "README.md": "# Orders service\n\nConsumed by the checkout frontend.\n",
    "build.gradle.kts": (
        'plugins { kotlin("jvm") version "1.9.24"; id("org.springframework.boot") version "3.3.1" }\n'
        "kotlin { jvmToolchain(21) }\n"
        'dependencies { implementation("org.springframework.kafka:spring-kafka")\n'
        '  implementation("software.amazon.awssdk:s3")\n'
        '  implementation("org.postgresql:postgresql") }\n'
    ),
    "Dockerfile": "FROM zulu-openjdk:21-jre\nCOPY build/libs/app.jar /app.jar\n"
                  'ENTRYPOINT ["java", "-jar", "/app.jar"]\n',
    "src/main/resources/application.yml": (
        "spring:\n  datasource:\n    url: jdbc:postgresql://db:5432/orders\n"
        "    password: hunter2\n"
        "    username: ${DB_USER}\n"
        "payments-url: http://payments.internal/api\n"
        "kafka:\n  topic: orders.created\n"
    ),
    "src/main/kotlin/app/OrdersController.kt": (
        "package app\n@RestController\nclass OrdersController(private val client: WebClient) {\n"
        '  @GetMapping("/orders") fun list() = client.get()\n}\n'
    ),
    ".env": "SECRET=do-not-read\n",
    "build/generated/Big.kt": "@RestController class Generated\n",
    "node_modules/x/index.js": "axios.get('x')\n",
}


def make_repo(root: Path) -> Path:
    """Write the fixture repo under root and return root."""
    for rel, text in FILES.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    (root / "logo.bin").write_bytes(b"\0\1\2binary")
    return root
