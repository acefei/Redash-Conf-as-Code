# Telemetry UI Deployment
## Prerequisites
- At least 3 GB of RAM available on your cluster
- Kubernetes 1.19+ - chart is tested with latest 3 stable versions
- Helm 3 (Helm 2 depreciated)
- PV provisioner support in the underlying infrastructure

## Installing the Chart
    ./deploy.sh ui

## Configuration
There is an example for dev env deployment, see ui-value.yaml.

The following configurable parameters need to tweak for production env.

### SAML
Ask IT for the following configuration.

    redash.samlEntityId
    redash.samlMetadataUrl
    redash.samlNameidFormat

### Image Repo
We can customize the image configuration as follows for postgresql and redis.

    image.registry
    image.repository
    image.tag

### Expose UI service
In dev env, we set service.type=NodePort, but there are many downsides to this method:
-    You can only have one service per port
-    You can only use ports 30000–32767 by default
-    If your Node/VM IP address change, you need to deal with that

For these reasons, I don’t recommend using this method in production to directly expose UI service.
You might consider using ingress controller, please find the details in https://kubernetes.io/docs/concepts/services-networking/ingress-controllers/

### PV provisioner
In dev env, we set persistence.enable=false for postgresql and redis.

In production, I hope there is a PV provisioner, and you need to set corresponding persistence configuration.

About the details, please search `persistence` in https://artifacthub.io/packages/helm/bitnami/redis and https://artifacthub.io/packages/helm/bitnami/postgresql

## Access Service
In dev env, gettging the application URL by running these commands:

    export NODE_PORT=$(kubectl get --namespace default -o jsonpath="{.spec.ports[0].nodePort}" services telemetry-ui-redash)
    export NODE_IP=$(kubectl get nodes --namespace default -o jsonpath="{.items[0].status.addresses[0].address}")
    echo http://$NODE_IP:$NODE_PORT

Note: If you want to access UI remotely, please find the bridged IP on the node.

In production, we should access ingress IP directly which would route to UI service.
