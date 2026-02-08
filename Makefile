.PHONY: init help

## Show help for all commands
help:
	@echo "Available commands:"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z0-9._-]+:.*?## / {printf "  \033[36m%-25s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

lib: ## Install resilience-lib
	@rsync -av --exclude='pyenv' ../resilience-lib/ ./local-libs/resilience-lib

chart: ## Build local kubernetes charts
	helm secrets template resilience-agent ../helm-charts/app -f ./helm/agent/common.yaml -f ./helm/agent/local/values.yaml -f ./helm/agent/local/secrets.enc.yaml
	helm secrets template control-plane ../helm-charts/app -f ./helm/controlplane/local/values.yaml

build: lib ## Build local docker containers
	@eval $(minikube docker-env)
	@echo "🐳 Building Docker containers"
	docker build -f ./docker/AgentDockerfile --target local -t resilience-agent:local .
	docker build -f ./docker/MockserverDockerfile -t resilience-agent-cp:local .

up: ## Deploy local charts
	@echo "🚀 Deploying Resilience Agent Control Plane Locally"
	helm secrets upgrade --install controlplane ../helm-charts/app \
		-n resiltyio \
		-f ./helm/controlplane/local/values.yaml \
		--create-namespace --force

	@echo "🚀 Deploying Resilience Agent Locally"
	helm secrets upgrade --install agent ../helm-charts/app \
		-n resiltyio \
		-f ./helm/agent/common.yaml \
		-f ./helm/agent/local/secrets.enc.yaml \
		-f ./helm/agent/local/values.yaml --force

down: ## Remove all the deployments
	helm uninstall -n resiltyio agent controlplane

forward: ## Port forward control plane to localhost
	kubectl port-forward svc/controlplane 8000:8000

logs: ## Log stream of agent
	kubectl logs -f $$(kubectl get pod -n resiltyio -l app.kubernetes.io/name=agent -o jsonpath='{.items[0].metadata.name}')


nginx-up: ## Deploy nginx with hpa
	@echo "🐳 Building stress container"
	docker build -f ./docker/NginxDockerfile -t resiltyio-nginx:local .
	kubectl apply -f ./examples/nginx-hpa.yaml -n nginx

nginx-down: ## Delete nginx deployment
	kubectl delete -f ./examples/nginx-hpa.yaml
