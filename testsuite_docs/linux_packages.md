### [perfkitbenchmarker.linux_packages.act ](../perfkitbenchmarker/linux_packages/act.py)

#### Description:

Module containing aerospike server installation and cleanup functions.

#### Flags:

`--act_duration`: Duration of act test in seconds.
    (default: '86400')
    (an integer)

`--act_load`: Load multiplier for act test per device.
    (default: '1.0')
    (a comma separated list)

`--act_num_queues`: Total number of transaction queues. Default is number of
    cores, detected by ACT at runtime.
    (an integer)

`--[no]act_parallel`: Run act tools in parallel. One copy per device.
    (default: 'false')

`--act_reserved_partitions`: Number of partitions reserved (not being used by
    act).
    (default: '0')
    (an integer)

`--act_threads_per_queue`: Number of threads per transaction queue. Default is 4
    threads/queue.
    (an integer)

### [perfkitbenchmarker.linux_packages.aerospike_server ](../perfkitbenchmarker/linux_packages/aerospike_server.py)

#### Description:

Module containing aerospike server installation and cleanup functions.

#### Flags:

`--aerospike_replication_factor`: Replication factor for aerospike server.
    (default: '1')
    (an integer)

`--aerospike_storage_type`: <memory|disk>: The type of storage to use for
    Aerospike data. The type of disk is controlled by the "data_disk_type" flag.
    (default: 'memory')

`--aerospike_transaction_threads_per_queue`: Number of threads per transaction
    queue.
    (default: '4')
    (an integer)

### [perfkitbenchmarker.linux_packages.aws_credentials ](../perfkitbenchmarker/linux_packages/aws_credentials.py)

#### Description:

Module containing AWS credential file installation and cleanup helpers.

AWS credentials consist of a secret access key and its ID, stored in a single
file. Following PKB's AWS setup instructions (see
https://github.com/GoogleCloudPlatform/PerfKitBenchmarker#install-aws-cli-and-setup-authentication),
the default location of the file will be at ~/.aws/credentials

This package copies the credentials file to the remote VM to make them available
for calls from the VM to other AWS services, such as SQS or Kinesis.


#### Flags:

`--aws_credentials_local_path`: Path where the AWS credential files can be found
    on the local machine.
    (default: '~/.aws')

`--[no]aws_credentials_overwrite`: When set, if an AWS credential file already
    exists at the destination specified by --aws_credentials_remote_path, it
    will be overwritten during AWS credential file installation.
    (default: 'false')

`--aws_credentials_remote_path`: Path where the AWS credential files will be
    written on remote machines.
    (default: '.aws')

`--aws_s3_region`: Region for the S3 bucket

### [perfkitbenchmarker.linux_packages.azure_sdk ](../perfkitbenchmarker/linux_packages/azure_sdk.py)

#### Description:

Package for installing the Azure SDK.

#### Flags:

`--azure_lib_version`: Use a particular version of azure client lib, e.g.: 1.0.2
    (default: '1.0.3')

### [perfkitbenchmarker.linux_packages.cassandra ](../perfkitbenchmarker/linux_packages/cassandra.py)

#### Description:

Installs/Configures Cassandra.

See 'perfkitbenchmarker/data/cassandra/' for configuration files used.

Cassandra homepage: http://cassandra.apache.org


#### Flags:

`--cassandra_concurrent_reads`: Concurrent read requests each server accepts.
    (default: '32')
    (an integer)

`--cassandra_replication_factor`: Num of replicas.
    (default: '3')
    (an integer)

### [perfkitbenchmarker.linux_packages.ch_block_storage ](../perfkitbenchmarker/linux_packages/ch_block_storage.py)

#### Description:

Contains cloudharmony block storage benchmark installation functions.

#### Flags:

`--ch_params`: A list of comma seperated "key=value" parameters passed into
    cloud harmony benchmarks.
    (default: '')
    (a comma separated list)

### [perfkitbenchmarker.linux_packages.cloud_tpu_models ](../perfkitbenchmarker/linux_packages/cloud_tpu_models.py)

#### Description:

Module containing cloud TPU models installation and cleanup functions.

#### Flags:

`--cloud_tpu_commit_hash`: git commit hash of desired cloud TPU models commit.
    (default: '0aecc4c539db2b753bec722a6e3dfc6f685959eb')

### [perfkitbenchmarker.linux_packages.cuda_toolkit ](../perfkitbenchmarker/linux_packages/cuda_toolkit.py)

