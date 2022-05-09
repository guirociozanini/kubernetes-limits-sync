from kubernetes import client, config
import json

# Kubernetes client
config.load_kube_config()
api = client.AppsV1Api()

def retrieve_deployments_by_ns(namespace):
    response = api.list_namespaced_deployment(
        namespace=namespace,
        _preload_content=False
    )

    return json.loads(response.data)

def update_deployment(deployment_name, deployment, namespace):
    # Kubernetes client
    return api.patch_namespaced_deployment(
        name=deployment_name, namespace=namespace, body=deployment
    )
