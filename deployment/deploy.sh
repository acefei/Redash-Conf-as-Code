ui() {
    helm repo add redash https://getredash.github.io/contrib-helm-chart/
    helm upgrade --install -f ui-value.yaml telemetry-ui redash/redash
}

mongodb() {
    helm repo add bitnami https://charts.bitnami.com/bitnami
    helm upgrade --install -f mongo-value.yaml datasource bitnami/mongodb
}


case ${1:-help} in
ui|mongodb)
    eval "$1"
    ;;
*)
     echo "usage: $0 [ui|mongodb]"
esac
