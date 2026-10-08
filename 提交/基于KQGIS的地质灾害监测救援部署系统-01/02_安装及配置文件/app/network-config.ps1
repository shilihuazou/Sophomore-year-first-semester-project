# Both web frontends listen on all network adapters by default.
# Django and KQGIS stay on 127.0.0.1 and are reached through frontend proxies.
$NetworkAccessConfig = @{
    BindAddress = '0.0.0.0'

    # Add the exact browser-facing origins used for public deployment.
    # Each value must contain only scheme + host + optional port.
    # Domain example:
    # PublicOrigins = @('https://admin.example.com', 'https://team.example.com')
    # Direct port-forwarding example:
    # PublicOrigins = @('http://203.0.113.10:5173', 'http://203.0.113.10:5174')
    PublicOrigins = @()
}
