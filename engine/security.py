"""engine/security.py

Security module providing:
1. SSRF Guard: Scheme validation, IP resolution & blacklist enforcement, redirect checking, bounded reading.
2. Path Traversal Guard: Directory containment validation, strict identifier enforcement (run_id, rev_id, scene_id, export filename).
3. Authentication & CSRF Guard: Constant-time token verification, permitted origin checks.
4. GitHub Webhook Security: HMAC SHA-256 signature verification.
"""

from __future__ import annotations

import gzip
import hashlib
import hmac
import http.client
import ipaddress
import os
from pathlib import Path
import re
import socket
import ssl
import tempfile
from typing import Any, Dict, List, Optional, Set, Tuple, Union
import urllib.parse
import urllib.request


# ===========================================================================
# 1. SSRF PROTECTION & SAFE REMOTE FETCHING
# ===========================================================================

ALLOWED_SCHEMES: Set[str] = {"http", "https"}

ALLOWED_CONTENT_TYPES: Set[str] = {
    "text/plain",
    "text/markdown",
    "text/html",
    "application/xhtml+xml",
    "application/xml",
    "text/xml",
    "application/json",
}

MAX_REMOTE_CONTENT_BYTES: int = 2 * 1024 * 1024  # 2 MB limit
DEFAULT_FETCH_TIMEOUT: int = 15  # seconds

DISALLOWED_HOSTNAMES: Set[str] = {
    "localhost",
    "metadata.google.internal",
    "instance-data",
}

DISALLOWED_SPECIFIC_IPS: Set[str] = {
    "169.254.169.254",  # AWS/GCP/Azure/DigitalOcean metadata
    "100.100.100.200",  # Alibaba Cloud metadata
    "169.254.170.2",    # AWS ECS task metadata
    "fd00:ec2::254",    # AWS IPv6 metadata
}

# RFC 6598 Shared Address Space (Carrier Grade NAT)
SHARED_CGNAT_NETWORK = ipaddress.ip_network("100.64.0.0/10")


def is_ip_allowed(ip_obj: Union[ipaddress.IPv4Address, ipaddress.IPv6Address]) -> bool:
    """Returns True only if ip_obj is a publicly routable, non-reserved, non-metadata IP."""
    # Unpack IPv4-mapped IPv6 addresses (e.g. ::ffff:127.0.0.1)
    if isinstance(ip_obj, ipaddress.IPv6Address) and ip_obj.ipv4_mapped:
        ip_obj = ip_obj.ipv4_mapped

    if ip_obj.is_loopback:
        return False
    if ip_obj.is_private:
        return False
    if ip_obj.is_link_local:
        return False
    if ip_obj.is_multicast:
        return False
    if ip_obj.is_reserved:
        return False
    if ip_obj.is_unspecified:
        return False

    ip_str = str(ip_obj)
    if ip_str in DISALLOWED_SPECIFIC_IPS:
        return False

    if isinstance(ip_obj, ipaddress.IPv4Address) and ip_obj in SHARED_CGNAT_NETWORK:
        return False

    return True


def resolve_and_validate_host(hostname: str, port: int = 443) -> Tuple[bool, str, List[str]]:
    """
    Resolves hostname to IP addresses and checks every IP against the blacklist.
    Returns (is_valid, error_message, resolved_ips).
    """
    if not hostname or not hostname.strip():
        return False, "Empty hostname", []

    cleaned_host = hostname.strip().lower()

    if (
        cleaned_host in DISALLOWED_HOSTNAMES
        or cleaned_host.endswith(".localhost")
        or cleaned_host.endswith(".internal")
        or cleaned_host.endswith(".local")
    ):
        return False, f"Access to internal hostname '{cleaned_host}' is blocked", []

    # First attempt direct IP parse (in case hostname is an IP string)
    try:
        direct_ip = ipaddress.ip_address(cleaned_host.strip("[]"))
        if not is_ip_allowed(direct_ip):
            return False, f"Access to IP address '{cleaned_host}' is blocked", [str(direct_ip)]
        return True, "", [str(direct_ip)]
    except ValueError:
        pass

    # Resolve via DNS
    try:
        addr_infos = socket.getaddrinfo(cleaned_host, port, socket.AF_UNSPEC, socket.SOCK_STREAM)
    except socket.gaierror as e:
        return False, f"Hostname resolution failed: {e}", []
    except Exception as e:
        return False, f"Network error during resolution: {e}", []

    if not addr_infos:
        return False, f"No IP addresses resolved for hostname '{cleaned_host}'", []

    resolved_ips: List[str] = []
    for info in addr_infos:
        sockaddr = info[4]
        ip_str = sockaddr[0]
        resolved_ips.append(ip_str)
        try:
            ip_obj = ipaddress.ip_address(ip_str)
            if not is_ip_allowed(ip_obj):
                return False, f"Resolved IP '{ip_str}' is in a prohibited range", resolved_ips
        except ValueError:
            return False, f"Invalid resolved IP format '{ip_str}'", resolved_ips

    return True, "", resolved_ips


