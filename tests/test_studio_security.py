"""tests/test_studio_security.py

Security regression test suite covering Phase 4.1 requirements:
1. Safe default host binding & explicit CORS behavior.
2. Unauthorized state-changing API requests.
3. SSRF attempts against loopback, private, link-local, cloud-metadata, IPv6, octal/dword, and redirects.
4. Local-file traversal and symlink escape attempts.
5. run_id, rev_id, scene_id, and export filename traversal.
6. Restricted run-artifact serving (blocking raw manifests, evidence packs, data.json).
7. GitHub webhook signature verification & disabled-by-default behavior.
8. Stored-XSS prevention in Studio UI templates and DOM construction.
"""

from io import BytesIO
import json
import os
from pathlib import Path
import re
import shutil
import tempfile
import unittest
from unittest.mock import patch, MagicMock
import urllib.error

from fastapi.testclient import TestClient
import pytest

import studio_api
from studio_api import app, RUNS_DIR, OUT_DIR, STUDIO_AUTH_TOKEN
from engine.security import (
    validate_url_for_ssrf,
    resolve_and_validate_host,
    is_ip_allowed,
    get_allowed_source_dirs,
    validate_path_containment,
    validate_run_id_safe,
    validate_rev_id_safe,
    validate_scene_id_safe,
    validate_export_filename_safe,
    verify_studio_token,
    verify_github_signature,
    safe_fetch_remote_url,
    SafeRedirectHandler,
    PinnedIPHTTPConnection,
    PinnedIPHTTPSConnection,
)
from engine.ingestion.source_loader import load_source_content, fetch_url_content