#### Description:

Module containing CUDA toolkit installation and cleanup functions.

This module installs cuda toolkit from NVIDIA, configures gpu clock speeds
and autoboost settings, and exposes a method to collect gpu metadata. Currently
Tesla K80 and P100 gpus are supported, provided that there is only a single
type of gpu per system.


#### Flags:

`--cuda_toolkit_installation_dir`: installation directory to use for CUDA
    toolkit. If the toolkit is not installed, it will be installed here. If it
    is already installed, the installation at this path will be used.
    (default: '/usr/local/cuda')

`--cuda_toolkit_version`: <8.0|9.0|10.0|10.1>: Version of CUDA Toolkit to
    install
    (default: '9.0')

`--[no]gpu_autoboost_enabled`: whether gpu autoboost is enabled

### [perfkitbenchmarker.linux_packages.cudnn ](../perfkitbenchmarker/linux_packages/cudnn.py)

#### Description:

Module containing CUDA Deep Neural Network library installation functions.

#### Flags:

`--cudnn`: The NVIDIA CUDA Deep Neural Network library. Please put in data
    directory and specify the name

### [perfkitbenchmarker.linux_packages.gluster ](../perfkitbenchmarker/linux_packages/gluster.py)

#### Description:

Module containing GlusterFS installation and cleanup functions.

#### Flags:

`--gluster_replicas`: The number of Gluster replicas.
    (default: '3')
    (an integer)

`--gluster_stripes`: The number of Gluster stripes.
    (default: '1')
    (an integer)

### [perfkitbenchmarker.linux_packages.hadoop ](../perfkitbenchmarker/linux_packages/hadoop.py)

#### Description:

Module containing Hadoop installation and cleanup functions.

For documentation of commands to run at startup and shutdown, see:
http://hadoop.apache.org/docs/current/hadoop-project-dist/hadoop-common/ClusterSetup.html#Hadoop_Startup


#### Flags:

`--hadoop_version`: Version of hadoop.
    (default: '2.8.4')

### [perfkitbenchmarker.linux_packages.hbase ](../perfkitbenchmarker/linux_packages/hbase.py)

#### Description:

Module containing HBase installation and cleanup functions.

HBase is a scalable NoSQL database built on Hadoop.
https://hbase.apache.org/


#### Flags:

`--hbase_bin_url`: Specify to override url from HBASE_URL_BASE.

`--[no]hbase_use_stable`: Whether to use the current stable release of HBase.
    (default: 'false')

`--hbase_version`: HBase version.
    (default: '1.3.2.1')

### [perfkitbenchmarker.linux_packages.hpcc ](../perfkitbenchmarker/linux_packages/hpcc.py)

#### Description:

Module containing HPCC installation and cleanup functions.

The HPC Challenge is a collection of High Performance Computing benchmarks,
including High Performance Linpack (HPL). More information can be found here:
http://icl.cs.utk.edu/hpcc/


#### Flags:

`--hpcc_benchmarks`: A list of benchmarks in HPCC to run. If none are specified
    (the default), then all of the benchmarks are run. In 1.5.0, the benchmarks
    may include the following: HPL, Latency/Bandwidth, MPI RandomAccess, MPI
    RandomAccess LCG, MPIFFT, PTRANS, SingleDGEMM, SingleFFT,
    SingleRandomAccess, SingleRandomAccess LCG, SingleSTREAM, StarDGEMM,
    StarFFT, StarRandomAccess, StarRandomAccess LCG, StarSTREAM
    (default: '')
    (a comma separated list)

`--hpcc_math_library`: <openblas|mkl>: The math library to use when compiling
    hpcc: openblas or mkl. The default is openblas.
    (default: 'openblas')

### [perfkitbenchmarker.linux_packages.memcached_server ](../perfkitbenchmarker/linux_packages/memcached_server.py)

#### Description:

Module containing memcached server installation and cleanup functions.

#### Flags:

`--memcached_num_threads`: Number of worker threads.
    (default: '4')
    (an integer)

`--memcached_size_mb`: Size of memcached cache in megabytes.
    (default: '64')
    (an integer)

### [perfkitbenchmarker.linux_packages.memtier ](../perfkitbenchmarker/linux_packages/memtier.py)

#### Description:

Module containing memtier installation and cleanup functions.

#### Flags:

