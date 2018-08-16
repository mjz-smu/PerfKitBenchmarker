# Copyright 2014 PerfKitBenchmarker Authors. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Runs ping.

This benchmark runs ping using the internal, and optionally external, ips of
vms in the same zone.
"""

import logging
from perfkitbenchmarker import vm_util
from perfkitbenchmarker import configs
from perfkitbenchmarker import flags
from perfkitbenchmarker import sample
import re


# flags.DEFINE_boolean('ping_also_run_using_external_ip', False,
#                      'If set to True, the ping command will also be executed '
#                      'using the external ips of the vms.')

flags.DEFINE_integer('desired_throughput_mbit', 1000,
                     'The desired throughput to test for '
                     'in Mbits/sec',
                     lower_bound=1)

flags.DEFINE_integer('desired_throughput_max_iterations', 3,
                     'The maximum number of iterations '
                     'used of different window sizes to '
                     'try and achieve the desired throughput',
                     lower_bound = 1, upper_bound = 10)

#TODO change these flags to be specific to this benchmark
#also uses flags
#FLAGS.iperf_sending_thread_count
#FLAGS.iperf_runtime_in_seconds

FLAGS = flags.FLAGS


BENCHMARK_NAME = 'defined_throughput'
BENCHMARK_CONFIG = """
defined_throughput:
  description: Run iperf
  vm_groups:
    vm_1:
      vm_spec: *default_single_core
    vm_2:
      vm_spec: *default_single_core