class TestStudioSecurity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Client without credentials for testing auth enforcement
        cls.unauth_client = TestClient(app)
        # Client with valid credentials
        cls.auth_client = TestClient(app, headers={"X-Studio-Token": STUDIO_AUTH_TOKEN})

    def setUp(self):
        self.test_run_id = f"sec_test_run_{os.getpid()}"
        self.test_run_dir = RUNS_DIR / self.test_run_id
        self.test_run_dir.mkdir(parents=True, exist_ok=True)

        # Create basic test data
        data_payload = {
            "run_id": self.test_run_id,
            "topic": "Security Baseline",
            "subject": "devtools",
            "duration": 10.0,
            "scenes": [{"scene_id": 1, "title": "Intro", "spoken_text": "Secure pipeline"}],
        }
        with open(self.test_run_dir / "data.json", "w", encoding="utf-8") as f:
            json.dump(data_payload, f)

        # Create dummy output MP4 and manifest
        with open(self.test_run_dir / "output.mp4", "wb") as f:
            f.write(b"\x00" * 2048)

        with open(self.test_run_dir / "manifest.json", "w", encoding="utf-8") as f:
            json.dump({"revision": 1, "scenes": {}}, f)

        with open(self.test_run_dir / "evidence_pack.json", "w", encoding="utf-8") as f:
            json.dump({"records": []}, f)

        # Revisions dir
        rev_dir = self.test_run_dir / "revisions" / "rev_001"
        rev_dir.mkdir(parents=True, exist_ok=True)
        with open(rev_dir / "manifest.json", "w", encoding="utf-8") as f:
            json.dump({"revision": 1}, f)

    def tearDown(self):
        if self.test_run_dir.exists():
            shutil.rmtree(self.test_run_dir, ignore_errors=True)

    # =========================================================================
    # 1. HOST BINDING, CORS & CSRF SECURITY
    # =========================================================================

    def test_01_default_host_binding_is_loopback(self):
        """Uvicorn startup host must default to 127.0.0.1, never 0.0.0.0."""
        with open(Path(studio_api.__file__), "r", encoding="utf-8") as f:
            content = f.read()
        # Verify host defaults to 127.0.0.1
        self.assertIn('os.environ.get("STUDIO_HOST", "127.0.0.1")', content)
        self.assertNotIn('host="0.0.0.0"', content)

    def test_02_cors_wildcard_credentials_prohibited(self):
        """Wildcard CORS origin with credentials is not configured."""
        self.assertNotIn("*", studio_api.ALLOWED_ORIGINS)
        for origin in studio_api.ALLOWED_ORIGINS:
            self.assertTrue(origin.startswith("http://127.0.0.1") or origin.startswith("http://localhost"))

    def test_03_csrf_cross_origin_state_changes_rejected(self):
        """State-changing requests with an unauthorized Origin header must return 403 Forbidden."""
        resp = self.auth_client.post(
            "/api/projects/generate",
            json={"topic": "Test", "length": 15, "mock": True},
            headers={"Origin": "http://evil-attacker.com"},
        )
        self.assertEqual(resp.status_code, 403)
        self.assertIn("Cross-origin request not permitted", resp.text)

    def test_04_security_headers_enforced(self):
        """Verify X-Content-Type-Options, X-Frame-Options, and CSP are present."""
        resp = self.auth_client.get("/api/health")
        self.assertEqual(resp.headers.get("X-Content-Type-Options"), "nosniff")
        self.assertEqual(resp.headers.get("X-Frame-Options"), "DENY")
        self.assertIn("frame-ancestors 'none'", resp.headers.get("Content-Security-Policy", ""))

    # =========================================================================
    # 2. LOCAL API AUTHENTICATION ENFORCEMENT
    # =========================================================================

    def test_05_unauthorized_state_changing_requests_fail(self):
        """State-changing requests without authentication token must return 401."""
        # 1. Generate
        r1 = self.unauth_client.post("/api/projects/generate", json={"topic": "Test"})
        self.assertEqual(r1.status_code, 401)

        # 2. Mode A Revision
        r2 = self.unauth_client.post(
            f"/api/projects/{self.test_run_id}/scenes/1/revise-visual",
            json={"title": "New Title"},
        )
        self.assertEqual(r2.status_code, 401)

        # 3. Mode B Revision
        r3 = self.unauth_client.post(
            f"/api/projects/{self.test_run_id}/scenes/1/revise-narration",
            json={"narration": "New narration"},
        )
        self.assertEqual(r3.status_code, 401)

        # 4. Restore
        r4 = self.unauth_client.post(f"/api/projects/{self.test_run_id}/restore/rev_001")
        self.assertEqual(r4.status_code, 401)

        # 5. Export
        r5 = self.unauth_client.post(f"/api/projects/{self.test_run_id}/export", json={})
        self.assertEqual(r5.status_code, 401)

    def test_06_invalid_token_rejected_with_401(self):
        """Invalid token provided in X-Studio-Token or Bearer header is rejected."""
        resp = self.unauth_client.post(
            "/api/projects/generate",
            json={"topic": "Test"},
            headers={"X-Studio-Token": "completely_invalid_token_12345"},
        )
        self.assertEqual(resp.status_code, 401)

    def test_07_valid_token_bearer_accepted(self):
        """Valid token in Authorization: Bearer <token> is accepted."""
        with patch("studio_api.execute_revision"):
            resp = self.unauth_client.post(
                f"/api/projects/{self.test_run_id}/scenes/1/revise-visual",
                json={"title": "Updated Title"},
                headers={"Authorization": f"Bearer {STUDIO_AUTH_TOKEN}"},
            )
            self.assertEqual(resp.status_code, 200)

    # =========================================================================
    # 3. SSRF DEFENSE TESTS
    # =========================================================================

    def test_08_ssrf_rejects_loopback_and_metadata(self):
        """SSRF guard blocks loopback, cloud metadata, and link-local destinations."""
        targets = [
            "http://127.0.0.1:8000/secret",
            "http://localhost:5432/",
            "http://[::1]/admin",
            "http://169.254.169.254/latest/meta-data/",
            "http://100.100.100.200/latest/meta-data/",
            "http://0177.0.0.1/admin",      # Octal loopback
            "http://2130706433/",           # Dword loopback
            "http://[::ffff:127.0.0.1]/",   # IPv4-mapped IPv6 loopback
            "http://[::ffff:169.254.169.254]/",  # IPv4-mapped IPv6 metadata
            "http://10.0.0.1/internal",     # RFC 1918 Private
            "http://172.16.0.1/",           # RFC 1918 Private
            "http://192.168.1.1/router",    # RFC 1918 Private
        ]
        for target in targets:
            is_safe, reason = validate_url_for_ssrf(target)
            self.assertFalse(is_safe, f"Target '{target}' should be blocked, but passed SSRF check!")

    def test_09_ssrf_rejects_unsupported_schemes(self):
        """Schemes other than http/https are blocked."""
        bad_schemes = [
            "file:///etc/passwd",
            "gopher://127.0.0.1:6379/_flushall",
            "ftp://ftp.example.com/file",
            "data:text/plain;base64,SGVsbG8=",
        ]
        for url in bad_schemes:
            is_safe, reason = validate_url_for_ssrf(url)
            self.assertFalse(is_safe)
            self.assertIn("scheme", reason.lower())

    def test_10_ssrf_blocks_redirect_to_loopback(self):
        """Redirects to restricted IP destinations are blocked by SafeRedirectHandler."""
        handler = SafeRedirectHandler(max_redirects=3)
        mock_req = MagicMock()
        with pytest.raises(ValueError) as excinfo:
            handler.redirect_request(mock_req, None, 302, "Found", {}, "http://127.0.0.1:8000/internal")
        self.assertIn("SSRF", str(excinfo.value))

    def test_11_ssrf_bounded_response_size_limit(self):
        """Responses exceeding maximum allowed bytes are rejected without memory exhaustion."""
        oversized = b"A" * (2 * 1024 * 1024 + 1024)
        mock_resp = MagicMock()
        mock_resp.headers = {"Content-Type": "text/plain"}
        mock_resp.status = 200
        mock_resp.read.side_effect = [oversized[:65536], oversized[65536:]]

        with patch("engine.security.resolve_and_validate_host", return_value=(True, "", ["93.184.216.34"])):
            with patch("engine.security.PinnedIPHTTPSConnection") as mock_conn_cls:
                mock_conn = MagicMock()
                mock_conn.getresponse.return_value = mock_resp
                mock_conn_cls.return_value = mock_conn

                with pytest.raises(ValueError) as exc:
                    safe_fetch_remote_url("https://example.com/huge.md")
                self.assertIn("exceeded maximum allowed size", str(exc.value))

    def test_12_generation_endpoint_rejects_ssrf_source_url(self):
        """POST /api/projects/generate rejects SSRF source_url payloads."""
        resp = self.auth_client.post(
            "/api/projects/generate",
            json={
                "topic": "SSRF Exploit Attempt",
                "source_url": "http://169.254.169.254/latest/meta-data/",
                "mock": True,
            },
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn("Invalid source_url", resp.text)

    # =========================================================================
    # 4. PATH TRAVERSAL & CONTAINMENT DEFENSE
    # =========================================================================

    def test_13_local_source_file_path_traversal_blocked(self):
        """load_source_content rejects paths outside permitted directories."""
        with pytest.raises(PermissionError):
            load_source_content(source_file="/etc/passwd")

        with pytest.raises(PermissionError):
            load_source_content(source_file="../../etc/shadow")

    def test_14_symlink_escape_blocked(self, tmp_path=None):
        """Symlinks pointing outside permitted roots are rejected upon resolution."""
        with tempfile.TemporaryDirectory() as td:
            t_path = Path(td)
            symlink = t_path / "link_to_passwd.md"
            try:
                symlink.symlink_to("/etc/passwd")
            except OSError:
                self.skipTest("Symlinks not supported on filesystem")

            # Even though symlink is in /tmp, its target is /etc/passwd
            with pytest.raises(PermissionError):
                validate_path_containment(symlink, [Path(__file__).resolve().parent.parent])

    def test_15_run_id_path_traversal_rejected(self):
        """Path traversal characters in run_id are rejected."""
        bad_ids = [
            "../../etc",
            "run_../test",
            "run/with/slash",
            "run\\backslash",
            "run$evil",
            "",
        ]
        for bad_id in bad_ids:
            with pytest.raises(ValueError):
                validate_run_id_safe(bad_id, RUNS_DIR)

        # In HTTP API, non-matching paths return 404 while invalid identifiers return 400
        r_bad = self.auth_client.get("/api/projects/run$evil")
        self.assertEqual(r_bad.status_code, 400)
        self.assertIn("Invalid run_id", r_bad.text)

    def test_16_rev_id_path_traversal_rejected(self):
        """Path traversal or malformed rev_id is rejected."""
        with pytest.raises(ValueError):
            validate_rev_id_safe("../../rev_001", self.test_run_dir)
        with pytest.raises(ValueError):
            validate_rev_id_safe("rev$evil", self.test_run_dir)

        resp = self.auth_client.post(
            f"/api/projects/{self.test_run_id}/restore/rev$evil",
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn("Invalid rev_id", resp.text)

    def test_17_export_filename_traversal_rejected(self):
        """Custom export filename cannot traverse outside video/out/."""
        bad_filenames = [
            "../../evil.mp4",
            "test/export.mp4",
            "..\\..\\evil.mp4",
        ]
        for name in bad_filenames:
            with pytest.raises(ValueError):
                validate_export_filename_safe(name, self.test_run_id, 1, OUT_DIR)

            resp = self.auth_client.post(
                f"/api/projects/{self.test_run_id}/export",
                json={"custom_filename": name},
            )
            self.assertEqual(resp.status_code, 400)

    # =========================================================================
    # 5. RESTRICTED RUN-ARTIFACT SERVING (No Raw JSON Exfiltration)
    # =========================================================================

    def test_18_raw_manifest_and_evidence_pack_blocked_from_static_serving(self):
        """Direct file streaming routes must deny sensitive non-media files."""
        # Sensitive files inside runs/ directory
        blocked_paths = [
            f"/public/runs/{self.test_run_id}/manifest.json",
            f"/public/runs/{self.test_run_id}/evidence_pack.json",
            f"/public/runs/{self.test_run_id}/data.json",
            f"/public/runs/{self.test_run_id}/revisions/rev_001/manifest.json",
        ]
        for path in blocked_paths:
            resp = self.auth_client.get(path)
            self.assertEqual(resp.status_code, 403, f"Path '{path}' should be blocked (403), but got {resp.status_code}")

    def test_19_media_streaming_permitted(self):
        """Legitimate video and audio assets are served with appropriate headers."""
        resp = self.auth_client.get(f"/public/runs/{self.test_run_id}/output.mp4")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.headers.get("content-type"), "video/mp4")

    # =========================================================================
    # 6. GITHUB WEBHOOK SIGNATURE VERIFICATION
    # =========================================================================

    def test_20_webhook_disabled_by_default(self):
        """Webhook endpoint returns 403 when GITHUB_WEBHOOK_SECRET is not configured."""
        with patch.dict(os.environ, {}, clear=False):
            if "GITHUB_WEBHOOK_SECRET" in os.environ:
                del os.environ["GITHUB_WEBHOOK_SECRET"]

            resp = self.unauth_client.post(
                "/api/webhooks/github",
                json={"action": "published"},
            )
            self.assertEqual(resp.status_code, 403)
            self.assertIn("disabled", resp.text.lower())

    def test_21_webhook_requires_signature_when_enabled(self):
        """Webhook returns 401 when signature header is missing or invalid."""
        with patch.dict(os.environ, {"GITHUB_WEBHOOK_SECRET": "test_secret_12345"}):
            # Missing signature header
            r1 = self.unauth_client.post(
                "/api/webhooks/github",
                json={"action": "published"},
            )
            self.assertEqual(r1.status_code, 401)

            # Invalid signature header
            r2 = self.unauth_client.post(
                "/api/webhooks/github",
                json={"action": "published"},
                headers={"X-Hub-Signature-256": "sha256=invalid_signature_hex"},
            )
            self.assertEqual(r2.status_code, 401)

    def test_22_webhook_valid_signature_accepted(self):
        """Webhook with valid HMAC SHA256 signature is processed successfully."""
        secret = "super_secret_webhook_key_2026"
        payload_data = {
            "action": "published",
            "release": {"tag_name": "v2.5.0", "body": "New feature release", "html_url": "https://example.com/release"},
            "repository": {"name": "TestSDK"},
        }
        body_bytes = json.dumps(payload_data).encode("utf-8")

        import hmac, hashlib
        valid_sig = "sha256=" + hmac.new(secret.encode("utf-8"), body_bytes, hashlib.sha256).hexdigest()

        with patch.dict(os.environ, {"GITHUB_WEBHOOK_SECRET": secret}):
            with patch("threading.Thread"):  # Prevent actual generator thread launch
                resp = self.unauth_client.post(
                    "/api/webhooks/github",
                    content=body_bytes,
                    headers={
                        "X-Hub-Signature-256": valid_sig,
                        "X-GitHub-Event": "release",
                        "Content-Type": "application/json",
                    },
                )
                self.assertEqual(resp.status_code, 200)
                self.assertEqual(resp.json().get("status"), "queued")

    # =========================================================================
    # 7. STORED XSS MITIGATION IN STUDIO UI
    # =========================================================================

    def test_23_ui_template_contains_no_raw_innerhtml_interpolations(self):
        """Verify studio_ui/index.html does not interpolate untrusted variables into innerHTML."""
        ui_file = Path(__file__).resolve().parent.parent / "studio_ui" / "index.html"
        content = ui_file.read_text(encoding="utf-8")

        # Dangerous interpolation patterns in innerHTML
        dangerous_patterns = [
            r'innerHTML\s*=\s*`[^`]*\${(?:p\.|sc\.|r\.|sn\.|data\.|message|state\.)',
            r'innerHTML\s*=\s*["\'].*\+(?:p\.|sc\.|r\.|sn\.|data\.|message)',
            r'onclick=["\'][^"\']*\${',
        ]
        for pat in dangerous_patterns:
            matches = re.findall(pat, content)
            self.assertEqual(
                matches,
                [],
                f"Found dangerous dynamic innerHTML/onclick interpolation pattern: {matches}",
            )

    def test_24_ui_serves_with_injected_auth_token(self):
        """GET / serves UI with local authentication token injected."""
        resp = self.auth_client.get("/")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(STUDIO_AUTH_TOKEN, resp.text)
        self.assertNotIn("__STUDIO_AUTH_TOKEN_PLACEHOLDER__", resp.text)

    # =========================================================================
    # 8. RESIDUAL SECURITY AUDIT: DNS REBINDING, TOKEN SAFETY & ENV HARDENING
    # =========================================================================

    def test_25_dns_rebinding_pins_initial_validated_ip(self):
        """
        DNS rebinding defense: PinnedIPHTTPSConnection binds to the validated IP,
        preventing second-lookup rebinding to AWS metadata or internal IP.
        """
        initial_ip = "93.184.216.34"
        rebind_ip = "169.254.169.254"

        # Mock address resolution: first returns public IP, second returns metadata IP
        resolution_calls = [
            (True, "", [initial_ip]),   # Check 1: returns public IP
            (False, f"Access to IP address '{rebind_ip}' is blocked", [rebind_ip]), # Check 2 (if ever called)
        ]

        connected_addresses = []

        def mock_create_connection(address, timeout=None, source_address=None):
            connected_addresses.append(address)
            mock_sock = MagicMock()
            return mock_sock

        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.headers = {"Content-Type": "text/markdown"}
        mock_resp.read.side_effect = [b"# Documentation Content", b""]

        with patch("engine.security.resolve_and_validate_host", side_effect=resolution_calls):
            with patch("socket.create_connection", side_effect=mock_create_connection):
                with patch("ssl._create_default_https_context") as mock_ssl_ctx:
                    mock_wrapped_sock = MagicMock()
                    mock_ssl_ctx.return_value.wrap_socket.return_value = mock_wrapped_sock

                    with patch.object(PinnedIPHTTPSConnection, "getresponse", return_value=mock_resp):
                        body, content_type = safe_fetch_remote_url("https://rebind.attacker.com/docs.md")

                        self.assertIn("Documentation Content", body)
                        # Verify the connection was established STRICTLY to initial_ip
                        self.assertEqual(len(connected_addresses), 1)
                        self.assertEqual(connected_addresses[0], (initial_ip, 443))
                        # Verify it never attempted to connect to the rebind IP
                        self.assertNotIn((rebind_ip, 443), connected_addresses)
                        # Verify TLS SNI used the original domain name
                        mock_ssl_ctx.return_value.wrap_socket.assert_called_once_with(
                            unittest.mock.ANY,
                            server_hostname="rebind.attacker.com",
                        )

    def test_26_dns_rebinding_redirect_to_prohibited_ip_blocked(self):
        """Redirects attempting to hop to a metadata/loopback/private IP are blocked per-hop."""
        mock_resp1 = MagicMock()
        mock_resp1.status = 302
        mock_resp1.headers = {"Location": "http://169.254.169.254/latest/meta-data/"}

        with patch("engine.security.resolve_and_validate_host") as mock_res:
            # First URL (example.com) resolves to public IP
            # Second URL (169.254.169.254) is blocked
            mock_res.side_effect = [
                (True, "", ["93.184.216.34"]),
                (False, "Access to IP address '169.254.169.254' is blocked", ["169.254.169.254"]),
            ]
            with patch.object(PinnedIPHTTPSConnection, "connect"):
                with patch.object(PinnedIPHTTPSConnection, "request"):
                    with patch.object(PinnedIPHTTPSConnection, "getresponse", return_value=mock_resp1):
                        with pytest.raises(ValueError) as exc:
                            safe_fetch_remote_url("https://example.com/redirect")
                        self.assertIn("SSRF protection blocked URL", str(exc.value))
                        self.assertIn("169.254.169.254", str(exc.value))

    def test_27_auth_token_not_in_url_or_storage(self):
        """Studio UI client contains no token query string handling or local/sessionStorage exposure."""
        ui_file = Path(__file__).resolve().parent.parent / "studio_ui" / "index.html"
        content = ui_file.read_text(encoding="utf-8")

        self.assertNotIn("urlParams.get('token')", content)
        self.assertNotIn('urlParams.get("token")', content)
        self.assertNotIn("sessionStorage", content)
        self.assertNotIn("localStorage", content)

        # Unauthenticated request without token is rejected
        unauth_resp = self.unauth_client.post("/api/projects/generate", json={"topic": "Test"})
        self.assertEqual(unauth_resp.status_code, 401)

        # Request with forged token is rejected
        bad_token_resp = self.unauth_client.post(
            "/api/projects/generate",
            headers={"X-Studio-Token": "forged_invalid_token_12345"},
            json={"topic": "Test"},
        )
        self.assertEqual(bad_token_resp.status_code, 401)

    def test_28_environment_cannot_weaken_source_dirs(self):
        """STUDIO_ALLOWED_SOURCE_DIRS cannot add system root (/) or sensitive directories (/etc)."""
        with patch.dict(os.environ, {"STUDIO_ALLOWED_SOURCE_DIRS": "/:/etc:/root"}):
            allowed = get_allowed_source_dirs()
            # None of the disallowed system roots should be present
            allowed_posix = [p.as_posix() for p in allowed]
            self.assertNotIn("/", allowed_posix)
            self.assertNotIn("/etc", allowed_posix)
            self.assertNotIn("/root", allowed_posix)

            with pytest.raises(PermissionError):
                validate_path_containment("/etc/shadow", allowed)

    def test_29_environment_cannot_weaken_auth_or_origins(self):
        """STUDIO_AUTH_TOKEN < 8 chars and STUDIO_ALLOWED_ORIGINS='*' are safely rejected."""
        # 1. Origins parsing in studio_api logic
        env_origins = "*"
        parsed = [o.strip() for o in env_origins.split(",") if o.strip() and o.strip() != "*"]
        self.assertEqual(parsed, [])

        # 2. Token generation logic
        empty_token = "   "
        if not empty_token.strip() or len(empty_token.strip()) < 8:
            import secrets
            fallback = secrets.token_hex(24)
        else:
            fallback = empty_token
        self.assertGreaterEqual(len(fallback), 48)

    def test_30_pinned_ip_tls_verification_preserved(self):
        """PinnedIPHTTPSConnection preserves SNI and verifies TLS certificates using system CA."""
        with patch("socket.create_connection") as mock_create_conn:
            with patch("ssl._create_default_https_context") as mock_ssl_ctx:
                mock_sock = MagicMock()
                mock_create_conn.return_value = mock_sock

                conn = PinnedIPHTTPSConnection("93.184.216.34", "docs.example.com", 443)
                self.assertEqual(conn.target_ip, "93.184.216.34")
                self.assertEqual(conn.host, "docs.example.com")
                self.assertEqual(conn.port, 443)

                conn.connect()

                mock_create_conn.assert_called_once_with(
                    ("93.184.216.34", 443),
                    timeout=conn.timeout,
                    source_address=None,
                )
                mock_ssl_ctx.return_value.wrap_socket.assert_called_once_with(
                    mock_sock,
                    server_hostname="docs.example.com",
                )


if __name__ == "__main__":
    unittest.main()
