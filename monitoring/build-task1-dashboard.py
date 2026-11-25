import json
from pathlib import Path

output = Path(__file__).resolve().parent
datasource = {"type": "prometheus", "uid": "prometheus"}

namespace = 'namespace=~"${namespace:regex}"'
container_legend = "{{namespace}}/{{pod}}/{{container}}"
panels = []


def panel(title, description, queries, x, y,
          unit="short", kind="timeseries", width=12, height=8):
    item = {
        "id": len(panels) + 1,
        "title": title,
        "description": description,
        "type": kind,
        "datasource": datasource,
        "gridPos": {"x": x, "y": y, "w": width, "h": height},
        "fieldConfig": {
            "defaults": {
                "unit": unit,
                "decimals": 2,
                "color": {"mode": "palette-classic"}
            },
            "overrides": []
        },
        "targets": [
            {
                "refId": chr(65 + index),
                "datasource": datasource,
                "expr": expression,
                "legendFormat": legend,
                "editorMode": "code",
                "format": "table" if kind == "table" else "time_series",
                "instant": kind in ("stat", "table"),
                "range": kind == "timeseries"
            }
            for index, (expression, legend) in enumerate(queries)
        ]
    }

    if kind == "timeseries":
        item["options"] = {
            "legend": {"displayMode": "list", "placement": "bottom"},
            "tooltip": {"mode": "multi", "sort": "desc"}
        }
    elif kind == "stat":
        item["fieldConfig"]["defaults"]["decimals"] = 0
        item["options"] = {
            "reduceOptions": {
                "calcs": ["lastNotNull"],
                "fields": "",
                "values": False
            },
            "graphMode": "none",
            "textMode": "auto",
            "colorMode": "value"
        }
    else:
        item["options"] = {"showHeader": True}
        item["transformations"] = [
            {
                "id": "filterFieldsByName",
                "options": {
                    "include": {
                        "names": [
                            "namespace", "pod", "container", "reason", "Value"
                        ]
                    }
                }
            }
        ]

    panels.append(item)


panel(
    "MongoDB available",
    "1 — the exporter can connect to MongoDB; 0 — the connection failed.",
    [('max(mongodb_up{namespace="demo"})', "MongoDB")],
    0, 0, kind="stat", width=6, height=4
)

panel(
    "Scrape targets DOWN",
    "Number of endpoints that Prometheus failed to scrape.",
    [('sum(1 - up)', "DOWN")],
    6, 0, kind="stat", width=6, height=4
)

panel(
    "Container restarts / 15m",
    "Increase in container restarts over the last 15 minutes for the selected namespaces.",
    [('sum(increase(kube_pod_container_status_restarts_total{'
      + namespace + '}[15m]))', "Restarts")],
    12, 0, kind="stat", width=6, height=4
)

panel(
    "Running pods",
    "Number of pods in the Running phase. Running does not guarantee readiness.",
    [('sum(kube_pod_status_phase{' + namespace
      + ',phase="Running"} == 1)', "Running")],
    18, 0, kind="stat", width=6, height=4
)

panel(
    "Node CPU usage",
    "Node CPU utilization based on metrics collected by node-exporter.",
    [('100 * (1 - avg by (instance) (rate('
      'node_cpu_seconds_total{job="node-exporter",mode="idle"}'
      '[$__rate_interval])))', "{{instance}}")],
    0, 4, unit="percent"
)

panel(
    "Node memory usage",
    "Percentage of node memory in use, calculated from total minus available memory.",
    [('100 * (1 - node_memory_MemAvailable_bytes{job="node-exporter"}'
      ' / node_memory_MemTotal_bytes{job="node-exporter"})',
      "{{instance}}")],
    12, 4, unit="percent"
)

