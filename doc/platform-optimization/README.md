# Kubernetes Platform Optimization with Resource Management

## Introduction

This document provides an example how to manage which CPUs and
memories (NUMA nodes) are allowed to be used by containers on a
Kubernetes node.

Managing CPUs and memories enables improving AI container performance
and maintaining predictable response times even under heavy
load. Reasons for performance improvements include the following.

- Better cache hit ratios in all cache levels.
- Fewer remote memory accesses.
- Fewer processes and threads per CPU in the whole system.
- Disabling CPU hyperthreading on containers that run faster when the
  other CPU thread is idle.

More predictable response times are possible by using dedicated CPUs
for containers and sets of containers. This ensures that critical
containers will always have enough compute resources, and that
resource hungry containers will not be able to hurt all processes in
the system.

## NRI Plugins

[NRI plugins](https://github.com/containers/nri-plugins) connect to
the container runtime running on a Kubernetes node. Containerd and
CRI-O runtimes support NRI plugins.

The NRI plugins project includes two resource policies, balloons and
topology-aware. They manage allowed CPUs and memories (cpuset.cpus and
cpuset.mems) of all Kubernetes containers created and running on the
node.

In this example, we use the balloons policy because it can be tuned
for certain applications (like RAG pipelines) using even node-specific
parameters for each container in applications. The topology-aware
policy, on the other hand, needs no configuration and does CPU
assignment automatically based on resource requests in containers and
underlying hardware topology.

## Install

Warning: installing and reconfiguring the balloons policy in can
change allowed CPUs and memories of already running containers in the
cluster. This may hurt containers that rely on the number of allowed
CPUs being static.

Install the balloons policy with helm:

1. Add the NRI plugins repository
   ```bash
   helm repo add nri-plugins https://containers.github.io/nri-plugins
   ```

2. Install the balloons resource policy and patch container runtime's
   configuration on host in order to switch NRI support on.
   ```bash
   helm install balloons nri-plugins/nri-resource-policy-balloons --set patchRuntimeConfig=true
   ```

Now the balloons policy is managing node resources in the cluster as a
DaemonSet that communicates with the container runtime on every
node. You should see `nri-resource-policy-balloons-...` pod running on
every node.

## Configure

Edit the default balloons policy:
```bash
kubectl edit balloonspolicy default
```

Let us consider isolating AI inference and reranking containers in
[ChatQnA](https://github.com/opea-project/GenAIExamples/tree/main/ChatQnA)
application's Gaudi accelerated pipeline.

In the
[manifest](https://github.com/opea-project/GenAIExamples/blob/main/ChatQnA/kubernetes/manifests/gaudi/chatqna.yaml)
there are "tgi" and "tei" containers that will need a lot of CPUs.

We will allocate 16 CPUs (8 full CPU cores with two hyperthreads on
each core) for each tgi container, and 32 CPUs (that is 16
hyperthreaded cores) for each tei container. This is done with the
following balloons policy configuration that is explained below.

```yaml
apiVersion: config.nri/v1alpha1
kind: BalloonsPolicy
metadata:
  name: default
spec:
  allocatorTopologyBalancing: true
  balloonTypes:
  - name: tgi
    allocatorPriority: high
    minCPUs: 16
    minBalloons: 1
    preferNewBalloons: true
    hideHyperthreads: true
    matchExpressions:
    - key: name
      operator: Equals
      values: ["tgi"]
  - name: tei
    allocatorPriority: high
    minCPUs: 32
    minBalloons: 1
    preferNewBalloons: true
    hideHyperthreads: true
    matchExpressions:
    - key: name
      operator: Equals
      values: ["tei"]
  - allocatorPriority: normal
    minCPUs: 1
    hideHyperthreads: false
    name: default
    namespaces:
    - "*"
    shareIdleCPUsInSame: numa
  instrumentation:
    httpEndpoint: :8891
    prometheusExport: true
    reportPeriod: 60s
    samplingRatePerMillion: 0
  log:
    source: true
    debug: ["policy"]
  pinCPU: true
  pinMemory: false
  reservedPoolNamespaces:
  - kube-system
  reservedResources:
    cpu: "2"
```

The balloons policy creates "balloons" of CPUs that only containers
assigned into a balloon are allowed to use.

The most important options in the above configuration example are:

- `allocatorTopologyBalancing: true`. This option ensures that
  balloons (sets of allowed CPUs) are balanced between CPU sockets in
  the system, and local NUMA nodes if the system is running a sub-NUMA
  clustering (SNC) mode. Without this options balloons would be
  tightly packed on a single socket allowing the other CPU socket
  sleep and save power. Here we have optimized for performance.
- The list of `balloonTypes` includes two application-specific balloon
  types: one for tgi and one for tei containers.
- `matchExpressions` of a balloon type enable matching containers that
  should be run in balloons of this type. We select tei and tgi
  containers into their special balloon types based on container
  name. Matching could be done based on labels and pod name, too.
- `preferNewBalloon: true` on both tei and tgi balloon types means
  that when a container is assigned into this balloon type and it is
  possible to create a new balloon of this type because there are
  enough free CPUs in the system, then the new balloon will be created
  for the container. As a result, both tei and tgi containers will get
  dedicated set of CPUs, unlike other containers that will run in the
  default balloon type. Each container is allowed to use only CPUs of
  the balloon where they are assigned.
- `minCPUs: 16` and `minCPUs: 32` define the minimum number of CPUs in
  a balloon. Created balloon will never be smaller even if containers
  assigned to a balloon of this type would request fewer or no CPUs at
  all. Correspondingly `maxCPUs` could be used to set an upper limit
  for CPUs.
- `hideHyperthreads: true` means that containers in balloons of this
  type are allowed to use only single CPU hyperthread from each full
  CPU core in the balloon. By default, both using hyperthreads of all
  CPUs in the balloon is allowed. Note that when `true`, both
  hyperthreads are allocated to the balloon in any case, preventing
  alloating them into other balloons. This ensures that the whole CPU
  core is dedicated to containers in these balloons only.

For more information about the configuration and the balloons resource
policy, refer to the balloons
[documentation](https://containers.github.io/nri-plugins/stable/docs/resource-policy/policy/balloons.html).

## NRI topology-aware resource policy

NRI plugins include topology-aware resource policy, too. Unlike
balloons, it does not require configuration to start with. It will
create CPU pools for containers based on their resource requests and
limits. See the topology-aware policy
[documentation](https://containers.github.io/nri-plugins/stable/docs/resource-policy/policy/topology-aware.html)
for more information.
