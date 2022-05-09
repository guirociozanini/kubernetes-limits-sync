from modules import kubernetes_helpers
from kubernetes import client, config
from os.path import exists
import json
import click
import yaml

NAMESPACE   = "of-services"
BASE_FOLDER = "base-limits/"
OUTPUT_FOLDER = "output-deployments/"
DEPLOYMENTS_TO_IGNORE = ["blu-cli", "redis", "blu-connectors"]

def has_base_limit(name):
    return exists(BASE_FOLDER + name + ".json")

def load_base_limit(name):
    f = open(BASE_FOLDER + name + ".json", "r")
    return json.loads(f.read())

def write_file(name, data):
    f_name = OUTPUT_FOLDER + f"{NAMESPACE}-{name}.yaml"
    f = open(f_name, "w")
    f.write(data)
    f.close()

def pluck(lst, key):
    return [x.get(key) for x in lst]

def update_limit(deployment, new_limits):
    containers = deployment['spec']['template']['spec']['containers']
    deployment_name = deployment['metadata']['name']

    for index, container in enumerate(containers):
        deployment['spec']['template']['spec']['containers'][index]['resources'] = new_limits[container['name']]

    deployment_yaml = yaml.dump(deployment)
    write_file(deployment_name, deployment_yaml)

    kubernetes_helpers.update_deployment(deployment_name, deployment, NAMESPACE)

    print("\n[INFO] deployment's container limits updated.\n")
    print("%s\t%s\t\t\t%s\t%s" % ("NAMESPACE", "NAME", "REVISION", "IMAGE"))
    print(
        "%s\t\t%s\t%s\t\t%s\n"
        % (
            resp.metadata.namespace,
            resp.metadata.name,
            resp.metadata.generation,
            resp.spec.template.spec.containers[0].image,
        )
    )

def sync_base_limits():
    deployments = kubernetes_helpers.retrieve_deployments_by_ns(NAMESPACE)

    for deployment in deployments['items']:
        deployment_spec = deployment['spec']
        deployment_name = deployment['metadata']['name']
        template = deployment_spec['template']['spec']
        containers = template['containers']

        if deployment_name in DEPLOYMENTS_TO_IGNORE:
            print(f"Deployment {deployment_name} marked to ignore")
            continue

        if has_base_limit(deployment_name):
            base_limit = load_base_limit(deployment_name)
            old_limits = pluck(containers, 'resources')

            message = "\nReview the following limits of " + deployment_name
            message += "\n Old limits: " + json.dumps(old_limits[0], indent=2)
            message += "\n New limits: " + json.dumps(base_limit[deployment_name], indent=2)
            print(message)

            if click.confirm("Confirm?", default=False):
                update_limit(deployment, base_limit)
        else:
            print(f"Deployment {deployment_name} base limit doesn't exists")

sync_base_limits()