panel(
    "Container CPU: usage / request / limit",
    "Actual CPU usage compared with container resource requests and limits. "
    "Measured in CPU cores; for example, 0.1 core equals 100m.",
    [
        ('sum by (namespace,pod,container) (rate('
         'container_cpu_usage_seconds_total{' + namespace
         + ',container!="",container!="POD",image!=""}'
         '[$__rate_interval]))',
         container_legend + " usage"),
        ('max by (namespace,pod,container) ('
         'kube_pod_container_resource_requests{' + namespace
         + ',resource="cpu",unit="core"})',
         container_legend + " request"),
        ('max by (namespace,pod,container) ('
         'kube_pod_container_resource_limits{' + namespace
         + ',resource="cpu",unit="core"})',
         container_legend + " limit")
    ],
    0, 12, unit="cores"
)

panel(
    "Container memory: usage / request / limit",
    "Container working set compared with memory requests and limits. "
    "Helps identify containers approaching their memory limits.",
    [
        ('max by (namespace,pod,container) ('
         'container_memory_working_set_bytes{' + namespace
         + ',container!="",container!="POD",image!=""})',
         container_legend + " usage"),
        ('max by (namespace,pod,container) ('
         'kube_pod_container_resource_requests{' + namespace
         + ',resource="memory",unit="byte"})',
         container_legend + " request"),
        ('max by (namespace,pod,container) ('
         'kube_pod_container_resource_limits{' + namespace
         + ',resource="memory",unit="byte"})',
         container_legend + " limit")
    ],
    12, 12, unit="bytes"
)

panel(
    "Restarts by container / 15m",
    "Identifies containers that restarted during the last 15 minutes.",
    [('sum by (namespace,pod,container) (increase('
      'kube_pod_container_status_restarts_total{'
      + namespace + '}[15m]))', container_legend)],
    0, 20
)

panel(
    "Last termination: OOMKilled",
    "Containers whose last recorded termination reason is OOMKilled. "
    "This is not a count of recent OOM events; correlate it with recent restarts. "
    "An empty table is expected when no matching terminations have been recorded.",
    [('kube_pod_container_status_last_terminated_reason{'
      + namespace + ',reason="OOMKilled"} == 1', "")],
    12, 20, kind="table"
)

panel(
    "MongoDB asserts: total",
    "Cumulative assertion counters grouped by type. "
    "An increasing user counter requires log analysis; it does not by itself indicate a database outage.",
    [('mongodb_asserts_total{namespace="demo"}', "{{type}}")],
    0, 28
)

panel(
    "MongoDB asserts: increase / 5m",
    "Increase in assertions over five minutes. Only mongodb_asserts_total is used "
    "to avoid double-counting the same data exposed as mongodb_ss_asserts.",
    [('sum by (type) (increase('
      'mongodb_asserts_total{namespace="demo"}[5m]))', "{{type}}")],
    12, 28
)

dashboard = {
    "id": None,
    "uid": "week13-task1",
    "title": "Week13 | Task 1 - Infrastructure & MongoDB",
    "description": (
        "Node, container, and MongoDB monitoring. "
        "The namespace filter applies to workload panels; "
        "node and MongoDB panels use fixed sources. "
        "Kubernetes Events will be added in a later stage."
    ),
    "tags": ["week13", "task1", "kubernetes", "mongodb"],
    "timezone": "Europe/Warsaw",
    "schemaVersion": 39,
    "version": 1,
    "editable": False,
    "refresh": "30s",
    "time": {"from": "now-1h", "to": "now"},
    "templating": {
        "list": [
            {
                "name": "namespace",
                "label": "Workload namespace",
                "type": "query",
                "datasource": datasource,
                "query": "label_values(kube_pod_info, namespace)",
                "refresh": 1,
                "sort": 1,
                "multi": True,
                "includeAll": True,
                "allValue": ".+",
                "current": {"text": ["demo"], "value": ["demo"]},
                "options": []
            }
        ]
    },
    "panels": panels
}


# BEGIN KUBERNETES EVENTS PANELS
loki_datasource = {"type": "loki", "uid": "loki"}

events_selector = (
    '{job="kubernetes-events",'
    'namespace=~"${namespace:regex}"}'
)

