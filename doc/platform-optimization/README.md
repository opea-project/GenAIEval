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

Warning: installing and reconfiguring the balloons policy can change
allowed CPUs and memories of already running containers in the
cluster. This may hurt containers that rely on the number of allowed
CPUs being static. Furthermore, if there are containers with gigabytes
of memory allocated, reconfiguring the policy may cause the kernel to
move large amounts of memory between NUMA nodes. This may cause
extremely slow response times until moves have finished. Therefore, it
is recommended that nodes are empty or relatively lightly loaded when
new resource policy is applied.

Install the balloons policy with helm:

1. Add the NRI plugins repository
   ```bash
   helm repo add nri-plugins https://containers.github.io/nri-plugins
   ```

2. Install the balloons resource policy and patch container runtime's
   configuration on the individual worker nodes/hosts to enable NRI support.
   ```bash
   helm install balloons nri-plugins/nri-resource-policy-balloons --set patchRuntimeConfig=true
   ```

Now the balloons policy is managing node resources in the cluster as a
DaemonSet that communicates with the container runtime on every node.

## Validate policy status

The balloons policy is running on a node once you can find
`nri-resource-policy-balloons-...` pod.

```
kubectl get pods -A -o wide | grep nri-resource-policy

default   nri-resource-policy-balloons-v6bvq   1/1   Running   0   12s   10.0.0.136   spr-2   <none>   <none>
```

Status of the policy on each node in a cluster can be read from the
balloonspolicy custom resource. For instance, see Status from

```
kubectl describe balloonspolicy default
```

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
there are "tgi", "tei" and "teirerank" containers in "chatqna-tgi" and
"chatqna-tei" and "chatqna-teirerank" deployments that will need a lot
of CPUs. They implement text-generation-interface and
text-embeddings-interface services.