def validate_url_for_ssrf(url: str) -> Tuple[bool, str]:
    """
    Validates a URL before making an HTTP request.
    Enforces allowed schemes, valid hostnames, and resolves/checks IPs.
    Returns (is_safe, failure_reason).
    """
    if not url or not url.strip():
        return False, "URL is empty"

    url_str = url.strip()
    try:
        parsed = urllib.parse.urlsplit(url_str)
    except Exception as e:
        return False, f"Malformed URL: {e}"

    # If scheme was omitted, default to https
    if not parsed.scheme:
        url_str = "https://" + url_str
        try:
            parsed = urllib.parse.urlsplit(url_str)
        except Exception as e:
            return False, f"Malformed URL: {e}"

    scheme = parsed.scheme.lower()
    if scheme not in ALLOWED_SCHEMES:
        return False, f"Prohibited URL scheme '{scheme}'. Only http and https are permitted."

    hostname = parsed.hostname
    if not hostname:
        return False, "URL is missing a valid hostname"

    # Reject URLs with userinfo/embedded credentials
    if parsed.username or parsed.password:
        return False, "URLs with embedded credentials are not permitted"

    port = parsed.port or (443 if scheme == "https" else 80)
    is_safe, reason, _ = resolve_and_validate_host(hostname, port)
    return is_safe, reason


class SafeRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Subclass of HTTPRedirectHandler that re-validates redirect destinations for SSRF."""

    def __init__(self, max_redirects: int = 3):
        super().__init__()
        self.max_redirects = max_redirects
        self.redirect_count = 0

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        self.redirect_count += 1
        if self.redirect_count > self.max_redirects:
            raise ValueError(f"Too many redirects (limit is {self.max_redirects})")

        is_safe, reason = validate_url_for_ssrf(newurl)
        if not is_safe:
            raise ValueError(f"SSRF protection blocked redirect to '{newurl}': {reason}")

        return super().redirect_request(req, fp, code, msg, headers, newurl)


class PinnedIPHTTPConnection(http.client.HTTPConnection):
    """
    HTTPConnection that connects directly to a pre-validated IP address,
    preventing DNS rebinding (TOCTOU) while preserving the original Host header.
    """

    def __init__(
        self,
        target_ip: str,
        host: str,
        port: int = 80,
        timeout: float = DEFAULT_FETCH_TIMEOUT,
    ):
        super().__init__(host=host, port=port, timeout=timeout)
        self.target_ip = target_ip

    def connect(self) -> None:
        self.sock = socket.create_connection(
            (self.target_ip, self.port),
            timeout=self.timeout,
            source_address=self.source_address,
        )


class PinnedIPHTTPSConnection(http.client.HTTPSConnection):
    """
    HTTPSConnection that connects directly to a pre-validated IP address,
    preventing DNS rebinding (TOCTOU) while preserving SNI and strict TLS
    hostname/certificate verification against the original hostname.
    """

    def __init__(
        self,
        target_ip: str,
        host: str,
        port: int = 443,
        timeout: float = DEFAULT_FETCH_TIMEOUT,
        context: Optional[ssl.SSLContext] = None,
    ):
        super().__init__(host=host, port=port, timeout=timeout, context=context)
        self.target_ip = target_ip

    def connect(self) -> None:
        sock = socket.create_connection(
            (self.target_ip, self.port),
            timeout=self.timeout,
            source_address=self.source_address,
        )
        ctx = self._context if getattr(self, "_context", None) is not None else ssl.create_default_context()
        self.sock = ctx.wrap_socket(sock, server_hostname=self.host)


def safe_read_response(resp: Any, max_bytes: int = MAX_REMOTE_CONTENT_BYTES) -> Tuple[str, str]:
    """
    Reads HTTP response with bounded size check, content-type enforcement,
    and safe gzip decompression.
    Returns (body_text, content_type).
    """
    content_type_header = resp.headers.get("Content-Type", "").lower()
    main_type = content_type_header.split(";")[0].strip()

    if main_type and main_type not in ALLOWED_CONTENT_TYPES:
        raise ValueError(f"Unsupported content type '{main_type}'. Expected text documentation.")

    charset = "utf-8"
    if "charset=" in content_type_header:
        charset = content_type_header.split("charset=")[-1].split(";")[0].strip()

    chunks: List[bytes] = []
    total_bytes = 0
    chunk_size = 65536

    while True:
        chunk = resp.read(chunk_size)
        if not chunk:
            break
        total_bytes += len(chunk)
        if total_bytes > max_bytes:
            raise ValueError(f"Remote content exceeded maximum allowed size of {max_bytes} bytes")
        chunks.append(chunk)

    raw_bytes = b"".join(chunks)

    # Decompress gzip if present
    content_encoding = resp.headers.get("Content-Encoding", "").lower()
    if content_encoding == "gzip":
        try:
            raw_bytes = gzip.decompress(raw_bytes)
            if len(raw_bytes) > max_bytes:
                raise ValueError(f"Decompressed content exceeded maximum allowed size of {max_bytes} bytes")
        except Exception as e:
            if "exceeded maximum" in str(e):
                raise

    try:
        body = raw_bytes.decode(charset, errors="replace")
    except Exception:
        body = raw_bytes.decode("utf-8", errors="replace")

    return body, main_type


def safe_fetch_remote_url(
    url: str,
    timeout_sec: int = DEFAULT_FETCH_TIMEOUT,
    max_bytes: int = MAX_REMOTE_CONTENT_BYTES,
    max_redirects: int = 3,
) -> Tuple[str, str]:
    """
    Safely fetches a remote URL with:
    - Pre-request SSRF validation on scheme and IP address ranges.
    - Pinned IP connections: connects directly to the validated IP, eliminating DNS rebinding TOCTOU.
    - Preserved TLS certificate & hostname verification via SNI and default SSLContext.
    - Safe redirect tracking with per-hop SSRF validation and IP pinning.
    - Bounded response body reading (enforcing max_bytes).
    - Allowed Content-Type validation (rejects binary/executable content).
    Returns (body_text, content_type).
    """
    current_url = url.strip()
    parsed = urllib.parse.urlsplit(current_url)
    if not parsed.scheme:
        current_url = "https://" + current_url

    redirect_count = 0
    visited_urls: Set[str] = set()

    while True:
        if redirect_count > max_redirects:
            raise ValueError(f"Too many redirects (limit is {max_redirects})")

        if current_url in visited_urls:
            raise ValueError(f"Circular redirect detected to '{current_url}'")
        visited_urls.add(current_url)

        parsed = urllib.parse.urlsplit(current_url)
        scheme = (parsed.scheme or "https").lower()
        if scheme not in ALLOWED_SCHEMES:
            raise ValueError(f"Prohibited URL scheme '{scheme}'. Only http and https are permitted.")

        hostname = parsed.hostname
        if not hostname:
            raise ValueError("URL is missing a valid hostname")

        if parsed.username or parsed.password:
            raise ValueError("URLs with embedded credentials are not permitted")

        port = parsed.port or (443 if scheme == "https" else 80)

        # 1. Resolve and validate all IPs (rejecting loopback, private, link-local, cloud metadata)
        is_safe, reason, resolved_ips = resolve_and_validate_host(hostname, port)
        if not is_safe:
            raise ValueError(f"SSRF protection blocked URL '{current_url}': {reason}")

        if not resolved_ips:
            raise ValueError(f"No IP addresses resolved for hostname '{hostname}'")

        # 2. Pin to first validated safe IP address (eliminates DNS rebinding)
        target_ip = resolved_ips[0]

        # 3. Path and query
        path = parsed.path or "/"
        if parsed.query:
            path = f"{path}?{parsed.query}"

        # 4. Connect directly to target_ip using Pinned Connection
        conn: Union[PinnedIPHTTPConnection, PinnedIPHTTPSConnection]
        if scheme == "https":
            conn = PinnedIPHTTPSConnection(
                target_ip=target_ip,
                host=hostname,
                port=port,
                timeout=timeout_sec,
            )
        else:
            conn = PinnedIPHTTPConnection(
                target_ip=target_ip,
                host=hostname,
                port=port,
                timeout=timeout_sec,
            )

        try:
            conn.connect()
            host_header = hostname if (port in (80, 443)) else f"{hostname}:{port}"
            headers = {
                "Host": host_header,
                "User-Agent": "Mozilla/5.0 (compatible; VideoGenPipeline/1.0)",
                "Accept": "text/html,text/plain,text/markdown,application/json,*/*;q=0.8",
                "Connection": "close",
            }
            conn.request("GET", path, headers=headers)
            resp = conn.getresponse()

            # Handle Redirects (301, 302, 303, 307, 308)
            if resp.status in {301, 302, 303, 307, 308}:
                location = resp.headers.get("Location")
                if not location:
                    raise ValueError(f"Redirect HTTP {resp.status} received without Location header")
                next_url = urllib.parse.urljoin(current_url, location)
                redirect_count += 1
                current_url = next_url
                conn.close()
                continue

            if resp.status >= 400:
                raise ValueError(f"Remote fetch failed: HTTP {resp.status} {resp.reason}")

            return safe_read_response(resp, max_bytes=max_bytes)
        except (ValueError,):
            raise
        except Exception as e:
            raise ValueError(f"Connection failed for '{current_url}': {e}")
        finally:
            conn.close()


# ===========================================================================
# 2. PATH TRAVERSAL & CONTAINMENT GUARDS
# ===========================================================================

DISALLOWED_SOURCE_ROOTS: Set[str] = {
    "/",
    "/etc",
    "/root",
    "/var",
    "/usr",
    "/bin",
    "/sbin",
    "/boot",
    "/dev",
    "/proc",
    "/sys",
}


def get_allowed_source_dirs(repo_root: Optional[Path] = None) -> List[Path]:
    """Returns canonical list of permitted directories for local source file reading."""
    if repo_root is None:
        repo_root = Path(__file__).resolve().parent.parent

    allowed: List[Path] = [
        repo_root.resolve(),
        Path(tempfile.gettempdir()).resolve(),
    ]

    # Optional environment override for additional allowed source paths
    extra_dirs = os.environ.get("STUDIO_ALLOWED_SOURCE_DIRS")
    if extra_dirs:
        for d in extra_dirs.split(os.pathsep):
            clean_d = d.strip()
            if not clean_d:
                continue
            p = Path(clean_d).resolve()
            # Explicitly disallow root filesystem and sensitive system directories
            if p.as_posix() in DISALLOWED_SOURCE_ROOTS or p == Path(p.anchor):
                continue
            if p.exists() and p.is_dir():
                allowed.append(p)

    return allowed


def validate_path_containment(target_path: Union[str, Path], allowed_roots: List[Path]) -> Path:
    """
    Resolves target_path (following symlinks) and confirms it is strictly
    contained within at least one of the allowed_roots.
    Raises PermissionError if path escapes allowed boundaries.
    """
    resolved = Path(target_path).resolve()
    for root in allowed_roots:
        root_resolved = root.resolve()
        try:
            resolved.relative_to(root_resolved)
            return resolved
        except ValueError:
            continue

    raise PermissionError(
        f"Access denied: path '{target_path}' resolves outside permitted directories."
    )


def is_safe_identifier(val: str) -> bool:
    """Validates that val contains only safe alphanumeric, underscore, or hyphen characters."""
    if not val or not isinstance(val, str):
        return False
    return bool(re.match(r"^[a-zA-Z0-9_\-]+$", val.strip()))


def validate_run_id_safe(run_id: str, runs_dir: Path) -> Path:
    """Validates run_id identifier and verifies containment within runs_dir."""
    clean_id = str(run_id).strip()
    if not is_safe_identifier(clean_id):
        raise ValueError(f"Invalid run_id format: '{run_id}'. Must be alphanumeric with '_' or '-'.")

    run_dir = (runs_dir / clean_id).resolve()
    if not run_dir.is_relative_to(runs_dir.resolve()):
        raise ValueError(f"Path traversal detected in run_id: '{run_id}'.")
    return run_dir


def validate_rev_id_safe(rev_id: str, run_dir: Path) -> Path:
    """Validates rev_id format (e.g. rev_001) and containment within run_dir/revisions."""
    clean_id = str(rev_id).strip()
    if not re.match(r"^rev_\d+$", clean_id):
        raise ValueError(f"Invalid rev_id format: '{rev_id}'. Must match 'rev_XXX'.")

    revs_dir = (run_dir / "revisions").resolve()
    snap_dir = (revs_dir / clean_id).resolve()
    if not snap_dir.is_relative_to(revs_dir):
        raise ValueError(f"Path traversal detected in rev_id: '{rev_id}'.")
    return snap_dir


def validate_scene_id_safe(scene_id: Union[int, str]) -> int:
    """Validates scene_id is a valid integer identifier (1-9999)."""
    if isinstance(scene_id, int):
        if scene_id < 1 or scene_id > 9999:
            raise ValueError(f"Invalid scene_id value: {scene_id}")
        return scene_id

    s = str(scene_id).strip()
    m = re.match(r"^(?:scene_)?(\d+)$", s)
    if not m:
        raise ValueError(f"Invalid scene_id format: '{scene_id}'")
    val = int(m.group(1))
    if val < 1 or val > 9999:
        raise ValueError(f"Invalid scene_id value: {val}")
    return val


def validate_export_filename_safe(
    filename: Optional[str],
    run_id: str,
    current_rev: int,
    out_dir: Path,
) -> Path:
    """Validates export filename to prevent directory traversal outside out_dir."""
    if filename and filename.strip():
        raw_name = filename.strip()
        # Explicitly reject separators and traversal tokens
        if "/" in raw_name or "\\" in raw_name or ".." in raw_name:
            raise ValueError("Export filename cannot contain path separators or '..'")

        clean_name = re.sub(r"[^a-zA-Z0-9_\-\.]", "_", raw_name)
        if not clean_name.lower().endswith(".mp4"):
            clean_name += ".mp4"
    else:
        clean_name = f"{run_id}_final_v{current_rev}.mp4"

    target_path = (out_dir / clean_name).resolve()
    if not target_path.is_relative_to(out_dir.resolve()):
        raise ValueError("Export path traversal detected")

    return target_path


# ===========================================================================
# 3. LOCAL AUTHENTICATION & CSRF PROTECTION
# ===========================================================================

def verify_studio_token(provided_token: Optional[str], expected_token: str) -> bool:
    """Performs constant-time comparison of the Studio authentication token."""
    if not provided_token or not expected_token:
        return False
    return hmac.compare_digest(provided_token.strip(), expected_token.strip())


def is_origin_allowed(origin: Optional[str], allowed_origins: List[str]) -> bool:
    """Verifies that an HTTP Origin header is in the permitted origins list."""
    if not origin:
        return True  # Non-browser or same-origin direct request without Origin header
    origin_clean = origin.strip().rstrip("/")
    for allowed in allowed_origins:
        if origin_clean == allowed.strip().rstrip("/"):
            return True
    return False


# ===========================================================================
# 4. GITHUB WEBHOOK SIGNATURE VERIFICATION
# ===========================================================================

def verify_github_signature(
    body_bytes: bytes,
    signature_header: Optional[str],
    secret: str,
) -> bool:
    """
    Verifies GitHub X-Hub-Signature-256 header using constant-time comparison.
    Format expected: 'sha256=<hex_digest>'
    """
    if not signature_header or not secret:
        return False

    sig = signature_header.strip()
    if not sig.startswith("sha256="):
        return False

    expected_hash = hmac.new(
        secret.encode("utf-8"),
        body_bytes,
        hashlib.sha256,
    ).hexdigest()

    expected_sig = f"sha256={expected_hash}"
    return hmac.compare_digest(sig, expected_sig)