`--memtier_clients`: Comma separated list of number of clients per thread.
    Specify more than 1 value to vary the number of clients. Defaults to [50].
    (default: '50')
    (a comma separated list)

`--memtier_data_size`: Object data size. Defaults to 32 bytes.
    (default: '32')
    (an integer)

`--memtier_key_pattern`: Set:Get key pattern. G for Gaussian distribution, R for
    uniform Random, S for Sequential. Defaults to R:R.
    (default: 'R:R')

`--memtier_protocol`: <memcache_binary|redis|memcache_text>: Protocol to use.
    Supported protocols are redis, memcache_text, and memcache_binary. Defaults
    to memcache_binary.
    (default: 'memcache_binary')

`--memtier_ratio`: Set:Get ratio. Defaults to 9x Get versus Sets (9 Gets to 1
    Set in 10 total requests).
    (default: '9')
    (an integer)

`--memtier_requests`: Number of total requests per client. Defaults to 10000.
    (default: '10000')
    (an integer)

`--memtier_run_count`: Number of full-test iterations to perform. Defaults to 1.
    (default: '1')
    (an integer)

`--memtier_threads`: Number of threads. Defaults to 4.
    (default: '4')
    (an integer)

### [perfkitbenchmarker.linux_packages.mxnet ](../perfkitbenchmarker/linux_packages/mxnet.py)

#### Description:

Module containing MXNet installation and cleanup functions.

#### Flags:

`--mx_version`: mxnet pip package version
    (default: '1.4.0')

### [perfkitbenchmarker.linux_packages.mxnet_cnn ](../perfkitbenchmarker/linux_packages/mxnet_cnn.py)

#### Description:

Module containing MXNet CNN installation and cleanup functions.

#### Flags:

`--mxnet_commit_hash`: git commit hash of desired mxnet commit.
    (default: '2700ddbbeef212879802f7f0c0812192ec5c2b77')

### [perfkitbenchmarker.linux_packages.netperf ](../perfkitbenchmarker/linux_packages/netperf.py)

#### Description:

Module containing netperf installation and cleanup functions.

#### Flags:

`--netperf_histogram_buckets`: The number of buckets per bucket array in a
    netperf histogram. Netperf keeps one array for latencies in the single usec
    range, one for the 10-usec range, one for the 100-usec range, and so on
    until the 10-sec range. The default value that netperf uses is 100. Using
    more will increase the precision of the histogram samples that the netperf
    benchmark produces.
    (default: '100')
    (an integer)

### [perfkitbenchmarker.linux_packages.openjdk ](../perfkitbenchmarker/linux_packages/openjdk.py)

#### Description:

Module containing OpenJDK installation and cleanup functions.

#### Flags:

`--openjdk_version`: Version of openjdk to use. By default, the version of
    openjdk is automatically detected.

### [perfkitbenchmarker.linux_packages.openmpi ](../perfkitbenchmarker/linux_packages/openmpi.py)

#### Description:

Module containing OpenMPI installation and cleanup functions.

#### Flags:

`--[no]openmpi_enable_shared`: Whether openmpi should build shared libraries in
    addition to static ones.
    (default: 'false')

### [perfkitbenchmarker.linux_packages.redis_server ](../perfkitbenchmarker/linux_packages/redis_server.py)

#### Description:

Module containing redis installation and cleanup functions.

#### Flags:

`--[no]redis_enable_aof`: Enable append-only file (AOF) with appendfsync always.
    (default: 'false')

`--redis_server_version`: Version of redis server to use.
    (default: '2.8.9')

`--redis_total_num_processes`: Total number of redis server processes.
    (default: '1')
    (a positive integer)

### [perfkitbenchmarker.linux_packages.speccpu ](../perfkitbenchmarker/linux_packages/speccpu.py)

#### Description:

Module to install, uninstall, and parse results for SPEC CPU 2006 and 2017.


#### Flags:

`--runspec_build_tool_version`: Version of gcc/g++/gfortran. This should match
    runspec_config. Note, if neither runspec_config and
    runspec_build_tool_version is set, the test install gcc/g++/gfortran-4.7,
    since that matches default config version. If runspec_config is set, but not
    runspec_build_tool_version, default version of build tools will be
    installed. Also this flag only works with debian.

