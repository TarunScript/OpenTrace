"""
SSRF Protection Module
Enforces strict destination host validation to prevent Server-Side Request Forgery.
Blocks private networks, loopback addresses, link-local addresses, and cloud metadata APIs.
Provides connection-time DNS rebinding protection via custom socket transport.
"""
import ipaddress
import socket
from urllib.parse import urlparse
from typing import Union, Optional
import httpx
from httpcore import AnyIOBackend

from packages.osint_engine.core.exceptions import SSRFViolationError

# Blocked IP networks
BLOCKED_NETWORKS = [
    ipaddress.ip_network("0.0.0.0/8"),          # Current network ("this" network)
    ipaddress.ip_network("10.0.0.0/8"),         # RFC 1918 Private
    ipaddress.ip_network("100.64.0.0/10"),      # Shared Address Space / CGNAT
    ipaddress.ip_network("127.0.0.0/8"),        # Loopback
    ipaddress.ip_network("169.254.0.0/16"),     # Link-Local (Cloud metadata 169.254.169.254)
    ipaddress.ip_network("172.16.0.0/12"),      # RFC 1918 Private
    ipaddress.ip_network("192.0.0.0/24"),       # IETF Protocol Assignments
    ipaddress.ip_network("192.0.2.0/24"),       # TEST-NET-1
    ipaddress.ip_network("192.88.99.0/24"),     # 6to4 Relay Anycast
    ipaddress.ip_network("192.168.0.0/16"),     # RFC 1918 Private
    ipaddress.ip_network("198.18.0.0/15"),      # Benchmarking
    ipaddress.ip_network("198.51.100.0/24"),    # TEST-NET-2
    ipaddress.ip_network("203.0.113.0/24"),     # TEST-NET-3
    ipaddress.ip_network("224.0.0.0/4"),        # Multicast
    ipaddress.ip_network("240.0.0.0/4"),        # Reserved
    ipaddress.ip_network("255.255.255.255/32"), # Broadcast
    # IPv6
    ipaddress.ip_network("::1/128"),            # Loopback
    ipaddress.ip_network("::/128"),             # Unspecified
    ipaddress.ip_network("64:ff9b:1::/48"),     # Local-Use IPv4/IPv6 Translation
    ipaddress.ip_network("fc00::/7"),           # Unique Local Address (ULA)
    ipaddress.ip_network("fe80::/10"),          # Link-Local Unicast
    ipaddress.ip_network("ff00::/8"),           # Multicast
]

# Explicitly blocked hostnames
BLOCKED_HOSTNAMES = {
    "localhost",
    "localhost.localdomain",
    "metadata.google.internal",
    "metadata.internal",
    "instance-data",
    "169.254.169.254",
}

# Permitted public HTTP ports
ALLOWED_PORTS = {80, 443}


def parse_and_validate_ip(ip_str: str) -> Optional[Union[ipaddress.IPv4Address, ipaddress.IPv6Address]]:
    """
    Parses an IP address string, converting unusual formats (octal, decimal integer, hex,
    IPv4-mapped IPv6, classful shortened addresses, scoped IPv6) into canonical IP objects.
    Returns None if the string is not an IP literal.
    """
    clean = ip_str.split("%")[0].strip("[]").rstrip(".")
    if not clean:
        return None

    # 1. Decimal or Hex integer literals (e.g. 2130706433, 0x7f000001)
    if clean.isdigit() or (clean.lower().startswith("0x") and all(c in "0123456789abcdefABCDEFxX" for c in clean)):
        try:
            val = int(clean, 0)
            if 0 <= val <= 0xFFFFFFFF:
                return ipaddress.IPv4Address(val)
        except (ValueError, OverflowError):
            pass

    # 2. Octal, dotted hex, shortened classful (e.g. 0177.0.0.1, 017700000001, 127.1)
    try:
        if clean.count(".") > 0 or clean.isdigit():
            raw = socket.inet_aton(clean)
            dotted = socket.inet_ntoa(raw)
            return ipaddress.IPv4Address(dotted)
    except OSError:
        pass

    # 3. Standard IPv4 or IPv6 (including ::ffff:127.0.0.1)
    try:
        return ipaddress.ip_address(clean)
    except ValueError:
        return None


def is_ip_blocked(ip: Union[str, ipaddress.IPv4Address, ipaddress.IPv6Address]) -> bool:
    """
    Checks whether an IP address belongs to any restricted or private network.
    """
    if isinstance(ip, str):
        parsed_ip = parse_and_validate_ip(ip)
        if parsed_ip is None:
            return False
        ip = parsed_ip

    # If IPv4-mapped IPv6 (::ffff:x.x.x.x), check inner IPv4 as well
    if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped:
        if is_ip_blocked(ip.ipv4_mapped):
            return True

    # Check standard attributes
    if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast or ip.is_unspecified:
        return True

    for net in BLOCKED_NETWORKS:
        if ip in net:
            return True

    return False


