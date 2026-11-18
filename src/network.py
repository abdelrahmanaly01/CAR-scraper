import ssl

import truststore


def create_ssl_context() -> ssl.SSLContext:
    """Use the operating system certificate store instead of only bundled CA files."""
    return truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
