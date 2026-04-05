.DEFAULT_GOAL := help
.PHONY: help lib chart build up down forward logs nginx-up nginx-down http-up http-down

NAMESPACE ?= resiltyio
APP_CHART ?= ../helm-charts/app
AGENT_RELEASE ?= agent
CONTROL_RELEASE ?= controlplane
AGENT_VERSION ?= 1a2b3c4d
RBAC_NAMESPACES ?= nginx,http-echo

AGENT_COMMON_VALUES := ./helm/agent/common.yaml
AGENT_FLUENTBIT_VALUES := ./helm/agent/fluentbit.yaml
AGENT_LOCAL_VALUES := ./helm/agent/local/values.yaml
AGENT_LOCAL_SECRETS := ./helm/agent/local/secrets.enc.yaml
CONTROL_LOCAL_VALUES := ./helm/controlplane/local/values.yaml

HELM_AGENT_ARGS := \
	-f $(AGENT_COMMON_VALUES) \
	-f $(AGENT_FLUENTBIT_VALUES) \
	-f $(AGENT_LOCAL_SECRETS) \
	-f $(AGENT_LOCAL_VALUES) \
	--set-string 'environment_variable.data.RESILTY_AGENT_CONFIG_VERSION=$(AGENT_VERSION)' \
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
	helm secrets template $(AGENT_RELEASE) $(APP_CHART) \
	    -n $(NAMESPACE) \
		$(HELM_AGENT_ARGS)

	helm secrets template $(CONTROL_RELEASE) $(APP_CHART) \
		$(HELM_CONTROL_ARGS)

build: lib ## Build local docker containers
	@eval $(minikube docker-env)
	@echo "🐳 Building Docker containers"
	docker build --no-cache -f ./docker/AgentDockerfile --target local -t resilience-agent:local .
	docker build --no-cache -f ./docker/MockserverDockerfile -t resilience-agent-cp:local .

up: ## Deploy local charts
	@echo "🚀 Deploying Resilience Agent Control Plane Locally"
	helm secrets upgrade --install $(CONTROL_RELEASE) $(APP_CHART) \
		-n $(NAMESPACE) \
		$(HELM_CONTROL_ARGS) \
		--create-namespace --force

	@echo "🚀 Deploying Resilience Agent Locally"
	helm secrets upgrade --install $(AGENT_RELEASE) $(APP_CHART) \
		-n $(NAMESPACE) \
		$(HELM_AGENT_ARGS) \
		--force

down: ## Remove all the deployments
	helm uninstall -n $(NAMESPACE) $(AGENT_RELEASE) $(CONTROL_RELEASE)

forward: ## Port forward control plane to localhost
	kubectl port-forward svc/$(CONTROL_RELEASE) 8000:8000 -n $(NAMESPACE)

logs: ## Log stream of agent
	kubectl logs -f $$(kubectl get pod -n $(NAMESPACE) -l app.kubernetes.io/name=$(AGENT_RELEASE) -o jsonpath='{.items[0].metadata.name}') -n $(NAMESPACE)


nginx-up: ## Deploy nginx with hpa
	@echo "🐳 Building nginx container"
	docker build -f ./docker/NginxDockerfile -t resiltyio-nginx:local .
	kubectl apply -f ./examples/nginx-hpa.yaml -n nginx

nginx-down: ## Delete nginx deployment
	kubectl delete -f ./examples/nginx-hpa.yaml

http-up: ## Deploy http echo with hpa
	kubectl apply -f ./examples/http-echo.yaml -n http-echo

http-down: ## Delete http echo deployment
	kubectl delete -f ./examples/http-echo.yaml
