## HPA Scaling Measurement (Simple)

- Latency (p50 / p95 / p99) before, during, after scaling
- Time HPA takes to react (trigger → desired replicas updated)
- Time for new pods to be created
- Time for new pods to become Ready
- Duration where available replicas < desired replicas
- Error budget exceeded (yes / no)
