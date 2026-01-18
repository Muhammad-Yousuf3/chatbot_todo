{{/*
Common labels
*/}}
{{- define "todo-chatbot.labels" -}}
app.kubernetes.io/name: {{ .Chart.Name }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
helm.sh/chart: {{ .Chart.Name }}-{{ .Chart.Version }}
{{- end }}

{{/*
Selector labels for backend
*/}}
{{- define "todo-chatbot.backend.selectorLabels" -}}
app: todo-backend
app.kubernetes.io/name: {{ .Chart.Name }}-backend
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Selector labels for frontend
*/}}
{{- define "todo-chatbot.frontend.selectorLabels" -}}
app: todo-frontend
app.kubernetes.io/name: {{ .Chart.Name }}-frontend
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Backend fullname
*/}}
{{- define "todo-chatbot.backend.fullname" -}}
todo-backend
{{- end }}

{{/*
Frontend fullname
*/}}
{{- define "todo-chatbot.frontend.fullname" -}}
todo-frontend
{{- end }}

{{/*
ConfigMap name for backend
*/}}
{{- define "todo-chatbot.backend.configmap" -}}
todo-backend-config
{{- end }}

{{/*
Secret name for backend
*/}}
{{- define "todo-chatbot.backend.secret" -}}
todo-backend-secrets
{{- end }}

{{/*
ConfigMap name for frontend
*/}}
{{- define "todo-chatbot.frontend.configmap" -}}
todo-frontend-config
{{- end }}

{{/*
Image pull policy - use backend-specific if set, otherwise global
*/}}
{{- define "todo-chatbot.backend.imagePullPolicy" -}}
{{- if .Values.backend.image.pullPolicy }}
{{- .Values.backend.image.pullPolicy }}
{{- else }}
{{- .Values.global.imagePullPolicy }}
{{- end }}
{{- end }}

{{/*
Image pull policy for frontend
*/}}
{{- define "todo-chatbot.frontend.imagePullPolicy" -}}
{{- if .Values.frontend.image.pullPolicy }}
{{- .Values.frontend.image.pullPolicy }}
{{- else }}
{{- .Values.global.imagePullPolicy }}
{{- end }}
{{- end }}