`--runspec_config`: Used by the PKB speccpu benchmarks. Name of the cfg file to
    use as the SPEC CPU config file provided to the runspec binary via its
    --config flag. If the benchmark is run using an .iso file, then the cfg file
    must be placed in the local PKB data directory and will be copied to the
    remote machine prior to executing runspec/runcpu. Defaults to None. See
    README.md for instructions if running with a repackaged .tgz file.

`--runspec_define`: Used by the PKB speccpu benchmarks. Optional comma-separated
    list of SYMBOL[=VALUE] preprocessor macros provided to the runspec binary
    via repeated --define flags. Example: numa,smt,sse=SSE4.2
    (default: '')

`--[no]runspec_enable_32bit`: Used by the PKB speccpu benchmarks. If set,
    multilib packages will be installed on the remote machine to enable use of
    32-bit SPEC CPU binaries. This may be useful when running on memory-
    constrained instance types (i.e. less than 2 GiB memory/core), where 64-bit
    execution may be problematic.
    (default: 'false')

`--[no]runspec_estimate_spec`: Used by the PKB speccpu benchmarks. If set, the
    benchmark will report an estimated aggregate score even if SPEC CPU did not
    compute one. This usually occurs when --runspec_iterations is less than 3.
    --runspec_keep_partial_results is also required to be set. Samples will
    becreated as estimated_SPECint(R)_rate_base and
    estimated_SPECfp(R)_rate_base.  Available results will be saved, and PKB
    samples will be marked with a metadata value of partial=true. If unset,
    SPECint(R)_rate_base20** and SPECfp(R)_rate_base20** are listed in the
    metadata under missing_results.
    (default: 'false')

`--runspec_iterations`: Used by the PKB speccpu benchmarks. The number of
    benchmark iterations to execute, provided to the runspec binary via its
    --iterations flag.
    (default: '3')
    (an integer)

`--[no]runspec_keep_partial_results`: Used by the PKB speccpu benchmarks. If
    set, the benchmark will report an aggregate score even if some of the SPEC
    CPU component tests failed with status "NR". Available results will be
    saved, and PKB samples will be marked with a metadata value of partial=true.
    If unset, partial failures are treated as errors.
    (default: 'false')

`--spec_runmode`: <base|peak|all>: Run mode to use. Defaults to base.
    (default: 'base')

### [perfkitbenchmarker.linux_packages.tensorflow ](../perfkitbenchmarker/linux_packages/tensorflow.py)

#### Description:

Module containing TensorFlow installation and cleanup functions.

#### Flags:

`--t2t_pip_package`: Tensor2Tensor pip package to install. By default, PKB will
    install tensor2tensor==1.7 .
    (default: 'tensor2tensor==1.7')

`--tf_cnn_benchmarks_branch`: TensorFlow CNN branchmarks branch that is
    compatible with A TensorFlow version.
    (default: 'cnn_tf_v1.12_compatible')

