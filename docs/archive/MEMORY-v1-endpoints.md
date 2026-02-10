# Claude Code Memory

## Key Patterns & Learnings

### Multi-Provider Media Router (2026-02-07) - NEW
- **Multi-Provider Video Router** at `execution/multi_provider_video_router.py`
- **Multi-Provider Image Router** at `execution/multi_provider_image_router.py`
- **Purpose**: Cost optimization + rate limit mitigation across multiple AI providers

**Video Providers (by tier)**:
| Tier | Provider | Cost | Notes |
|------|----------|------|-------|
| FREE | MoviePy | $0 | Local, 70-85% success |
| BUDGET | Hailuo Fast (fal.ai) | $0.03/video | Minimax via fal.ai |
| STANDARD | Creatomate | $0.05/video | Reliable fallback |
| STANDARD | Grok Imagine | $0.70/10s | xAI direct text-to-video |
| PREMIUM | Veo 3 Fast (Kie.ai) | $0.40/8s | Google via third-party |
| PREMIUM | Veo 3 (Kie.ai) | $2.00/8s | Highest quality |

**Image Providers (by tier)**:
| Tier | Provider | Cost | Notes |
|------|----------|------|-------|
| BUDGET | Replicate SD | $0.003/img | Cheapest for bulk |
| STANDARD | Grok Aurora | $0.07/img | xAI primary |
| STANDARD | Ideogram | $0.05/img | Good text rendering |
| PREMIUM | DALL-E 3 | $0.08/img | OpenAI highest quality |

**Features**:
- Automatic rate limit tracking (hourly/daily)
- Per-provider cost tracking with 30-day history
- Fallback chains per quality tier
- Force provider override option
- Statistics and analytics

**API Keys Required**:
- `XAI_API_KEY` - xAI/Grok (images + video)
- `FAL_API_KEY` - Hailuo/Minimax via fal.ai
- `KIE_API_KEY` - Veo 3 via Kie.ai
- `REPLICATE_API_TOKEN` - Stable Diffusion
- `OPENAI_API_KEY` - DALL-E 3
- `IDEOGRAM_API_KEY` - Ideogram

**Usage**:
```bash
# Video generation with tier
python execution/multi_provider_video_router.py --prompt "Fitness workout" --tier standard

# Image generation with count
python execution/multi_provider_image_router.py --prompt "Hero image" --count 4 --tier budget

# View stats
python execution/multi_provider_video_router.py --stats
python execution/multi_provider_image_router.py --stats
```

**Note**: Banana.dev shut down March 2024 - not available.

---

### n8n Agent Orchestrator v5.1-Ultra (2026-02-07) - CURRENT - Maximum Capability & Efficiency
- **Universal Agent Orchestrator** deployed to EC2 n8n (ID: `1s52PkA1lY1lHfGP`)
- Python Bridge API v5.1 at `execution/agent_bridge_api.py` runs on EC2 localhost:5010
- Webhook: `http://34.193.98.97:5678/webhook/agent/execute`
- Exported to: `projects/shared/n8n-workflows/agent-orchestrator-v51-ultra.json`

**v5.1-Ultra Optimization Summary**:
| Metric | v4.15 | v4.18-Ultra | v5.1-Ultra | Net Improvement |
|--------|-------|-------------|------------|-----------------|
| Systems | 23 overlap | 13 unified | **21 total** | **All unique** |
| New Endpoints | - | +45 | **+28** | **73 new** |
| Capabilities | Base | Optimized | **Maximum** | **Enterprise** |

**v5.1-Ultra NEW Features (8 Advanced Systems)**:

1. **Multi-Level Cache (L1/L2/L3)**:
   - `/v51/cache/get`, `/v51/cache/set`, `/v51/cache/stats`
   - Hot/warm/cold hierarchy with automatic promotion/demotion
   - LRU eviction per level

2. **Predictive Preloading Engine**:
   - `/v51/predict/record`, `/v51/predict/next`, `/v51/predict/stats`
   - Pattern learning from request history
   - Confidence-based preload decisions

3. **Load Shedding**:
   - `/v51/shed/check`, `/v51/shed/status`
   - Priority-based request dropping under pressure
   - CPU/memory/queue threshold monitoring

4. **Backpressure Management**:
   - `/v51/backpressure/signal`, `/v51/backpressure/query`
   - Upstream signaling when overloaded
   - Delay/reject recommendations

5. **Deadline Propagation**:
   - `/v51/deadline/set`, `/v51/deadline/remaining`
   - Timeout inheritance across request chains
   - Automatic propagation to sub-requests

6. **Resource Quotas (Per-Tenant)**:
   - `/v51/quota/create`, `/v51/quota/check`, `/v51/quota/usage`
   - Per-tenant resource limits
   - Usage tracking and alerts

7. **Cost Attribution**:
   - `/v51/cost/start`, `/v51/cost/record`, `/v51/cost/total`
   - Per-request cost tracking
   - Tenant cost aggregation

8. **Smart GC Scheduler**:
   - `/v51/gc/schedule`, `/v51/gc/status`
   - Traffic-aware garbage collection
   - Low-traffic period optimization

**v5.1-Ultra Dashboard**: `/v51/dashboard` - Unified view of all 8 systems

**Previous Features (All Retained)**:
- v4.18-Ultra: Auto-Tuning, Efficiency Score, Optimization Advisor
- v5 Consolidated: Rate Controller, Resilience, Observability, Traffic, Dedup
- v4.18 Performance: Pooling, Compression, Lazy Loading, Memory, Query, Precompute
- v4.17 Resilience: Distributed Locking, Request Batching, Smart Retry, Hedging

**Unique v4.17 Features (kept as nodes)**:
1. **Distributed Locking**: `/v417/lock/*` - Cross-instance coordination with TTL
2. **Request Batching**: `/v417/batch/*` - Combine requests for efficiency
3. **Request Correlation**: `/v417/correlate/*` - End-to-end tracing

**Enhanced v5 Systems (absorbed v4.17)**:
- `/v5/rate/adaptive` - Auto-adjusting rate limits based on backend health
- `/v5/resilience/hedge` - Request hedging (parallel requests, fastest wins)
- `/v5/resilience/degrade` - Graceful degradation with tiered service levels
- `/v5/traffic/mirror` - Shadow traffic with sampling for testing
- `/v5/observe/correlate` - End-to-end request correlation and tracing
- `/v5/status` - Comprehensive health check for all v5 systems

**v4.18 Performance Features** (still available):
- **Connection Pooling**: `/v418/pool/*` - Reuse HTTP/DB connections
- **Request Compression**: `/v418/compress/*` - Gzip/deflate/brotli
- **Lazy Loading**: `/v418/lazy/*` - On-demand module loading
- **Memory Optimization**: `/v418/memory/*` - GC tuning, profiling
- **Query Optimization**: `/v418/query/*` - Caching and analysis
- **Precomputation Engine**: `/v418/precompute/*` - Cache expensive ops
- **Resource Pooling**: `/v418/resource/*` - Thread/connection pools
- **Hot Path Optimization**: `/v418/hotpath/*` - Frequently-used paths
- **Zero-Copy Operations**: `/v418/zerocopy/*` - Buffer sharing
- **Request Pipelining**: `/v418/pipeline/*` - Chain operations
- **Async Batch Processing**: `/v418/batch/*` - Parallel processing
- **Performance Dashboard**: `/v418/dashboard` - Unified monitoring