Warning: an
[issue](https://github.com/opea-project/GenAIExamples/issues/763) in
the text-generation-interface causes bad performance when CPUs are
managed. As a workaround, prevent CPU management of these containers
by adding a pod annotation in both "chatqna-tei" and
"chatqna-teirerank" deployments:
```
cpu.preserve.resource-policy.nri.io: "true"
```

A note on terminology: we refer to physical CPU cores as "CPU cores"
and hyperthreads as vCPUs or just CPUs. When hyperthreading is on, the
operating system typically sees every CPU core as two separate vCPUs.

In the example configuration below, we assume that hyperthreading is
on. We allocate 16 CPUs (8 CPU cores with two hyperthreads per core)
for each tgi container, and 32 CPUs (that is 16 CPU cores) for each
tei container. This happens with the following balloons policy
configuration.

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
      operator: In
      values:
      - tei
      - teirerank
  - name: default
    hideHyperthreads: false
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
assigned into a balloon are allowed to use. A CPU belongs into at most
one balloon at a time. CPUs that do not belong to any balloon are
called idle CPUs.

The most important options in the above configuration example are:

- `allocatorTopologyBalancing: true`. This option ensures that
  balloons (sets of allowed CPUs) are balanced between CPU sockets in
  the system. Balancing happens also within a CPU socket if the system
  is running in a sub-NUMA clustering (SNC) mode. Without this option
  balloons would be tightly packed on a single socket allowing the
  other CPU socket to sleep and save power. Here we have optimized for
  performance, but to optimize for power savings, one could
  alternately have set `allocatorTopologyBalancing: false`. For more
  information about sub-NUMA clustering, see [Xeon scalable
  overview](https://www.intel.com/content/www/us/en/developer/articles/technical/fourth-generation-xeon-scalable-family-overview.html)
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
  type are allowed to use only single CPU hyperthread from each CPU
  core in the balloon. By default, both using hyperthreads of all CPUs
  in the balloon is allowed. Note that when `true`, both hyperthreads
  are allocated to the balloon in any case, preventing allocating them
  into other balloons. This ensures that the whole CPU core is
  dedicated to containers in these balloons only.
- `hideHyperthreads: false` allows containers in a balloon use all
  balloon's CPUs, whether or not they are from same CPU cores. As the
  default balloon option, this option applies to all other containers
  but tgi and tei in the example configuration. Note that `false`
  cannot unhide hyperthreads if hyperthreading is off in BIOS.
- `shareIdleCPUsInSame: numa` means that containers in a balloon of
  this type are allowed to use, not only balloon's own CPUs, but also
  idle CPUs within the same NUMA nodes as balloon's own CPUs. This
  enables bursting CPU usage above what is requested by containers in
  the balloon, yet still keep using only CPUs with the lowest latency
  to the data in the memory.

For more information about the configuration and the balloons resource
policy, refer to the balloons
[documentation](https://containers.github.io/nri-plugins/stable/docs/resource-policy/policy/balloons.html).


## Validate CPU affinity and hardware alignment in containers

CPUs allowed in each container of the ChatQnA RAG pipeline can be
listed by running grep in each container. Assuming that the pipeline
is running in the "chatqna" namespace, this can be done as follows.

```
namespace=chatqna
for pod in $(kubectl get pods -n $namespace -o name); do
    echo $(kubectl exec -t -n $namespace $pod -- grep Cpus_allowed_list /proc/self/status) $pod
done | sort

Cpus_allowed_list: 0-30 chatqna-tgi-84c98dd9b7-26dhl
Cpus_allowed_list: 32-39 chatqna-teirerank-7fd4d88d85-swjjv
Cpus_allowed_list: 40-47 chatqna-tei-f5dd58487-vfv45
Cpus_allowed_list: 56-62,120-126 chatqna-85fb984fb9-7rfrk
Cpus_allowed_list: 56-62,120-126 chatqna-data-prep-5489d9b65d-szgth
Cpus_allowed_list: 56-62,120-126 chatqna-embedding-usvc-64566dd669-hdr4k
Cpus_allowed_list: 56-62,120-126 chatqna-llm-uservice-678dc9f98c-tvtqq
Cpus_allowed_list: 56-62,120-126 chatqna-redis-vector-db-676fb75667-trqm6
Cpus_allowed_list: 56-62,120-126 chatqna-reranking-usvc-74b5684cbc-28gdr
Cpus_allowed_list: 56-62,120-126 chatqna-retriever-usvc-64fd64475b-f892k
Cpus_allowed_list: 56-62,120-126 chatqna-ui-dd657bbf6-2wzhr
```

Alignment of allowed CPU sets with the underlying hardware topology
can be validated by comparing above output to CPUs in each NUMA node.

```
lscpu | grep NUMA

NUMA node(s):                       8
NUMA node0 CPU(s):                  0-7,64-71
NUMA node1 CPU(s):                  8-15,72-79
NUMA node2 CPU(s):                  16-23,80-87
NUMA node3 CPU(s):                  24-31,88-95
NUMA node4 CPU(s):                  32-39,96-103
NUMA node5 CPU(s):                  40-47,104-111
NUMA node6 CPU(s):                  48-55,112-119
NUMA node7 CPU(s):                  56-63,120-127
```

This shows that chatqna-tgi is executed on CPUs 0-30, that is, on NUMA
nodes 0-3. All these NUMA nodes are located in the same CPU socket, as
they have the same physical package id:

```
cat /sys/devices/system/node/node[0-3]/cpu*/topology/physical_package_id | sort -u
0
```

The output also shows that chatqna-teirerank and chatqna-tei have been
given CPUs from two separate NUMA nodes (4 and 5) from the other CPU socket.

```
cat /sys/devices/system/node/node[4-5]/cpu*/topology/physical_package_id | sort -u
1
```

Finally, taking a deeper look into CPUs of chatqna-teirerank (32-39),
we can find out that each of them is selected from a separate physical
CPU core in NUMA node4. That is, there are no two vCPUs (hyperthreads)
from the same core.

```
cat /sys/devices/system/node/node4/cpu3[2-9]/topology/core_id
0
1
2
3
4
5
6
7
```

## Remove a policy

The balloons policy is uninstalled from the cluster with helm:

```
helm uninstall balloons
```

Note that removing the policy does not modify CPU affinity (cgroups
cpuset.cpus files) of running containers. For that the containers need
to be recreated or new policy installed.

## NRI topology-aware resource policy

NRI plugins include the topology-aware resource policy, too. Unlike
balloons, it does not require configuration to start with. Instead, it
will create CPU pools for containers purely based on their resource
requests and limits, that must be set for effective use of the
policy. Containers in the
[Guaranteed](https://kubernetes.io/docs/concepts/workloads/pods/pod-qos/#guaranteed)
QoS class get dedicated CPUs. Yet container and node type-specific
configuration possibilities are more limited, the policy works well
for ensuring NUMA alignment and choosing CPUs with low latency access
to accelerators like Gaudi cards. See the topology-aware policy
[documentation](https://containers.github.io/nri-plugins/stable/docs/resource-policy/policy/topology-aware.html)
for more information.