`--tf_cpu_pip_package`: TensorFlow CPU pip package to install. By default, PKB
    will install an Intel-optimized CPU build when using CPUs.
    (default: 'https://anaconda.org/intel/tensorflow/1.12.0/download/tensorflow-
    1.12.0-cp27-cp27mu-linux_x86_64.whl')

`--tf_gpu_pip_package`: TensorFlow GPU pip package to install. By default, PKB
    will install tensorflow-gpu==1.12 when using GPUs.
    (default: 'tensorflow-gpu==1.12.0')

### [perfkitbenchmarker.linux_packages.tensorflow_models ](../perfkitbenchmarker/linux_packages/tensorflow_models.py)

#### Description:

Module containing TensorFlow models installation and cleanup functions.

#### Flags:

`--tensorflow_models_commit_hash`: git commit hash of desired TensorFlow models
    commit.
    (default: '57e075203f8fba8d85e6b74f17f63d0a07da233a')

### [perfkitbenchmarker.linux_packages.tensorflow_serving ](../perfkitbenchmarker/linux_packages/tensorflow_serving.py)

#### Description:

Module containing TensorFlow Serving installation functions.



#### Flags:

`--tf_serving_branch`: GitHub branch to pull from
    (default: 'master')

### [perfkitbenchmarker.linux_packages.tomcat ](../perfkitbenchmarker/linux_packages/tomcat.py)

#### Description:

Module containing Apache Tomcat installation and cleanup functions.

Installing Tomcat via this module makes some changes to the default settings:

  * Http11Nio2Protocol is used (non-blocking).
  * Request logging is disabled.
  * The session timeout is decreased to 1 minute.

https://tomcat.apache.org/


#### Flags:

`--tomcat_url`: Tomcat 8 download URL.
    (default: 'https://archive.apache.org/dist/tomcat/tomcat-8/v8.0.28/bin
    /apache-tomcat-8.0.28.tar.gz')

### [perfkitbenchmarker.linux_packages.ycsb ](../perfkitbenchmarker/linux_packages/ycsb.py)

#### Description:

Install, execute, and parse results from YCSB.

YCSB (the Yahoo! Cloud Serving Benchmark) is a common method of comparing NoSQL
database performance.
https://github.com/brianfrankcooper/YCSB

For PerfKitBenchmarker, we wrap YCSB to:

  * Pre-load a database with a fixed number of records.
  * Execute a collection of workloads under a staircase load.
  * Parse the results into PerfKitBenchmarker samples.

The 'YCSBExecutor' class handles executing YCSB on a collection of client VMs.
Generally, clients just need this class. For example, to run against
HBase 1.0:

  >>> executor = ycsb.YCSBExecutor('hbase-10')
  >>> samples = executor.LoadAndRun(loader_vms)

By default, this runs YCSB workloads A and B against the database, 32 threads
per client VM, with an initial database size of 1GB (1k records).
Each workload runs for at most 30 minutes.


#### Flags:

`--ycsb_client_vms`: Number of YCSB client VMs.
    (default: '1')
    (an integer)

`--ycsb_field_count`: Number of fields in a record. Defaults to None which uses
    the ycsb default of 10.
    (an integer)

`--ycsb_field_length`: Size of each field. Defaults to None which uses the ycsb
    default of 100.
    (an integer)

`--[no]ycsb_histogram`: Include individual histogram results from YCSB (will
    increase sample count).
    (default: 'false')

`--[no]ycsb_include_individual_results`: Include results from each client VM,
    rather than just combined results.
    (default: 'false')

`--ycsb_load_parameters`: Passed to YCSB during the load stage. Comma-separated
    list of "key=value" pairs.
    (default: '')
    (a comma separated list)

`--[no]ycsb_load_samples`: Include samples from pre-populating database.
    (default: 'true')

`--ycsb_measurement_interval`: <op|intended|both>: Measurement interval to use
    for ycsb. Defaults to op.
    (default: 'op')

`--ycsb_measurement_type`: <histogram|hdrhistogram|timeseries>: Measurement type
    to use for ycsb. Defaults to histogram.
    (default: 'histogram')

`--ycsb_operation_count`: Number of operations *per client VM*.
    (an integer)

`--ycsb_preload_threads`: Number of threads per loader during the initial data
    population stage. Default value depends on the target DB.
    (an integer)

`--ycsb_readproportion`: The read proportion, Default is 0.5 in workloada and
    0.95 in YCSB.
    (a number)

`--ycsb_record_count`: Pre-load with a total dataset of records total. Overrides
    recordcount value in all workloads of this run. Defaults to None, where
    recordcount value in each workload is used. If neither is not set, ycsb
    default of 0 is used.
    (an integer)

`--[no]ycsb_reload_database`: Reload database, othewise skip load stage. Note,
    this flag is only used if the database is already loaded.
    (default: 'true')

`--ycsb_requestdistribution`: <uniform|zipfian|latest>: Type of request
    distribution.  This will overwrite workload file parameter

`--ycsb_run_parameters`: Passed to YCSB during the load stage. Comma-separated
    list of "key=value" pairs.
    (default: '')
    (a comma separated list)

`--ycsb_scanproportion`: The scan proportion, Default is 0 in workloada and 0 in
    YCSB.
    (a number)

`--ycsb_threads_per_client`: Number of threads per loader during the benchmark
    run. Specify a list to vary the number of clients.
    (default: '32')
    (a comma separated list)

`--ycsb_timelimit`: Maximum amount of time to run each workload / client count
    combination. Set to 0 for unlimited time.
    (default: '1800')
    (an integer)

`--ycsb_updateproportion`: The update proportion, Default is 0.5 in workloada
    and 0.05 in YCSB.
    (a number)

`--ycsb_version`: YCSB version to use. Defaults to version 0.9.0.
    (default: '0.9.0')

`--ycsb_workload_files`: Path to YCSB workload file to use during *run* stage
    only. Comma-separated list
    (default: 'workloada,workloadb')
    (a comma separated list)