**v4.17 Features (ADVANCED RESILIENCE)**:
- **Distributed Locking**: Coordinate across instances with TTL-based locks
- **Request Batching**: Combine multiple requests for efficient processing
- **Smart Retry with Jitter**: Exponential backoff with randomization to prevent thundering herd
- **Request Hedging**: Send parallel requests, use first response for latency optimization
- **Circuit Breaker Pro**: Half-open state with configurable thresholds and recovery
- **Graceful Degradation**: Fallback strategies with tiered service levels
- **Traffic Mirroring**: Copy traffic to shadow systems for testing/analysis
- **Adaptive Rate Limiting**: Auto-adjust limits based on backend health
- **Request Correlation**: Link related requests across services for tracing

**v4.17 Endpoints**:
- `/v417/lock/acquire`, `/v417/lock/release`, `/v417/lock/renew`, `/v417/lock/status` - Distributed Locking
- `/v417/batch/create`, `/v417/batch/add`, `/v417/batch/execute`, `/v417/batch/status/<id>` - Request Batching
- `/v417/retry/policy`, `/v417/retry/calculate`, `/v417/retry/record`, `/v417/retry/stats` - Smart Retry
- `/v417/hedge/configure`, `/v417/hedge/execute`, `/v417/hedge/stats` - Request Hedging
- `/v417/circuit/configure`, `/v417/circuit/check`, `/v417/circuit/record`, `/v417/circuit/reset`, `/v417/circuit/list` - Circuit Breaker Pro
- `/v417/degrade/rule`, `/v417/degrade/check`, `/v417/degrade/fallback`, `/v417/degrade/status` - Graceful Degradation
- `/v417/mirror/configure`, `/v417/mirror/capture`, `/v417/mirror/flush`, `/v417/mirror/stats` - Traffic Mirroring
- `/v417/adaptive/configure`, `/v417/adaptive/record`, `/v417/adaptive/adjust`, `/v417/adaptive/current` - Adaptive Rate Limiting
- `/v417/correlate/start`, `/v417/correlate/add`, `/v417/correlate/complete`, `/v417/correlate/trace/<id>`, `/v417/correlate/list` - Request Correlation

**v4.16 Features (ENTERPRISE PLATFORM)**:
- **Request Prioritization Engine**: Smart priority queuing with preemption, auto-upgrade by tier
- **Auto-Scaling Controller**: Dynamic scaling based on CPU, memory, RPS metrics with cooldown
- **API Gateway Pro**: Request/response transformation, aggregation, circuit breaker
- **Service Mesh Integration**: Service discovery, health checks, traffic policies, weighted routing
- **Event Bus**: Pub/sub messaging with topics, subscriptions, retention policies
- **Data Pipeline Manager**: ETL pipelines with stage execution (filter, transform, aggregate, enrich)
- **ML Model Registry**: Model versioning, promotion (dev→staging→prod), deployment, prediction
- **Feature Store**: Centralized feature management for ML with online/offline access
- **Chaos Engineering Pro**: Advanced fault injection experiments (latency, error, cpu, memory, network)

**v4.16 Endpoints**:
- `/v416/priority/enqueue`, `/v416/priority/dequeue`, `/v416/priority/peek`, `/v416/priority/reorder`
- `/v416/autoscale/configure`, `/v416/autoscale/metrics`, `/v416/autoscale/recommend`, `/v416/autoscale/execute`
- `/v416/gateway/route`, `/v416/gateway/transform`, `/v416/gateway/aggregate`, `/v416/gateway/routes`
- `/v416/mesh/register`, `/v416/mesh/discover`, `/v416/mesh/heartbeat`, `/v416/mesh/policy`, `/v416/mesh/route`
- `/v416/events/topic`, `/v416/events/publish`, `/v416/events/subscribe`, `/v416/events/consume`, `/v416/events/topics`
- `/v416/pipeline/create`, `/v416/pipeline/run`, `/v416/pipeline/status/<run_id>`, `/v416/pipeline/list`
- `/v416/models/register`, `/v416/models/promote`, `/v416/models/deploy`, `/v416/models/predict/<id>`, `/v416/models/list`
- `/v416/features/group`, `/v416/features/ingest`, `/v416/features/get`, `/v416/features/batch`, `/v416/features/groups`
- `/v416/chaos/experiment`, `/v416/chaos/start/<id>`, `/v416/chaos/inject`, `/v416/chaos/stop/<id>`, `/v416/chaos/report/<id>`, `/v416/chaos/scenarios`, `/v416/chaos/list`

**v4.15 Features** (still available):
- **Response Cache**: Intelligent caching with TTL, LRU eviction, pattern-based invalidation
- **Metric Aggregator**: Custom metrics with tagging, time-series storage, and aggregation
- **Alert Manager**: Alert rules with thresholds, silencing, notifications, and escalation
- **Incident Tracker**: Incident management with timeline, status tracking, and postmortem templates
- **Change Auditor**: Configuration change tracking with diff, user attribution, and rollback
- **Compliance Scanner**: PCI-DSS, HIPAA, SOC2, GDPR compliance scanning with remediation
- **Cost Analyzer**: API cost tracking, anomaly detection, budgets, and optimization recommendations
- **API Playground**: Interactive API testing with request builder, history, and saved requests

**v4.15 New Endpoints**:
- `/v415/quota/create`, `/v415/quota/check`, `/v415/quota/usage/<api_key>` - Rate Quota Manager
- `/v415/router/configure`, `/v415/router/route`, `/v415/router/health`, `/v415/router/list` - Request Router Pro
- `/v415/cache/get`, `/v415/cache/set`, `/v415/cache/invalidate`, `/v415/cache/stats` - Response Cache
- `/v415/metrics/record`, `/v415/metrics/query`, `/v415/metrics/list` - Metric Aggregator
- `/v415/alerts/rule`, `/v415/alerts/evaluate`, `/v415/alerts/silence`, `/v415/alerts/active`, `/v415/alerts/history` - Alert Manager
- `/v415/incidents/create`, `/v415/incidents/update/<id>`, `/v415/incidents/postmortem/<id>`, `/v415/incidents/list`, `/v415/incidents/get/<id>` - Incident Tracker
- `/v415/audit/log`, `/v415/audit/query`, `/v415/audit/diff/<id>`, `/v415/audit/rollback/<id>` - Change Auditor
- `/v415/compliance/frameworks`, `/v415/compliance/scan`, `/v415/compliance/history` - Compliance Scanner
- `/v415/costs/record`, `/v415/costs/analyze`, `/v415/costs/budget`, `/v415/costs/summary` - Cost Analyzer
- `/v415/playground/execute`, `/v415/playground/save`, `/v415/playground/load/<name>`, `/v415/playground/list`, `/v415/playground/history` - API Playground

**v4.14 Features**:
- **Dedup Pro**: Advanced request deduplication with content hashing, TTL, and fuzzy matching
- **Traffic Mirror**: Traffic mirroring for shadow testing with sampling rates
- **Canary Analysis**: Canary deployment analysis with metrics comparison and recommendations
- **Feature Gate**: Advanced feature flag management with rollout percentages and user targeting
- **Request Validator**: Schema-based request validation with strict/lenient modes
- **Response Transformer**: Response transformation pipeline with field mapping and wrapping
- **Error Classifier**: Intelligent error classification with pattern matching and severity
- **Latency Analyzer**: Latency analysis with percentile tracking (p50, p90, p95, p99)
- **Capacity Planner**: Capacity forecasting with trend analysis and recommendations
- **Service Catalog**: Service registry with dependency graphing and search