def validate_target_url(url: str) -> None:
    """
    Validates that a URL does not resolve to an internal/private address, forbidden scheme,
    forbidden port, or cloud metadata service. Enforces Layer 1 pre-flight checks.
    Raises SSRFViolationError if URL is unsafe.
    """
    if "\x00" in url or "\r" in url or "\n" in url:
        raise SSRFViolationError("URL contains illegal control characters.")

    try:
        parsed = urlparse(url)
    except Exception as e:
        raise SSRFViolationError(f"Malformed URL: {e}")

    # Prohibit non-HTTP(S) schemes
    if parsed.scheme.lower() not in ("http", "https"):
        raise SSRFViolationError(f"Prohibited URL scheme: {parsed.scheme}. Only HTTP/HTTPS permitted.")

    # Prohibit embedded userinfo / credentials trick
    if parsed.username or parsed.password:
        raise SSRFViolationError("URLs with embedded user credentials (userinfo) are prohibited.")

    hostname = parsed.hostname
    if not hostname:
        raise SSRFViolationError("Target URL does not specify a valid hostname.")

    hostname_clean = hostname.lower().strip(".")

    # Prohibit non-standard ports
    port = parsed.port
    if port and port not in ALLOWED_PORTS:
        raise SSRFViolationError(f"Prohibited destination port: {port}. Only standard web ports (80, 443) are allowed.")

    # Check blocked hostnames and suffixes
    if hostname_clean in BLOCKED_HOSTNAMES:
        raise SSRFViolationError(f"Blocked hostname: {hostname}")

    for blocked_suffix in (".localhost", ".internal", ".local", ".invalid"):
        if hostname_clean.endswith(blocked_suffix):
            raise SSRFViolationError(f"Blocked internal domain suffix: {hostname}")

    # Check if hostname is an IP literal in any encoding
    ip_literal = parse_and_validate_ip(hostname)
    if ip_literal is not None:
        if is_ip_blocked(ip_literal):
            raise SSRFViolationError(f"Target IP {ip_literal} is within restricted/private network.")
        return

    # Hostname is a domain name: perform DNS pre-resolution
    try:
        addr_info = socket.getaddrinfo(hostname, None, proto=socket.IPPROTO_TCP)
        for entry in addr_info:
            ip_str = entry[4][0]
            resolved_ip = parse_and_validate_ip(ip_str)
            if resolved_ip and is_ip_blocked(resolved_ip):
                raise SSRFViolationError(
                    f"Resolved address {resolved_ip} for host {hostname} belongs to restricted network."
                )
    except socket.gaierror:
        # DNS lookup failure will be handled by connection transport
        pass


class SSRFProtectedNetworkBackend(AnyIOBackend):
    """
    Custom AnyIO network backend that enforces connection-time IP validation.
    Eliminates DNS rebinding (TOCTOU) by checking the connected socket peer IP
    before transmitting HTTP data.
    """
    async def connect_tcp(self, host: str, port: int, *args, **kwargs):
        # 1. Pre-connection check on destination host
        ip_literal = parse_and_validate_ip(host)
        if ip_literal and is_ip_blocked(ip_literal):
            raise SSRFViolationError(f"Connection blocked: Destination IP {ip_literal} is in restricted range.")

        # 2. Establish TCP connection
        stream = await super().connect_tcp(host, port, *args, **kwargs)

        # 3. Inspect connected socket peer IP (connection-time DNS rebinding defense)
        try:
            peer = stream.get_extra_info("peername")
            if peer and len(peer) > 0:
                peer_ip_str = str(peer[0])
                peer_ip = parse_and_validate_ip(peer_ip_str)
                if peer_ip and is_ip_blocked(peer_ip):
                    await stream.aclose()
                    raise SSRFViolationError(
                        f"Connection-time DNS rebinding blocked: Connected socket peer {peer_ip} is in restricted range."
                    )
        except Exception as e:
            if isinstance(e, SSRFViolationError):
                raise
            # If peer inspection failed, fail safely
            await stream.aclose()
            raise SSRFViolationError(f"Failed to verify socket peer identity: {e}")

        return stream


class SSRFProtectedTransport(httpx.AsyncHTTPTransport):
    """
    Async HTTP Transport equipped with SSRFProtectedNetworkBackend.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._pool._network_backend = SSRFProtectedNetworkBackend()
