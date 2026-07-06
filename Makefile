.DEFAULT_GOAL := help
.PHONY: help lib chart build secrets up down forward logs examples-up examples-down tests cicd-test

ifneq (,$(wildcard .env))
include .env
export
endif

NAMESPACE ?= resilops
AGENT_CHART ?= ./helm/agent
AGENT_VALUES ?= ./helm/local.yaml
AGENT_RELEASE ?= agent
AGENT_CONFIG_VERSION ?= hT8ahyVif9Q
RBAC_NAMESPACES ?= nginx,http-echo
SECRETS_NAME ?= resilops-agent-secrets

HELM_AGENT_ARGS := \
	--set 'region.name=local' \
	--set-string 'image.tag=local' \
	--set-string 'envVar.data.RESILOPS_AGENT_CONFIG_VERSION=$(AGENT_CONFIG_VERSION)' \
	--set 'rbac.namespaced.namespaces={$(RBAC_NAMESPACES)}'

## Show help for all commands
help:
	@echo "Available commands:"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z0-9._-]+:.*?## / {printf "  \033[36m%-25s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

lib: ## Install resilience-lib
	@rsync -av --exclude='pyenv' ../resilience-lib/ ./local-libs/resilience-lib

chart: ## Build local kubernetes charts
	helm template $(AGENT_RELEASE) $(AGENT_CHART) \
		-n $(NAMESPACE) \
		-f $(AGENT_VALUES) \
		$(HELM_AGENT_ARGS)

build: lib ## Build local agent and mock control plane images for Minikube
	@eval $(minikube docker-env)
	@echo "🐳 Building local images"
	docker build --no-cache -f ./docker/agent.Dockerfile -t resilops-agent:local .
	docker build --no-cache -f ./docker/mockserver.Dockerfile -t resilops-agent-cp:local .
	minikube image load resilops-agent:local
	minikube image load resilops-agent-cp:local

secrets: ## Create/update local agent secret from .env
	@test -n "$(OAUTH_CLIENT_ID)" || (echo "OAUTH_CLIENT_ID is not set"; exit 1)
	@test -n "$(OAUTH_CLIENT_SECRET)" || (echo "OAUTH_CLIENT_SECRET is not set"; exit 1)
	kubectl -n $(NAMESPACE) create secret generic $(SECRETS_NAME) \
		--from-literal=OAUTH_CLIENT_ID="$(OAUTH_CLIENT_ID)" \
		--from-literal=OAUTH_CLIENT_SECRET="$(OAUTH_CLIENT_SECRET)" \
		--dry-run=client -o yaml | kubectl apply -f -

up: ## Deploy mock control plane and resilience agent
	kubectl create namespace $(NAMESPACE) --dry-run=client -o yaml | kubectl apply -f -
	@echo "🚀 Deploying mock control plane"
	kubectl apply -n $(NAMESPACE) -f ./mockserver/deployment.yaml
	@echo "🚀 Deploying resilience agent"
	helm upgrade --install $(AGENT_RELEASE) $(AGENT_CHART) \
		-n $(NAMESPACE) \
		-f $(AGENT_VALUES) \
		$(HELM_AGENT_ARGS) \
		--force

down: ## Remove mock control plane and resilience agent
	helm uninstall -n $(NAMESPACE) $(AGENT_RELEASE)
	kubectl delete -n $(NAMESPACE) -f ./mockserver/deployment.yaml --ignore-not-found

forward: ## Port forward control plane to localhost
	kubectl port-forward svc/controlplane 8000:8000 -n $(NAMESPACE)

logs: ## Log stream of agent
	kubectl logs -f $$(kubectl get pod -n $(NAMESPACE) -l app.kubernetes.io/name=$(AGENT_RELEASE) -o jsonpath='{.items[0].metadata.name}') -n $(NAMESPACE)

examples-up: ## Deploy example workloads
	@eval $(minikube docker-env)
	@echo "🐳 Building nginx example image"
	docker build -f ./docker/nginx-example.Dockerfile -t resilops-nginx:local .
	minikube image load resilops-nginx:local
	kubectl apply -f ./examples/workloads/nginx-hpa.yaml -n nginx
	kubectl apply -f ./examples/workloads/http-echo.yaml -n http-echo

examples-down: ## Delete example workloads
	kubectl delete -f ./examples/workloads/http-echo.yaml
	kubectl delete -f ./examples/workloads/nginx-hpa.yaml

logs-fluentbit: ## Log stream of fluentbit
	kubectl logs -f $$(kubectl get pod -n $(NAMESPACE) -l app.kubernetes.io/name=$(AGENT_RELEASE) -o jsonpath='{.items[0].metadata.name}') -c fluent-bit-sidecar -n $(NAMESPACE)

tests: ## Run unit tests with coverage gate
	poetry run pytest