**v4.14 New Endpoints**:
- `/v414/dedup/check`, `/v414/dedup/store`, `/v414/dedup/config`, `/v414/dedup/stats` - Dedup Pro
- `/v414/mirror/create`, `/v414/mirror/send`, `/v414/mirror/list`, `/v414/mirror/toggle/<id>` - Traffic Mirror
- `/v414/canary/create`, `/v414/canary/record`, `/v414/canary/analyze/<id>`, `/v414/canary/promote/<id>` - Canary Analysis
- `/v414/gate/create`, `/v414/gate/check`, `/v414/gate/list`, `/v414/gate/update/<id>` - Feature Gate
- `/v414/validator/register`, `/v414/validator/validate`, `/v414/validator/schemas` - Request Validator
- `/v414/transform/create`, `/v414/transform/apply`, `/v414/transform/list` - Response Transformer
- `/v414/errors/pattern`, `/v414/errors/classify`, `/v414/errors/stats` - Error Classifier
- `/v414/latency/record`, `/v414/latency/analyze/<endpoint>`, `/v414/latency/trends` - Latency Analyzer
- `/v414/capacity/register`, `/v414/capacity/record`, `/v414/capacity/forecast/<resource>`, `/v414/capacity/status` - Capacity Planner
- `/v414/catalog/register`, `/v414/catalog/get/<id>`, `/v414/catalog/list`, `/v414/catalog/dependencies/<id>`, `/v414/catalog/search`, `/v414/catalog/update/<id>` - Service Catalog

**v4.13 Features**:
- **Rate Shaping**: Traffic shaping with burst buckets and smooth throttling
- **Priority Queue**: Priority-based request queuing with preemption (CRITICAL→BACKGROUND)
- **Dependency Health Monitor**: Track health of downstream dependencies with status aggregation
- **Trace Collector**: Distributed tracing with span collection (OpenTelemetry-compatible)
- **Config Versioning**: Git-like version control for configuration with branches and rollback
- **Deprecation Manager**: Manage API deprecation lifecycle with sunset tracking
- **Request Sampling**: Intelligent sampling for high-volume endpoints with adaptive rates
- **Tenant Quota Manager**: Per-tenant resource quotas with usage tracking and limits
- **Request Replay Engine**: Replay failed requests with modifications for debugging
- **API Lifecycle Manager**: Full API lifecycle from draft to sunset with phase tracking

**v4.13 New Endpoints**:
- `/v413/shaping/configure`, `/v413/shaping/check`, `/v413/shaping/stats` - Rate Shaping
- `/v413/queue/enqueue`, `/v413/queue/dequeue`, `/v413/queue/status` - Priority Queue
- `/v413/deps/register`, `/v413/deps/check`, `/v413/deps/status`, `/v413/deps/topology` - Dependency Health
- `/v413/trace/start`, `/v413/trace/span`, `/v413/trace/end`, `/v413/trace/get/<id>`, `/v413/trace/list` - Trace Collector
- `/v413/config/get`, `/v413/config/set`, `/v413/config/history`, `/v413/config/rollback`, `/v413/config/branches` - Config Versioning
- `/v413/deprecation/announce`, `/v413/deprecation/track`, `/v413/deprecation/status` - Deprecation Manager
- `/v413/sampling/configure`, `/v413/sampling/sample`, `/v413/sampling/stats` - Request Sampling
- `/v413/quota/create`, `/v413/quota/check`, `/v413/quota/consume`, `/v413/quota/status/<id>` - Tenant Quota
- `/v413/replay/capture`, `/v413/replay/list`, `/v413/replay/execute`, `/v413/replay/stats` - Request Replay
- `/v413/lifecycle/phases`, `/v413/lifecycle/create`, `/v413/lifecycle/promote`, `/v413/lifecycle/list`, `/v413/lifecycle/get/<id>`, `/v413/lifecycle/timeline/<id>` - API Lifecycle

**v4.12 Features**:
- **Circuit Breaker Pro**: Advanced circuit breaker with half-open state, sliding window, per-endpoint config
- **Request Coalescing**: Combine duplicate in-flight requests to reduce load
- **Adaptive Timeout Manager**: Dynamic timeouts based on historical latency percentiles
- **SLO Manager**: Service Level Objectives with error budgets and compliance tracking
- **Request Signing**: HMAC signing for request authenticity and integrity
- **Bulkhead Isolation**: Isolate failures with concurrent request limits per service
- **Retry Policy Engine**: Configurable strategies (exponential, linear, fixed) with jitter
- **Request Compression**: Automatic compression analysis and payload optimization
- **Hot Reload Manager**: Zero-downtime code/config deployments with version history
- **Chaos Scheduler**: Scheduled chaos experiments for resilience testing

**v4.12 New Endpoints**:
- `/v412/circuit/check`, `/v412/circuit/record`, `/v412/circuit/status`, `/v412/circuit/reset/<endpoint>` - Circuit Breaker Pro
- `/v412/coalesce/check`, `/v412/coalesce/complete`, `/v412/coalesce/stats` - Request Coalescing
- `/v412/timeout/get`, `/v412/timeout/record`, `/v412/timeout/reset/<endpoint>` - Adaptive Timeout
- `/v412/slo/list`, `/v412/slo/create`, `/v412/slo/record`, `/v412/slo/status/<id>` - SLO Manager
- `/v412/signing/create-key`, `/v412/signing/sign`, `/v412/signing/verify`, `/v412/signing/revoke/<id>`, `/v412/signing/keys` - Request Signing
- `/v412/bulkhead/configure`, `/v412/bulkhead/acquire`, `/v412/bulkhead/release`, `/v412/bulkhead/stats/<service>` - Bulkhead Isolation
- `/v412/retry/create`, `/v412/retry/get-delay`, `/v412/retry/should-retry`, `/v412/retry/policies` - Retry Policy
- `/v412/compression/analyze`, `/v412/compression/compress`, `/v412/compression/stats` - Request Compression
- `/v412/hotreload/deploy`, `/v412/hotreload/rollback`, `/v412/hotreload/status/<id>`, `/v412/hotreload/list` - Hot Reload
- `/v412/chaos/types`, `/v412/chaos/create`, `/v412/chaos/schedule`, `/v412/chaos/run`, `/v412/chaos/stop`, `/v412/chaos/history/<id>`, `/v412/chaos/list` - Chaos Scheduler

**v4.11 Features**:
- **Distributed Transactions (2PC)**: Two-phase commit with prepare/commit/rollback across services
- **Rate Limiter Pro**: Token bucket algorithm with per-tenant quotas and burst handling
- **Context Propagation**: Request context (trace IDs, user, tenant) across service boundaries
- **Config Templating Engine**: Parameterized configs with inheritance and environment overrides
- **Rollback Manager**: Automated rollback with health gates and traffic shifting
- **Request Mocking**: Mock responses for testing with scenario management
- **Load Shedding**: Graceful degradation under load with priority-based shedding
- **Multi-Cloud Router**: Route requests across AWS, GCP, Azure with cost optimization
- **Webhook Delivery**: Reliable webhook delivery with retries, signatures, and dead letter queue
- **API Docs Generator**: Auto-generate OpenAPI specs from registered endpoints

