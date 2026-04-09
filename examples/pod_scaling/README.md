## HPA Scaling SLO

- Latency: Request latency (p90/p95/p99) must stay below the defined threshold
- Time HPA takes to react (trigger → desired replicas updated)
- Time for new pods to become Ready
- Error rate: Percentage of failed requests must remain below the allowed limit
- Availability gap (optional): Duration where available replicas are below desired must be minimal