"""

METRICS = ('Min Latency', 'Average Latency', 'Max Latency', 'Latency Std Dev')
IPERF_PORT = 20000
IPERF_RETRIES = 5

def GetConfig(user_config):
  return configs.LoadConfig(BENCHMARK_CONFIG, user_config, BENCHMARK_NAME)


def Prepare(benchmark_spec):  # pylint: disable=unused-argument
  """Install ping on the target vm.
  Checks that there are exactly two vms specified.
  Args:
    benchmark_spec: The benchmark specification. Contains all data that is
        required to run the benchmark.
  """
  if len(benchmark_spec.vms) != 2:
    raise ValueError(
        'Ping benchmark requires exactly two machines, found {0}'
        .format(len(benchmark_spec.vms)))
  
  # vms = benchmark_spec.vms
  # for vm in vms:
  #   vm.AllowIcmp()

  vms = benchmark_spec.vms
  if len(vms) != 2:
    raise ValueError(
        'iperf benchmark requires exactly two machines, found {0}'.format(len(
            vms)))

  for vm in vms:
    vm.AllowIcmp()
    vm.Install('iperf')
    if vm_util.ShouldRunOnExternalIpAddress():
      vm.AllowPort(IPERF_PORT)
    stdout, _ = vm.RemoteCommand(('nohup iperf --server --port %s &> /dev/null'
                                  '& echo $!') % IPERF_PORT)
    # TODO store this in a better place once we have a better place
    vm.iperf_server_pid = stdout.strip()


def Run(benchmark_spec):
  """Run ping on the target vm.

  Args:
    benchmark_spec: The benchmark specification. Contains all data that is
        required to run the benchmark.

  Returns:
    A list of sample.Sample objects.
  """
  vms = benchmark_spec.vms
  ping_results = []
  ping_results_external = []
  for sending_vm, receiving_vm in vms, reversed(vms):
    ping_results = ping_results + _RunPing(sending_vm,
                                 receiving_vm,
                                 receiving_vm.internal_ip,
                                 'internal')
  #if FLAGS.ping_also_run_using_external_ip:
  for sending_vm, receiving_vm in vms, reversed(vms):
    ping_results_external = ping_results_external + _RunPing(sending_vm,
                                 receiving_vm,
                                 receiving_vm.ip_address,
                                 'external')

  # logging.info(type(ping_results))
  # logging.info(ping_results)
  # logging.info(ping_results[1])
  # logging.info(ping_results[5])
  # logging.info(ping_results[1].value)

  average_latency = float(ping_results[1].value * 0.001)

  average_latency_external = float(ping_results_external[1].value * 0.001)

  pipe_size = float(FLAGS.desired_throughput_mbit)

  logging.info("avg Latency in seconds: %s", str(average_latency))
  logging.info("pipe_size in mbits: %s", str(pipe_size))

  #window_size(Mbytes) = pipe_size(Mbits/sec) * average_latency(sec)
  window_size = pipe_size * (average_latency) * 0.125

  window_size_external = pipe_size * (average_latency_external) * 0.125

  logging.info(window_size)
  logging.info(window_size_external)

  results=[]
  logging.info('Iperf Results:')
  # Send traffic in both directions
  for sending_vm, receiving_vm in vms, reversed(vms):
    # Send using external IP addresses
    if vm_util.ShouldRunOnExternalIpAddress():
      results.append(_RunIperf(sending_vm,
                               receiving_vm,
                               receiving_vm.ip_address,
                               'external',
                               window_size_external))
    # Send using internal IP addresses
    if vm_util.ShouldRunOnInternalIpAddress(sending_vm,
                                            receiving_vm):
      results.append(_RunIperf(sending_vm,
                               receiving_vm,
                               receiving_vm.internal_ip,
                               'internal',
                               window_size))

  return results

@vm_util.Retry(max_retries=IPERF_RETRIES)
def _RunIperf(sending_vm, receiving_vm, receiving_ip_address, ip_type, window_size):
  """Run iperf using sending 'vm' to connect to 'ip_address'.

  Args:
    sending_vm: The VM sending traffic.
    receiving_vm: The VM receiving traffic.
    receiving_ip_address: The IP address of the iperf server (ie the receiver).
    ip_type: The IP type of 'ip_address' (e.g. 'internal', 'external')
  Returns:
    A Sample.
  """
  use_larger_tcp_window = False

  if window_size > 0.08:
    use_larger_tcp_window = True

  formatted_window_size = str(window_size) + "MB"

  iperf_cmd = ('iperf --client %s --port %s --format m --time %s -P %s' %
               (receiving_ip_address, IPERF_PORT,
                FLAGS.iperf_runtime_in_seconds,
                FLAGS.iperf_sending_thread_count))

  if use_larger_tcp_window == True:
    iperf_cmd = ('iperf --client %s --port %s --format m --time %s -P %s -w %s' %
               (receiving_ip_address, IPERF_PORT,
                FLAGS.iperf_runtime_in_seconds,
                FLAGS.iperf_sending_thread_count,
                formatted_window_size))
  # the additional time on top of the iperf runtime is to account for the
  # time it takes for the iperf process to start and exit
  timeout_buffer = FLAGS.iperf_timeout or 30 + FLAGS.iperf_sending_thread_count
  stdout, _ = sending_vm.RemoteCommand(iperf_cmd, should_log=True,
                                       timeout=FLAGS.iperf_runtime_in_seconds +
                                       timeout_buffer)

  # Example output from iperf that needs to be parsed
  # STDOUT: ------------------------------------------------------------
  # Client connecting to 10.237.229.201, TCP port 5001
  # TCP window size: 0.04 MByte (default)
  # ------------------------------------------------------------
  # [  6] local 10.76.234.115 port 53527 connected with 10.237.229.201 port 5001
  # [  3] local 10.76.234.115 port 53524 connected with 10.237.229.201 port 5001
  # [  4] local 10.76.234.115 port 53525 connected with 10.237.229.201 port 5001
  # [  5] local 10.76.234.115 port 53526 connected with 10.237.229.201 port 5001
  # [ ID] Interval       Transfer     Bandwidth
  # [  4]  0.0-60.0 sec  3730 MBytes  521.1 Mbits/sec
  # [  5]  0.0-60.0 sec  3499 MBytes   489 Mbits/sec
  # [  6]  0.0-60.0 sec  3044 MBytes   425 Mbits/sec
  # [  3]  0.0-60.0 sec  3738 MBytes   522 Mbits/sec
  # [SUM]  0.0-60.0 sec  14010 MBytes  1957 Mbits/sec

  stdout2 = stdout
  match = re.search('TCP window size: (.*) MByte ', stdout)
  if match:
    actual_window_size = match.group(1)
    actual_window_size = float(actual_window_size)
  else:
    match = re.search('TCP window size: .* MByte ', stdout)
    if match:
      actual_window_size = match.group(1)
      actual_window_size = float(actual_window_size)
    else:
      actual_window_size = 0

  if FLAGS.iperf_tcp_window:
    match = re.search('WARNING: requested (.*) MByte', stdout)
    if match:
      requested_window_size = match.group(1)
      requested_window_size = float(requested_window_size)
    else:
      requested_window_size = actual_window_size
  else:
    requested_window_size = 0
  

  thread_values = re.findall(r'\[SUM].*\s+(\d+\.?\d*).Mbits/sec', stdout)
  if not thread_values:
    # If there is no sum you have try and figure out an estimate
    # which happens when threads start at different times.  The code
    # below will tend to overestimate a bit.
    thread_values = re.findall('\[.*\d+\].*\s+(\d+\.?\d*).Mbits/sec', stdout)

    if len(thread_values) != FLAGS.iperf_sending_thread_count:
      raise ValueError('Only %s out of %s iperf threads reported a'
                       ' throughput value.' %
                       (len(thread_values), FLAGS.iperf_sending_thread_count))
  total_throughput = 0.0
  for value in thread_values:
    total_throughput += float(value)


  #TODO add logic to run tests again if didn't meet desired throughput

  metadata = {
      # The meta data defining the environment
      'receiving_machine_type': receiving_vm.machine_type,
      'receiving_zone': receiving_vm.zone,
      'sending_machine_type': sending_vm.machine_type,
      'sending_thread_count': FLAGS.iperf_sending_thread_count,
      'sending_zone': sending_vm.zone,
      'runtime_in_seconds': FLAGS.iperf_runtime_in_seconds,
      'ip_type': ip_type,
      'tcp_window_size_requested_mb': requested_window_size,
      'tcp_window_size_actual_mb': actual_window_size
  }
  return sample.Sample('Throughput', total_throughput, 'Mbits/sec', metadata)

def _RunPing(sending_vm, receiving_vm, receiving_ip, ip_type):
  """Run ping using 'sending_vm' to connect to 'receiving_ip'.

  Args:
    sending_vm: The VM issuing the ping request.
    receiving_vm: The VM receiving the ping.  Needed for metadata.
    receiving_ip: The IP address to be pinged.
    ip_type: The type of 'receiving_ip' (either 'internal' or 'external')
  Returns:
    A list of samples, with one sample for each metric.
  """
  if not sending_vm.IsReachable(receiving_vm):
    logging.warn('%s is not reachable from %s', receiving_vm, sending_vm)
    return []

  logging.info('Ping results (ip_type = %s):', ip_type)
  ping_cmd = 'ping -c 100 %s' % receiving_ip
  stdout, _ = sending_vm.RemoteCommand(ping_cmd, should_log=True)
  stats = re.findall('([0-9]*\\.[0-9]*)', stdout.splitlines()[-1])
  assert len(stats) == len(METRICS), stats
  results = []
  metadata = {'ip_type': ip_type,
              'receiving_zone': receiving_vm.zone,
              'sending_zone': sending_vm.zone}
  for i, metric in enumerate(METRICS):
    results.append(sample.Sample(metric, float(stats[i]), 'ms', metadata))
  return results


def Cleanup(benchmark_spec):  # pylint: disable=unused-argument
  """Cleanup ping on the target vm (by uninstalling).

  Args:
    benchmark_spec: The benchmark specification. Contains all data that is
        required to run the benchmark.
  """
  pass