**v4.11 New Endpoints**:
- `/v411/tx/begin`, `/v411/tx/prepare/<id>`, `/v411/tx/commit/<id>`, `/v411/tx/rollback/<id>`, `/v411/tx/status/<id>` - Distributed TX
- `/v411/ratelimit/check`, `/v411/ratelimit/consume`, `/v411/ratelimit/quota/<tenant>`, `/v411/ratelimit/stats` - Rate Limiter Pro
- `/v411/context/get`, `/v411/context/set`, `/v411/context/propagate`, `/v411/context/clear` - Context Propagation
- `/v411/config/templates`, `/v411/config/render`, `/v411/config/validate`, `/v411/config/environments` - Config Templating
- `/v411/rollback/status`, `/v411/rollback/initiate`, `/v411/rollback/history`, `/v411/rollback/gates` - Rollback Manager
- `/v411/mock/scenarios`, `/v411/mock/enable`, `/v411/mock/disable`, `/v411/mock/match` - Request Mocking
- `/v411/loadshed/status`, `/v411/loadshed/configure`, `/v411/loadshed/stats`, `/v411/loadshed/priorities` - Load Shedding
- `/v411/cloud/providers`, `/v411/cloud/route`, `/v411/cloud/costs`, `/v411/cloud/health` - Multi-Cloud Router
- `/v411/webhooks/register`, `/v411/webhooks/send`, `/v411/webhooks/status/<id>`, `/v411/webhooks/dlq` - Webhook Delivery
- `/v411/docs/generate`, `/v411/docs/openapi`, `/v411/docs/endpoints`, `/v411/docs/schemas` - API Docs Generator

**v4.10 Features**:
- **API Versioning Manager**: Multiple API versions with deprecation, sunset dates, migration paths
- **Request Batching Engine**: Combine requests for efficiency with configurable strategies
- **Service Discovery Registry**: Dynamic service registration, lookup, health-aware routing
- **Tenant Isolation Manager**: Complete data isolation with encryption boundaries
- **Audit Compliance Reporter**: Automated SOC2, GDPR, HIPAA, PCI-DSS reporting
- **Request Deduplication V2**: Advanced idempotency with content hashing, fuzzy matching
- **Graceful Shutdown Manager**: Clean shutdown with request draining, state checkpoints
- **Health Check Aggregator**: Deep health checks across dependencies with weighted scoring
- **Request Prioritization AI**: ML-based priority assignment with learning feedback loop
- **Multi-Protocol Gateway**: Unified HTTP, gRPC, WebSocket, GraphQL gateway

**v4.10 New Endpoints**:
- `/v410/versions`, `/v410/versions/register`, `/v410/versions/deprecate`, `/v410/versions/migration` - Versioning
- `/v410/batch/create`, `/v410/batch/add`, `/v410/batch/execute/<id>`, `/v410/batch/stats` - Batching
- `/v410/discovery/register`, `/v410/discovery/lookup`, `/v410/discovery/heartbeat`, `/v410/discovery/topology` - Discovery
- `/v410/tenant/create`, `/v410/tenant/validate`, `/v410/tenant/boundaries/<id>`, `/v410/tenant/rotate-keys/<id>` - Tenant
- `/v410/compliance/report`, `/v410/compliance/reports`, `/v410/compliance/gaps/<fw>`, `/v410/compliance/evidence/<id>` - Compliance
- `/v410/dedup/check`, `/v410/dedup/register`, `/v410/dedup/stats` - Deduplication
- `/v410/shutdown/status`, `/v410/shutdown/initiate`, `/v410/shutdown/checkpoint`, `/v410/shutdown/restore` - Shutdown
- `/v410/health/checks`, `/v410/health/run/<id>`, `/v410/health/aggregate` - Health
- `/v410/priority/predict`, `/v410/priority/feedback`, `/v410/priority/model` - Priority AI
- `/v410/gateway/protocols`, `/v410/gateway/translate`, `/v410/gateway/connections`, `/v410/gateway/broadcast` - Gateway

**v4.9 Features**:
- **Workflow Orchestration Engine**: Complex DAG execution with parallel branches and joins
- **API Gateway Manager**: Request transformation, routing, schema validation
- **Event Bus / Message Queue**: Pub/sub messaging with topics, subscriptions, replay
- **Secrets Vault Integration**: Secure secrets management with rotation and policies
- **Observability Dashboard**: Unified metrics, logs, traces with alerting
- **Contract Testing**: API contract validation between services (consumer-driven)
- **Feature Toggle Manager**: Advanced flags with segments, cohorts, scheduling
- **Data Masking Engine**: PII detection, tokenization, and automatic masking
- **Workflow Scheduler**: Cron-like scheduling with timezone support and dependencies
- **Resource Quotas**: Per-tenant limits with usage tracking and alerts

**v4.9 New Endpoints**:
- `/v49/workflow/create`, `/v49/workflow/execute`, `/v49/workflow/status/<id>`, `/v49/workflow/fork` - Orchestration
- `/v49/gateway/routes`, `/v49/gateway/transform`, `/v49/gateway/validate` - API Gateway
- `/v49/events/topics`, `/v49/events/subscribe`, `/v49/events/publish`, `/v49/events/replay` - Event Bus
- `/v49/vault/secrets`, `/v49/vault/secrets/<path>`, `/v49/vault/rotate`, `/v49/vault/policies` - Secrets
- `/v49/observe/metrics`, `/v49/observe/logs`, `/v49/observe/dashboards`, `/v49/observe/alerts` - Observability
- `/v49/contracts`, `/v49/contracts/verify/<id>`, `/v49/contracts/can-deploy` - Contract Testing
- `/v49/toggles`, `/v49/toggles/evaluate`, `/v49/toggles/segments`, `/v49/toggles/schedule` - Feature Toggles
- `/v49/masking/detect`, `/v49/masking/mask`, `/v49/masking/rules`, `/v49/masking/tokenize` - Data Masking
- `/v49/scheduler/schedules`, `/v49/scheduler/pause/<id>`, `/v49/scheduler/resume/<id>`, `/v49/scheduler/trigger/<id>` - Scheduler
- `/v49/quotas`, `/v49/quotas/usage/<tenant>`, `/v49/quotas/check`, `/v49/quotas/reserve`, `/v49/quotas/alerts` - Quotas

**v4.8 Features**:
- **Real-Time Collaboration**: Multi-user workspace with live state sync
- **Plugin Marketplace**: Dynamic plugin installation/uninstallation with config
- **Natural Language Query Engine**: NL→API translation with query suggestions
- **Distributed Locking**: Resource locking with TTL and ownership tracking
- **Schema Evolution Manager**: Version-tracked schema migrations with validation
- **Request Replay Debugger**: Capture, replay, and compare request executions
- **Intelligent Request Router**: ML-based routing to optimal compute pools
- **Dependency Injection Container**: Service registration, resolution, and graphs
- **Configuration Drift Detector**: Snapshot-based config drift detection and remediation
- **Self-Healing Network**: Topology visualization, predictive healing, node isolation

