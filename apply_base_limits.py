from modules import kubernetes_helpers
from kubernetes import client, config
from os.path import exists
import sys
import json
import click
import yaml

NAMESPACE   = sys.argv[1]
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

    #backup old deployment manifest
    write_file('old-' + deployment_name, yaml.dump(deployment))

    for index, container in enumerate(containers):
        deployment['spec']['template']['spec']['containers'][index]['resources'] = new_limits[container['name']]

    deployment_yaml = yaml.dump(deployment)

    #write new deployment manifest
    write_file('new-' + deployment_name, deployment_yaml)

    resp = kubernetes_helpers.update_deployment(deployment_name, deployment, NAMESPACE)

    print(f"[INFO] {deployment_name} container limits updated.")

def sync_base_limits():
    deployments = kubernetes_helpers.retrieve_deployments_by_ns(NAMESPACE)

    sync_all = click.confirm('Sync all without confirmation?', default=False)

    for deployment in deployments['items']:
        deployment_spec = deployment['spec']
        deployment_name = deployment['metadata']['name']
        template = deployment_spec['template']['spec']
        containers = template['containers']

        if deployment_name in DEPLOYMENTS_TO_IGNORE:
            print(f"[INFO] Deployment {deployment_name} marked to ignore")
            continue

        if has_base_limit(deployment_name):
            base_limit = load_base_limit(deployment_name)
            old_limits = pluck(containers, 'resources')

            sync = True
            if sync_all == False:               
                message = "\nReview the following limits of " + deployment_name
                message += "\n Old limits: " + json.dumps(old_limits[0], indent=2)
                message += "\n New limits: " + json.dumps(base_limit[deployment_name], indent=2)
                print(message)

                sync = click.confirm("Confirm?", default=False)

            if sync:
                update_limit(deployment, base_limit)
        else:
            print(f"[WARN] Deployment {deployment_name} base limit doesn't exists")

sync_base_limits()