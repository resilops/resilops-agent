## Distribution

This repository is proprietary software owned by ResilOps.

Recommended customer delivery model:

1. Build and publish the agent container image to a private container registry.
2. Package the Helm chart with `helm package`.
3. Publish the chart to a private OCI registry with `helm push`.
4. Grant each customer read access only to the specific image and chart
   repositories they need.
5. Provide customer usage rights through a separate commercial agreement or
   EULA.

Example Helm workflow:

```bash
helm package ./helm/agent
helm registry login REGISTRY_HOST
helm push agent-<version>.tgz oci://REGISTRY_HOST/helm-charts
```

Example customer install:

```bash
helm install agent \
  oci://REGISTRY_HOST/helm-charts/agent \
  --version <version>
```

Supported private OCI registry options include Amazon ECR, Azure Container
Registry, Google Artifact Registry, Harbor, and JFrog Artifactory.
