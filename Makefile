.PHONY: init help

## Show help for all commands
help:
	@echo "Available commands:"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z0-9._-]+:.*?## / {printf "  \033[36m%-25s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

lib: ## Install resilience-lib
	@rsync -av --exclude='pyenv' ../resilience-lib/ ./local-libs/resilience-lib

chart: ## Build local kubernetes charts
	helm secrets template resilience-agent ../helm-charts/app -f ./charts/local/agent/values.yaml -f ./charts/local/secrets.enc.yaml
	helm secrets template control-plane ../helm-charts/app -f ./charts/local/control-plane/values.yaml

build: lib ## Build local docker containers
	@eval $(minikube docker-env)
	@echo "🐳 Building Docker containers"
	docker build -f ./docker/AgentDockerfile --target local -t resilience-agent:local .
	docker build -f ./docker/MockserverDockerfile -t resilience-agent-cp:local .

up: ## Deploy local charts
	@echo "🚀 Deploying Resilience Agent Control Plane Locally"
	helm secrets upgrade --install resilience-agent-cp ../helm-charts/app \
		-n resiltyio \
		-f ./charts/local/control-plane/values.yaml \
		--create-namespace --force

	@echo "🚀 Deploying Resilience Agent Locally"
	helm secrets upgrade --install resilience-agent ../helm-charts/app \
		-n resiltyio \
		-f ./charts/local/secrets.enc.yaml \
		-f ./charts/local/agent/values.yaml --force

down: ## Remove all the deployments
	helm uninstall -n resiltyio resilience-agent resilience-agent-cp

forward: ## Port forward control plane to localhost
	kubectl port-forward svc/resilience-agent-cp 8000:8000

logs: ## Log stream of agent
	kubectl logs -f $$(kubectl get pod -n resiltyio -l app.kubernetes.io/name=resilience-agent -o jsonpath='{.items[0].metadata.name}')


up-nginx: ## Deploy nginx with hpa
	kubectl apply -f ./examples/nginx-hpa.yaml -n nginx

down-nginx: ## Delete nginx deployment
	kubectl delete -f ./examples/nginx-hpa.yaml
