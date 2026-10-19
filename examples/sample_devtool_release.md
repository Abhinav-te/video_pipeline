# Acme EdgeCache SDK v2.0 Release

High-performance distributed key-value cache engine engineered for edge runtimes.

## Quickstart & CLI Installation
Upgrade dependencies in a single step with zero peer dependency conflicts:

```bash
$ npm install @acme/edgecache@latest
$ npx acme init --cluster edge-us-east
```

## Migration Guide: v1 Callback Hell to v2 Async Promises
Migrate verbose legacy callback patterns into declarative, type-safe async streaming:

### Legacy v1 Client
```ts
const client = new LegacyClient({ timeout: 5000 });
client.connect((err, conn) => {
  if (err) throw err;
  conn.get("key", (e, val) => console.log(val));
});
```

### Modern v2 SDK
```ts
import { CacheClient } from "@acme/edgecache";

const cache = new CacheClient({ region: "auto" });
const user = await cache.getOrSet("user:123", async () => {
  return await fetchUserData("123");
});
```

## Global Edge Architecture
Global client requests resolve at nearest points-of-presence before touching origin databases:
- GET /v2/cache/keys - Fast key list retrieval
- POST /v2/cache/purge - Global cluster purge

## Production Benchmarks
- 99.9% cache hit rate in global production
- 1.4ms edge lookup latency across 40 regions
- 6x faster cold starts than legacy v1 client
- 90% reduction in client configuration boilerplate