**v4.8 New Endpoints**:
- `/v48/collab/create`, `/v48/collab/join`, `/v48/collab/sync`, `/v48/collab/list` - Collaboration
- `/v48/plugins/list`, `/v48/plugins/install`, `/v48/plugins/uninstall`, `/v48/plugins/config/<name>` - Plugins
- `/v48/nlq/query`, `/v48/nlq/suggest`, `/v48/nlq/history` - Natural language queries
- `/v48/lock/acquire`, `/v48/lock/release`, `/v48/lock/status` - Distributed locking
- `/v48/schema/current`, `/v48/schema/migrate`, `/v48/schema/validate`, `/v48/schema/diff` - Schema evolution
- `/v48/replay/capture`, `/v48/replay/list`, `/v48/replay/execute`, `/v48/replay/compare` - Replay debugger
- `/v48/router/route`, `/v48/router/rules`, `/v48/router/analyze` - Intelligent routing
- `/v48/di/register`, `/v48/di/resolve`, `/v48/di/list`, `/v48/di/graph` - Dependency injection
- `/v48/drift/snapshot`, `/v48/drift/detect`, `/v48/drift/history`, `/v48/drift/remediate` - Drift detection
- `/v48/network/topology`, `/v48/network/heal`, `/v48/network/predict`, `/v48/network/isolate` - Self-healing

**v4.7 Features**:
- **GraphQL Gateway**: Flexible query interface for agents, tasks, workflows
- **Service Mesh Integration**: mTLS, service discovery, sidecar proxies
- **Data Pipeline Orchestration**: ETL/ELT workflow management with lineage
- **Multi-Region Failover**: Active-active with automatic failover
- **Adaptive Rate Limiting**: Dynamic limits based on system health
- **Workflow Templates Library**: Reusable patterns (code_review, research, incident)
- **Cost Allocation & Chargeback**: Per-tenant cost tracking and invoicing
- **Automated Runbooks**: Self-executing incident response procedures
- **AI-Powered Optimization**: ML-based performance recommendations
- **Request Priority Queue**: Priority scheduling with preemption (CRITICAL→LOW)

**v4.7 New Endpoints**:
- `/graphql`, `/graphql/schema` - GraphQL gateway
- `/mesh/services`, `/mesh/discover`, `/mesh/health` - Service mesh
- `/v47/pipeline/list`, `/v47/pipeline/run`, `/v47/pipeline/lineage` - Data pipelines
- `/region/status`, `/region/select`, `/region/failover` - Multi-region
- `/ratelimit/check`, `/ratelimit/status` - Adaptive rate limits
- `/templates/list`, `/templates/get/<id>`, `/templates/instantiate` - Templates
- `/costs/calculate`, `/costs/tenant/<id>`, `/costs/invoice` - Cost allocation
- `/runbook/list`, `/runbook/execute`, `/runbook/status/<id>` - Runbooks
- `/ai/recommend`, `/ai/predict`, `/ai/optimize` - AI optimization
- `/queue/enqueue`, `/queue/dequeue`, `/queue/status` - Priority queue

**v4.6 Features**:
- **Auto-Remediation Engine**: Automatic error diagnosis and fix attempts
- **Predictive Scaling**: ML-based load prediction and proactive scaling
- **Dynamic Configuration**: Hot-reload config without service restart
- **Alert Routing & Escalation**: Smart alert routing with escalation policies
- **Capacity Planning**: Usage trend analysis and future capacity projection
- **Idempotency Handler**: Safe request retries without side effects
- **Request Shadowing**: Shadow traffic to staging for testing
- **Traffic Mirroring**: Copy traffic to analytics/security systems
- **Load Balancer**: Weighted round-robin with health checks
- **Response Streaming**: Real-time chunked response delivery

**v4.6 New Endpoints**:
- `/remediation/diagnose`, `/remediation/execute`, `/remediation/history` - Auto-fix
- `/scaling/predict`, `/scaling/plan`, `/scaling/history` - Predictive scaling
- `/config/get`, `/config/set`, `/config/history` - Dynamic config
- `/alerts/route`, `/alerts/queue`, `/alerts/escalate` - Alert routing
- `/capacity/current`, `/capacity/project`, `/capacity/recommendations` - Capacity
- `/idempotency/check`, `/idempotency/store`, `/idempotency/stats` - Idempotency
- `/shadow/queue`, `/shadow/status`, `/shadow/results` - Request shadowing
- `/mirror/configure`, `/mirror/queue`, `/mirror/add` - Traffic mirroring
- `/lb/backends`, `/lb/select`, `/lb/health` - Load balancer
- `/stream/create`, `/stream/<id>/send`, `/stream/<id>/close`, `/stream/active` - Streaming

**v4.5 Features**:
- **Event Sourcing**: Immutable event log for complete audit trail and replay
- **Saga Orchestration**: Distributed transaction management with compensation
- **Policy Engine**: Declarative rules (access, rate, content, time-based)
- **Compliance Auditor**: GDPR, SOC2, HIPAA compliance checks
- **Cost Optimizer**: API cost analysis with optimization recommendations
- **Anomaly Detection**: Statistical outlier detection (z-score based)
- **Geographic Routing**: Region-based request routing with failover
- **Dependency Tracker**: Tool and service dependency graph
- **Blue-Green Deployments**: Zero-downtime deployment switching
- **Semantic Caching**: Meaning-based cache matching (not just exact keys)

**v4.5 New Endpoints**:
- `/events/append`, `/events/stream/<id>`, `/events/replay/<id>` - Event sourcing
- `/saga/start`, `/saga/<id>/status`, `/saga/<id>/step`, `/saga/<id>/compensate` - Sagas
- `/policy/evaluate`, `/policy/list` - Policy engine
- `/compliance/audit`, `/compliance/history` - Compliance
- `/cost/analyze`, `/cost/summary` - Cost optimization
- `/anomaly/detect`, `/anomaly/history` - Anomaly detection
- `/geo/route`, `/geo/regions` - Geographic routing
- `/dependencies/check`, `/dependencies/services` - Dependency tracking
- `/deployment/status`, `/deployment/switch`, `/deployment/rollback` - Blue-green
- `/semantic-cache/search`, `/semantic-cache/store` - Semantic caching

**v4.4 Features**:
- **WebSocket Manager**: Real-time status updates pushed to clients
- **Intelligent Caching**: TTL-based cache with operation-type policies
- **Request Throttling**: Backpressure with tier-based rate limits
- **Multi-Tenancy**: Isolated workspaces with path/tool restrictions
- **Request Replay**: Automatic retry of failed requests from audit log
- **Canary Deployments**: Traffic splitting for safe rollouts
- **SLA Monitoring**: Response time, availability, error rate tracking
- **Secret Management**: Credential health and rotation scheduling
- **Request Correlation**: Link related requests across sub-agents
- **Chaos Engineering**: Fault injection for resilience testing

**v4.4 New Endpoints**:
- `/tenant/list`, `/tenant/get/<id>`, `/tenant/create` - Multi-tenancy
- `/canary/list`, `/canary/metrics/<id>`, `/canary/record` - Canary deployments
- `/sla/definitions`, `/sla/violations`, `/sla/record` - SLA monitoring
- `/ws/register`, `/ws/unregister`, `/ws/broadcast`, `/ws/connections` - WebSocket
- `/replay/queue`, `/replay/add`, `/replay/process` - Request replay
- `/secrets/health`, `/secrets/rotate` - Secret management
- `/correlation/log`, `/correlation/trace/<id>` - Request correlation
- `/chaos/status`, `/chaos/inject` - Chaos engineering

