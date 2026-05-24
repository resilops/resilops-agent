.DEFAULT_GOAL := help
.PHONY: help lib chart build secrets up down forward logs nginx-up nginx-down http-up http-down

ifneq (,$(wildcard .env))
include .env
export
endif

NAMESPACE ?= resiltyio
APP_CHART ?= ../helm-charts/app
AGENT_RELEASE ?= agent
CONTROL_RELEASE ?= controlplane
AGENT_CONFIG_VERSION ?= OC551dpOH70
RBAC_NAMESPACES ?= nginx,http-echo
SECRETS_NAME ?= resilty-agent-secrets

AGENT_COMMON_VALUES := ./helm/agent/common.yaml
AGENT_LOCAL_VALUES := ./helm/agent/local/values.yaml
CONTROL_LOCAL_VALUES := ./helm/controlplane/local/values.yaml

HELM_AGENT_ARGS := \
	-f $(AGENT_COMMON_VALUES) \
	-f $(AGENT_LOCAL_VALUES) \
	--set-string 'envVar.data.RESILTY_AGENT_CONFIG_VERSION=$(AGENT_CONFIG_VERSION)' \
	--set 'rbac.namespaced.namespaces={$(RBAC_NAMESPACES)}'

HELM_CONTROL_ARGS := \
	-f $(CONTROL_LOCAL_VALUES)

## Show help for all commands
help:
	@echo "Available commands:"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z0-9._-]+:.*?## / {printf "  \033[36m%-25s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

lib: ## Install resilience-lib
	@rsync -av --exclude='pyenv' ../resilience-lib/ ./local-libs/resilience-lib

chart: ## Build local kubernetes charts
	helm template $(AGENT_RELEASE) $(APP_CHART) \
		-n $(NAMESPACE) \
		$(HELM_AGENT_ARGS)

	helm template $(CONTROL_RELEASE) $(APP_CHART) \
		-n $(NAMESPACE) \
		$(HELM_CONTROL_ARGS)

build: lib ## Build local docker containers
	@eval $(minikube docker-env)
	@echo "🐳 Building Docker containers"
	docker build --no-cache -f ./docker/AgentDockerfile --target local -t resilience-agent:local .
	docker build --no-cache -f ./docker/MockserverDockerfile -t resilience-agent-cp:local .
	minikube image load resilience-agent:local
	minikube image load resilience-agent-cp:local

secrets: ## Create/update local agent secret from .env
	@test -n "$(OAUTH_CLIENT_ID)" || (echo "OAUTH_CLIENT_ID is not set"; exit 1)
	@test -n "$(OAUTH_CLIENT_SECRET)" || (echo "OAUTH_CLIENT_SECRET is not set"; exit 1)
	kubectl -n $(NAMESPACE) create secret generic $(SECRETS_NAME) \
		--from-literal=OAUTH_CLIENT_ID="$(OAUTH_CLIENT_ID)" \
		--from-literal=OAUTH_CLIENT_SECRET="$(OAUTH_CLIENT_SECRET)" \
		--dry-run=client -o yaml | kubectl apply -f -

up: ## Deploy local charts
	@echo "🚀 Deploying Resilience Agent Control Plane Locally"
	helm upgrade --install $(CONTROL_RELEASE) $(APP_CHART) \
		-n $(NAMESPACE) \
		$(HELM_CONTROL_ARGS) \
		--create-namespace --force

	@echo "🚀 Deploying Resilience Agent Locally"
	helm upgrade --install $(AGENT_RELEASE) $(APP_CHART) \
		-n $(NAMESPACE) \
		$(HELM_AGENT_ARGS) \
		--force

down: ## Remove all the deployments
	helm uninstall -n $(NAMESPACE) $(AGENT_RELEASE) $(CONTROL_RELEASE)

forward: ## Port forward control plane to localhost
	kubectl port-forward svc/$(CONTROL_RELEASE) 8000:8000 -n $(NAMESPACE)

logs: ## Log stream of agent
	kubectl logs -f $$(kubectl get pod -n $(NAMESPACE) -l app.kubernetes.io/name=$(AGENT_RELEASE) -o jsonpath='{.items[0].metadata.name}') -n $(NAMESPACE)

logs-fluentbit: ## Log stream of fluentbit
	kubectl logs -f $$(kubectl get pod -n $(NAMESPACE) -l app.kubernetes.io/name=$(AGENT_RELEASE) -o jsonpath='{.items[0].metadata.name}') -c fluent-bit-sidecar -n $(NAMESPACE)


nginx-up: ## Deploy nginx with hpa
	@echo "🐳 Building nginx container"
	docker build -f ./docker/NginxDockerfile -t resiltyio-nginx:local .
	minikube image load resiltyio-nginx:local
	kubectl apply -f ./examples/nginx-hpa.yaml -n nginx

nginx-down: ## Delete nginx deployment
	kubectl delete -f ./examples/nginx-hpa.yaml

http-up: ## Deploy http echo with hpa
	kubectl apply -f ./examples/http-echo.yaml -n http-echo

http-down: ## Delete http echo deployment
	kubectl delete -f ./examples/http-echo.yaml
