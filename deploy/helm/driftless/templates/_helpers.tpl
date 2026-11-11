{{- define "driftless.labels" -}}
app.kubernetes.io/part-of: driftless
app.kubernetes.io/managed-by: {{ .Release.Service }}
helm.sh/chart: {{ .Chart.Name }}-{{ .Chart.Version }}
{{- end -}}

{{- define "driftless.image" -}}
{{- $root := index . 0 -}}{{- $c := index . 1 -}}
{{ $root.Values.image.registry }}/{{ $c.image }}:{{ $root.Values.image.tag | default $root.Chart.AppVersion }}
{{- end -}}