panel(
    "Kubernetes event records / 5m",
    "Number of event log records received per namespace over a rolling "
    "5-minute window. Updates to the same Kubernetes Event may produce "
    "multiple records. No data means no matching records in that window.",
    [
        (
            "sum by (namespace) (count_over_time("
            + events_selector + "[5m]))",
            "{{namespace}}"
        )
    ],
    0, 36, width=24, height=6
)

panels[-1]["datasource"] = loki_datasource

for target in panels[-1]["targets"]:
    target["datasource"] = loki_datasource
    target["queryType"] = "range"

panels.append({
    "id": max(item["id"] for item in panels) + 1,
    "title": "Kubernetes Events",
    "description": (
        "Kubernetes Events collected by Alloy and stored in Loki. "
        "Expand a record to inspect its reason, object name and message. "
        "Filtered by Workload namespace and the dashboard time range."
    ),
    "type": "logs",
    "datasource": loki_datasource,
    "gridPos": {"x": 0, "y": 42, "w": 24, "h": 12},
    "targets": [
        {
            "refId": "A",
            "datasource": loki_datasource,
            "expr": events_selector,
            "editorMode": "code",
            "queryType": "range",
            "maxLines": 200
        }
    ],
    "options": {
        "showTime": True,
        "showLabels": False,
        "showCommonLabels": False,
        "wrapLogMessage": True,
        "prettifyLogMessage": True,
        "enableLogDetails": True,
        "dedupStrategy": "none",
        "sortOrder": "Descending"
    }
})

dashboard["description"] = (
    "Node, container and MongoDB metrics with Kubernetes Events "
    "collected by Alloy and stored in Loki. Workload namespace "
    "filters workload and event panels."
)
# END KUBERNETES EVENTS PANELS


# Kubernetes Events panels
loki_datasource = {"type": "loki", "uid": "loki"}
events_selector = (
    '{job="kubernetes-events",'
    'namespace=~"${namespace:regex}"}'
)

panel(
    "Kubernetes Event records / 5m",
    "Number of event log records collected in each rolling 5-minute window. "
    "Updates to the same Kubernetes Event can produce multiple records.",
    [(
        "sum by (namespace) (count_over_time("
        + events_selector + "[5m]))",
        "{{namespace}}"
    )],
    0, 36, width=24, height=6
)

panels[-1]["datasource"] = loki_datasource
for target in panels[-1]["targets"]:
    target["datasource"] = loki_datasource
    target["queryType"] = "range"

panels.append({
    "id": len(panels) + 1,
    "title": "Kubernetes Events",
    "description": (
        "Kubernetes Events collected by Alloy and stored in Loki. "
        "Expand a record to inspect its reason, object and message."
    ),
    "type": "logs",
    "datasource": loki_datasource,
    "gridPos": {"x": 0, "y": 42, "w": 24, "h": 12},
    "targets": [{
        "refId": "A",
        "datasource": loki_datasource,
        "expr": events_selector,
        "queryType": "range",
        "editorMode": "code",
        "maxLines": 200
    }],
    "options": {
        "showTime": True,
        "showLabels": False,
        "showCommonLabels": False,
        "wrapLogMessage": True,
        "prettifyLogMessage": True,
        "enableLogDetails": True,
        "dedupStrategy": "none",
        "sortOrder": "Descending"
    }
})

dashboard["description"] = (
    "Node, container and MongoDB metrics with Kubernetes Events "
    "collected by Alloy and stored in Loki. "
    "Workload namespace filters workload and event panels."
)


dashboard_json = json.dumps(dashboard, ensure_ascii=False, indent=2)

configmap = {
    "apiVersion": "v1",
    "kind": "ConfigMap",
    "metadata": {
        "name": "week13-task1-dashboard",
        "namespace": "monitoring",
        "labels": {"grafana_dashboard": "1"}
    },
    "data": {"week13-task1.json": dashboard_json}
}

(output / "task1-dashboard.json").write_text(
    dashboard_json + "\n", encoding="utf-8"
)

(output / "task1-dashboard-configmap.json").write_text(
    json.dumps(configmap, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8"
)

print(f"Dashboard created: {len(panels)} panels")
print("ConfigMap created: monitoring/task1-dashboard-configmap.json")
