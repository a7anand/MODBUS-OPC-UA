# OPC UA security (PDF §8–9)

## Configuration (`gateway.yaml`)

```yaml
opcua:
  server:
    security_mode: sign_and_encrypt   # none | sign | sign_and_encrypt
    certificate_path: certificates/own/gateway_cert.pem
    private_key_path: certificates/own/gateway_key.pem
    username_password_auth: true
    server_users:
      - username: opcuser
        password: changeme
        admin: false
```

Generate or rotate certificates from **Web → Certificates** or `POST /api/certificates/generate` / `/api/certificates/rotate` (archives previous files under `certificates/own/archive/`).

## Policy matrix

`GET /api/opcua/security-matrix` returns the supported OPC Foundation policy URIs exposed per `security_mode`. The gateway maps:

| `security_mode` | Endpoints offered |
|-----------------|-------------------|
| `none` | NoSecurity only (lab warning in logs) |
| `sign` | Basic256Sha256, AES128, AES256 — Sign |
| `sign_and_encrypt` | Same policies — SignAndEncrypt |

Clients must trust the gateway certificate in `certificates/trusted/` or use UA Expert trust-on-first-use.

## REST vs OPC UA users

`security.users` (hashed) applies to **Web/REST** only. OPC UA username tokens use `opcua.server.server_users` (plaintext in YAML — protect the config file).