**v4.3 Features**:
- **JWT Authentication**: API key and JWT token support with role-based access
- **RBAC Permissions**: Role-based access control (admin/developer/user/readonly)
- **Feature Flags**: Gradual rollout with user bucketing (0-100%)
- **Budget Enforcement**: Cost limits ($) and rate limits (req/min) per user role
- **Prometheus Metrics**: `/prometheus` endpoint for monitoring
- **Distributed Tracing**: OpenTelemetry-style request tracing
- **A/B Testing**: Experiment variants with deterministic user assignment
- **Workflow Versioning**: Version history with rollback support
- **Health Dashboard**: Aggregated system health status
- **Request Enrichment**: Client info, geo, intent detection

**v4.3 New Endpoints**:
- `/prometheus` - Prometheus metrics format
- `/prometheus/record` - Record metrics entry
- `/features/list`, `/features/set`, `/features/reset` - Feature flags
- `/ab/experiments`, `/ab/record`, `/ab/results/<exp>` - A/B testing
- `/versioning/current`, `/versioning/history`, `/versioning/rollback` - Versioning
- `/health/dashboard`, `/health/check` - Health monitoring
- `/trace/start`, `/trace/end/<id>`, `/trace/event`, `/trace/<id>` - Tracing

**v4.2 Resilience Features**:
- **Circuit Breaker**: Prevents cascade failures (threshold=5, timeout=30s)
- **Dead Letter Queue**: Stores failed tasks for retry
- **Priority Queue**: Task ordering by urgency (1=critical, 5=low)
- **Batch Processing**: Parallel task execution
- **Request Deduplication**: MD5 fingerprinting to prevent duplicates
- **Request Validation**: Schema validation before processing
- **Graceful Degradation**: Fallback modes when systems fail

**v4.1.1 Error Handling & Auto-Healing**:
- **Error Analysis**: `/error/analyze` - Analyzes errors, finds known patterns, suggests fixes
- **Auto-Fix**: `/error/auto-fix` - Attempts automatic fixes (retry, backoff, credential refresh)
- **Error Notifications**: `/notify/error` - Routes to SMS/email/Slack based on severity
- **Critical Alerts**: `/notify/critical` - Sends urgent SMS for critical errors
- **Error Stats**: `/error/stats` - View error statistics and common patterns
- **Auto-Fix Patterns**: ECONNREFUSED, ETIMEDOUT, rate limit, authentication errors
- **n8n Integration**: Set "Error Workflow" in workflow settings to `Self-Annealing-Error-Handler`

**To Configure Error Handling in n8n UI**:
1. Open workflow settings (gear icon → Settings)
2. Set "Error Workflow" to `Self-Annealing-Error-Handler`
3. Save and activate the workflow

**v4.1 Integrations**:
- **Gmail**: `gmail_list`, `gmail_read`, `gmail_send`, `gmail_search`
- **Google Sheets**: `sheets_read`, `sheets_write`, `sheets_append`
- **Twilio SMS**: `sms_send`, `sms_list`
- **ClickUp CRM**: `clickup_list_tasks`, `clickup_create_task`, `clickup_update_task`
- **n8n Workflows**: `n8n_list_workflows`, `n8n_get_workflow`, `n8n_create_workflow`, `n8n_update_workflow`, `n8n_activate_workflow`, `n8n_execute_workflow`
- **Enhanced Git**: `git_clone`, `git_pull`, `git_branch`, `git_log`
- **Enhanced Terminal**: `terminal_multi_command`, `terminal_script`

**v4.1 Meta-Agent (Self-Annealing)**:
- `meta_capabilities`: List all available tools
- `meta_discover`: Find new integrations and MCP tools
- `meta_create_tool`: Generate new tool code dynamically
- `meta_learn_error`: Store error patterns with solutions
- `meta_find_solution`: Retrieve stored error solutions
- `meta_introspect`: Analyze agent behavior and patterns
- `meta_suggest`: Get improvement suggestions
- `agent_build_workflow`: Self-replicate new agent workflows

**v4.1 Meta-Agent Endpoints**:
- `/meta/capabilities` - List all tools
- `/meta/discover` - Discover new integrations
- `/meta/create-tool` - Generate new tool code
- `/meta/learn-error` - Store error solution
- `/meta/find-solution` - Find stored solution
- `/meta/introspect` - Analyze behavior
- `/meta/suggest` - Get suggestions
- `/meta/questions` - List questions for future
- `/meta/patterns` - Get learned patterns
- `/agent/build-workflow` - Self-replicate workflows

**v4.1 Integration Endpoints**:
- `/gmail/list`, `/gmail/read`, `/gmail/send`, `/gmail/search`
- `/sheets/read`, `/sheets/write`, `/sheets/append`
- `/sms/send`, `/sms/list`
- `/clickup/list-tasks`, `/clickup/create-task`, `/clickup/update-task`
- `/n8n/list-workflows`, `/n8n/get-workflow`, `/n8n/create-workflow`, `/n8n/update-workflow`, `/n8n/activate-workflow`, `/n8n/execute-workflow`
- `/git/clone`, `/git/pull`, `/git/branch`, `/git/log`
- `/terminal/multi-command`, `/terminal/script`

**v4.1 Config Options**:
```json
{
  "task": "string or object",
  "persona": "senior_engineer|rapid_prototyper|research_analyst|devops_specialist",
  "template": "coder|researcher|analyst|writer|devops|orchestrator",
  "config": {
    "meta_agent": { "self_discovery": true, "error_learning": true, "auto_suggest": false }
  }
}
```

---

### n8n Agent Orchestrator v4.0 (2026-02-07)
- **Universal Agent Orchestrator** deployed to EC2 n8n (ID: `1s52PkA1lY1lHfGP`)
- Supports Claude (Anthropic) with correct model: `claude-sonnet-4-5-20250929`
- Python Bridge API at `execution/agent_bridge_api.py` runs on EC2 localhost:5010
- Agent loop: Webhook → Parse → API Call → Parse Response → HITL Check → Tool Router → Tool → Loop/Complete
- **37 nodes** (including Checkpoint, Async Background, Return Response)

**v4.0 Improvements** (2026-02-07):
- **Agent Personas**: Rich personality definitions with traits, expertise, communication style
  - Built-in: `senior_engineer`, `rapid_prototyper`, `research_analyst`, `devops_specialist`
  - Usage: `{"persona": "senior_engineer", "task": "..."}`
  - Endpoints: `/personas/list`, `/personas/get`, `/personas/create`, `/personas/update`, `/personas/delete`
- **Goal Decomposition**: Break complex tasks into sub-goals with dependencies
  - Auto-decompose tasks into sequential/parallel/adaptive sub-goals
  - Endpoints: `/goals/create`, `/goals/list`, `/goals/get`, `/goals/decompose`, `/goals/update-subgoal`, `/goals/delete`
- **Tool Macros**: Reusable multi-tool sequences that execute as single commands
  - Built-in: `backup_and_edit`, `git_safe_commit`, `find_replace_all`, `analyze_codebase`
  - Endpoints: `/macros/list`, `/macros/get`, `/macros/create`, `/macros/execute`, `/macros/delete`
