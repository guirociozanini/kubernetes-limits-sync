from modules import kubernetes_helpers
import json

NAMESPACE = "cd-services"

def write_file(name, data):
    f_name = "base-limits/" + name + ".json"
    f = open(f_name, "w")
    f.write(data)
    f.close()

def download_limits(namespace):
    data = kubernetes_helpers.retrieve_deployments_by_ns(namespace)

    for deployment in data['items']:
        deployment_spec = deployment['spec']
        template = deployment_spec['template']['spec']
        containers = template['containers']

        deployment_parsed = {}
        
        for container in containers:
            deployment_parsed[container['name']] = container['resources']

        write_file(
            deployment['metadata']['name'],
            json.dumps(deployment_parsed)
        )

download_limits(namespace)