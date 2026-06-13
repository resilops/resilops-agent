{{/*
Expand the name of the chart.
*/}}
{{- define "resilienceAgent.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "resilienceAgent.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "resilienceAgent.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "resilienceAgent.labels" -}}
helm.sh/chart: {{ include "resilienceAgent.chart" . }}
{{ include "resilienceAgent.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "resilienceAgent.selectorLabels" -}}
app.kubernetes.io/name: {{ include "resilienceAgent.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "resilienceAgent.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "resilienceAgent.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Environment variables from secrets
*/}}
{{- define "resilienceAgent.envFromSecrets" -}}
{{- if .Values.secrets }}
{{- range $key, $_ := .Values.secrets }}
- name: {{ $key | upper | replace "-" "_" }}
  valueFrom:
    secretKeyRef:
      name: {{ include "resilienceAgent.name" $ }}-secret
      key: {{ $key }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Environment variables from existing secrets (main container)
*/}}
{{- define "resilienceAgent.envFromExistingSecrets" -}}
{{- $secretName := .Values.existingSecret.name | default "" -}}
{{- $items := .Values.existingSecret.app | default list -}}
{{- if and $secretName (gt (len $items) 0) -}}
{{- range $items }}
- name: {{ .envName }}
  valueFrom:
    secretKeyRef:
      name: {{ $secretName }}
      key: {{ .secretKey }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Environment variables from configmap
*/}}
{{- define "resilienceAgent.envFromConfigMap" -}}
{{- if .Values.envVar.enabled }}
{{- range $key, $value := .Values.envVar.data }}
- name: {{ $key }}
  valueFrom:
    configMapKeyRef:
      name: {{ include "resilienceAgent.name" $ }}-configmap
      key: {{ $key }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Environment variables from existing secrets (sidecar)
*/}}
{{- define "resilienceAgent.sidecarEnvFromExistingSecrets" -}}
{{- $secretName := .Values.sidecar.existingSecret.name | default "" -}}
{{- $items := .Values.sidecar.existingSecret.data | default list -}}
{{- if and $secretName (gt (len $items) 0) -}}
{{- range $items }}
- name: {{ .envName }}
  valueFrom:
    secretKeyRef:
      name: {{ $secretName }}
      key: {{ .secretKey }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Whether existing secrets are configured for the sidecar
*/}}
{{- define "resilienceAgent.hasSidecarExistingSecrets" -}}
{{- $secretName := .Values.sidecar.existingSecret.name | default "" -}}
{{- $items := .Values.sidecar.existingSecret.data | default list -}}
{{- if and $secretName (gt (len $items) 0) -}}true{{- end -}}
{{- end }}