- **Audit Trail**: Complete action logging for debugging and compliance
  - Track all actions with timestamps, risk levels, and context
  - Endpoints: `/audit/log`, `/audit/list`, `/audit/get`, `/audit/query`, `/audit/clear`
- **Adaptive Behavior**: Auto-adjust agent behavior based on learning patterns
  - Track tool preferences, error patterns, and adjust strategies
  - Endpoints: `/adaptive/profile`, `/adaptive/update`, `/adaptive/reset`, `/adaptive/recommend`

**v4.0 Config Options** (extends v3.9):
```json
{
  "persona": "senior_engineer",
  "config": {
    "persona": { "id": "senior_engineer", "custom_traits": [] },
    "goals": { "enabled": true, "auto_decompose": false, "strategy": "sequential" },
    "macros": { "enabled": true, "allowed_macros": [] },
    "audit": { "enabled": true, "log_inputs": true, "log_outputs": true },
    "adaptive": { "enabled": true, "learning_rate": 0.1, "apply_adaptations": true }
  }
}
```

**v3.9 Improvements** (2026-02-07):
- **Agent Learning & Feedback**: Learn from task outcomes via `/learning/*` endpoints
  - Record outcomes: `/learning/record`, add feedback: `/learning/feedback`
  - Get recommendations: `/learning/recommendations`, list patterns: `/learning/patterns`
- **Workflow Recording & Playback**: Record and replay agent action sequences
  - Start/stop: `/recording/start`, `/recording/stop`, `/recording/step`
  - Playback: `/recording/playback`, list: `/recording/list`
- **Smart Context Injection**: Auto-inject relevant KB content into prompts
  - Create rules: `/context/rules/create`, toggle: `/context/rules/toggle`
  - Get context: `/context/inject`
- **Inter-Agent Communication**: Sub-agents share data and send messages
  - Send/receive: `/agents/message/send`, `/agents/message/receive`
  - Shared state: `/agents/state/get`, `/agents/state/update`, `/agents/state/lock`

**v3.8 Improvements** (2026-02-07):
- **Multi-Agent Orchestration**: Spawn sub-agents for parallel subtask execution via `/orchestration/*`
- **Knowledge Base / RAG**: Index project files for semantic search via `/kb/*` endpoints
- **Scheduled Tasks**: Cron-like scheduling for recurring agent tasks via `/scheduler/*`
- **Tool Plugins**: Dynamically load tools from Python, HTTP, or MCP via `/plugins/*`
- **New Template**: `orchestrator` - breaks down complex tasks and delegates to sub-agents

**v3.7 Improvements** (2026-02-07):
- **Conversation Memory**: Persist chat history across sessions via `/memory/*` endpoints
- **Tool Pipelines**: Chain tool outputs together (built-ins: `find_and_read`, `search_and_extract`, `backup_file`)
- **Webhook Notifications**: Get alerts when tasks complete via `/webhook/*` endpoints
- **Agent Templates**: Pre-configured profiles: `coder`, `researcher`, `analyst`, `writer`, `devops`

**v3.5 Improvements** (2026-02-07):
- **True Async Background**: `background: true` returns immediately, polls `/task/status`
- **Structured Errors**: ErrorCode enum, context, suggestions in API responses
- **Execution Metrics**: Track tool calls, latency, success/error rates via `/metrics`
- **Session Resume**: Save/load checkpoints via `checkpoint` tool
- **Task Persistence**: Tasks/sessions/checkpoints saved to disk (survives restarts)
- **Retry Logic**: `retry_with_backoff()` decorator + `/retry/execute` endpoint
- **Context Management**: Token estimation, auto-truncate long conversations via `/context/truncate`
- **Streaming Responses**: SSE endpoints (`/stream/start`, `/stream/push`, `/stream/events/{id}`)

**v3.6 Improvements** (2026-02-07):
- **Parallel Tool Execution**: Run independent tools simultaneously via ThreadPoolExecutor
- **Tool Result Caching**: LRU cache with TTL for file reads and search results
- **Smart Rate Limiting**: Token bucket algorithm to throttle API calls intelligently
- **Cost & Token Tracking**: Track API costs per session with budget limits

**v3.3 Tools (11 total)**:
- `file_read`: Read file contents
- `file_write`: Create/overwrite files (HITL configurable)
- `file_edit`: Line-based file editing (HITL configurable)
- `command`: Execute bash commands (HITL configurable)
- `git_status`: Get repository status
- `web_fetch`: Fetch and parse web content
- `grep`: Search file contents with regex
- `glob`: Find files by pattern with sorting
- `web_search`: DuckDuckGo search (no API key)
- `todo`: Session-based task tracking (add/update/list/delete/clear)
- `checkpoint`: Save session state for later resume (NEW)

**Session Checkpoints**:
- Save: Agent uses `{"action": "checkpoint", "input": {"name": "checkpoint-name"}}`
- Stored in-memory on Python Bridge (session_id → checkpoint_name → state)
- API endpoints: `/session/save`, `/session/load`, `/session/list`, `/session/delete`
- Resume functionality: Planned but not yet implemented

**True Async Background Tasks**:
- Enable: `{"task": "...", "background": true}` → returns immediately (~4s)
- Response: `{status: "accepted", task_id: "...", poll_url: "/task/status"}`
- Self-invoking webhook pattern: Trigger Background fires request with `_background_execution: true`
- Flow: Parse Request → Background? → Create BG Task → Trigger Background → Background Response
- Background execution: Runs separately, updates task via `/task/update` on completion
- API endpoints: `/task/create`, `/task/update`, `/task/status`, `/task/result`, `/task/list` (all POST)
- Results persisted in-memory on Python Bridge
- `onError: "continueRegularOutput"` on Update BG Task prevents failures from crashing workflow

**Plan Mode**:
- Enable with `config.plan_mode: true`
- Agent returns `{"action": "plan", "input": {"title": "...", "steps": [...]}}`
- Approve via `POST /webhook-waiting/agent-approval/{approval_id}`
- **Known bug**: n8n SQLite error on webhook resume (restart n8n if needed)

**Human-in-the-Loop (HITL) v3**:
- Webhook-based approval flow using n8n Wait node
- Dangerous pattern auto-detection: rm, kill, git push, etc.
- Approval webhook: `POST /webhook-waiting/agent-approval/{approval_id}`
- Configurable per-request: `config.require_approval_for: ["command", "file_write"]`
- Default timeout: 300 seconds

**Multi-Provider Support**:
- Anthropic (Claude) - Fully working
- Grok/xAI - Requires n8n credential configuration (API key format differs)

**Structured Error Handling**:
- ErrorCode enum in `agent_bridge_api.py` for categorized errors
- `make_error_response()` returns: `{success: false, error: {code, message, suggestion, context}}`
- Handle Result node updated to extract error.message from structured format
- Backwards compatible: also includes flat `error_message` field

### n8n Critical Learnings (2026-02-07)
- **responseMode**: Use `lastNode` (not `responseNode`) - simpler, more reliable
- **Do NOT** use respondToWebhook node with lastNode mode - causes "Unused" error
- **If node outputs**: Output 0 = true branch, Output 1 = false branch
- **Credential format**: httpHeaderAuth needs `name: "x-api-key"` for Anthropic
- **Model ID**: Use `claude-sonnet-4-5-20250929` (not old 3.5 sonnet format)
- **Partial updates**: Use `mcp__n8n__partial_update_workflow` for single node changes
- **System prompt**: Explicitly require JSON format for tool calls to avoid XML

### n8n Best Practices
- Always use EC2 instance (http://34.193.98.97:5678), never local
- Use `mcp__n8n__create_workflow_from_file` for deploying workflows
- Use `mcp__n8n__export_workflow_to_file` for backups
- Code nodes use JavaScript, not Python
- Switch nodes route by action type
- Keep workflows simple - complex conditionals can break lastNode routing

### Agent Workflow Architecture (v3.3)
- Webhook → Parse Request → Debug Check → API Call → Parse Response → **HITL Check** → Tool Router
- **HITL branch**: Format Approval → Wait for Approval (webhook) → Process Approval → Approved? → Tool Router or Loop
- Tool Router outputs: file_read, file_write, file_edit, command, git_status, web_fetch, grep, glob, web_search, todo, **checkpoint**, complete/error
- Python Bridge on EC2 localhost:5010 handles file/command/search/session operations
- Max iterations prevent runaway loops (default: 10)
- JSON format for tool calls: `{"action": "tool_name", "input": {...}}`
- Dangerous commands auto-flagged for approval (configurable)
- Task string accepted: `{"task": "string description"}` now works in addition to object format

### Credentials on EC2 n8n
- Anthropic API Key: `YcmiPKM8dtApO3q3` (httpHeaderAuth, x-api-key header)
- Google Sheets: `RIFdaHtNYdTpFnlu` (OAuth2)

**v3.8 New Endpoints (Python Bridge API v3.8.0)**:
- `/orchestration/create` POST - Create multi-agent orchestration
- `/orchestration/list` GET/POST - List orchestrations
- `/orchestration/status` POST - Get orchestration status with sub-agents
- `/orchestration/update-agent` POST - Update sub-agent status/result
- `/kb/create` POST - Create knowledge base
- `/kb/list` GET/POST - List knowledge bases
- `/kb/index` POST - Index files into knowledge base
- `/kb/search` POST - Search knowledge base (keyword matching)
- `/kb/delete` POST - Delete knowledge base
- `/scheduler/create` POST - Create scheduled task
- `/scheduler/list` GET/POST - List scheduled tasks
- `/scheduler/toggle` POST - Enable/disable scheduled task
- `/scheduler/delete` POST - Delete scheduled task
- `/scheduler/run-now` POST - Manually trigger scheduled task
- `/plugins/list` GET/POST - List registered plugins
- `/plugins/register-python` POST - Register Python function as plugin
- `/plugins/register-http` POST - Register HTTP endpoint as plugin
- `/plugins/register-mcp` POST - Register MCP server tool as plugin
- `/plugins/execute` POST - Execute a plugin
- `/plugins/toggle` POST - Enable/disable plugin
- `/plugins/delete` POST - Delete plugin

**v3.7 New Endpoints**:
- `/memory/add` POST - Add message to conversation memory
- `/memory/get` POST - Get conversation memory for session
- `/memory/list` GET/POST - List all conversation memories
- `/memory/clear` POST - Clear conversation memory
- `/memory/summarize` POST - Summarize conversation to reduce size
- `/pipeline/list` GET/POST - List available pipelines (built-in + custom)
- `/pipeline/create` POST - Create custom pipeline
- `/pipeline/execute` POST - Execute a pipeline
- `/webhook/register` POST - Register webhook for notifications
- `/webhook/list` GET/POST - List registered webhooks
- `/webhook/delete` POST - Delete a webhook
- `/webhook/test` POST - Test webhook connectivity
- `/webhook/notify` POST - Trigger webhook notification
- `/templates/list` GET/POST - List agent templates
- `/templates/get` POST - Get template details
- `/templates/apply` POST - Apply template to session

**v3.6 New Endpoints**:
- `/tools/parallel` POST - Execute multiple tools in parallel (ThreadPoolExecutor)
- `/cache/stats` GET/POST - Get cache statistics (hits, misses, size)
- `/cache/clear` POST - Clear cache or specific pattern
- `/cache/get` POST - Get cached value by key
- `/cache/set` POST - Set cache value with optional TTL
- `/ratelimit/stats` GET/POST - Get rate limiter statistics
- `/ratelimit/acquire` POST - Acquire tokens (wait for available if needed)
- `/cost/track` POST - Track API call cost for a session
- `/cost/session` POST - Get cost summary for a session
- `/cost/all` GET/POST - Get costs for all sessions
- `/cost/set_budget` POST - Set budget limit for a session
- `/cost/pricing` GET/POST - Get or update Anthropic pricing model

**v3.5 Endpoints**:
- `/context/truncate` POST - Truncate conversation history to fit token limits
- `/context/estimate` POST - Estimate token count for messages
- `/stream/start` POST - Start SSE streaming session
- `/stream/push` POST - Push event to stream
- `/stream/events/{id}` GET - SSE endpoint for real-time events
- `/stream/close` POST - Close streaming session
- `/retry/execute` POST - Execute operation with auto-retry + backoff
- `/state/export` GET/POST - Export full state for backup
- `/state/import` POST - Import state (requires confirm: true)
- `/state/persist` POST - Force save state to disk

**v3.6 Config Options**:
```json
{
  "config": {
    "retry": { "enabled": true, "max_retries": 3, "base_delay": 1.0 },
    "context": { "auto_truncate": true, "max_tokens": 120000, "preserve_first": 1, "preserve_last": 5 },
    "streaming": { "enabled": false },
    "parallel": { "enabled": true, "max_workers": 4, "timeout": 30 },
    "cache": { "enabled": true, "ttl": 300, "max_size": 100 },
    "ratelimit": { "enabled": true, "rate": 10.0, "capacity": 20 },
    "cost": { "enabled": true, "budget_limit": null, "track_tokens": true }
  }
}
```

**Persistence Location**:
- Default: `/tmp/agent_bridge_data/state.json`
- Override with: `AGENT_BRIDGE_DATA_DIR` env var
- Auto-saves every 30 seconds when dirty
- Loads on startup, saves on shutdown

**v3.7 Config Options** (extends v3.6):
```json
{
  "config": {
    "memory": { "enabled": true, "max_messages": 100 },
    "webhook": { "url": "https://...", "events": ["task_complete", "task_error"] }
  }
}
```

**Agent Templates Usage**:
```json
{"template": "coder", "task": "..."}  // Uses coder profile
{"template": "researcher", "task": "..."}  // Uses researcher profile
{"template": "orchestrator", "task": "..."}  // Spawns sub-agents (v3.8)
```

**v3.8 Config Options** (extends v3.7):
```json
{
  "config": {
    "orchestration": { "enabled": true, "max_sub_agents": 5, "strategy": "parallel" },
    "knowledge_base": { "kb_id": null, "auto_context": true }
  }
}
```

### File Locations
- n8n workflows: `projects/shared/n8n-workflows/`
- v4.0 workflow: `projects/shared/n8n-workflows/agent-orchestrator-v40.json`
- v3.9 workflow: `projects/shared/n8n-workflows/agent-orchestrator-v39.json`
- v3.8 workflow: `projects/shared/n8n-workflows/agent-orchestrator-v38.json`
- Python Bridge API: `execution/agent_bridge_api.py` (v4.0.0)
- Agent docs: `docs/AGENT-ORCHESTRATOR-GUIDE.md`
