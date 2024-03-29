#!/usr/bin/env python
from gpupeasy.core.server import GPUPeasyServer


if __name__ == '__main__':
    ## Configuration
    gpuList = [
        '0', '1', '2', '3', '4', '5', '6', '7',
    ]
    debug = True
    host = '0.0.0.0'
    port = '8844'
    logdir = '/tmp/gpupeasy/'
    ## End configuration
    gpu = GPUPeasyServer(gpuList, debug=debug, logdir=logdir)
    gpu.run(host=host, port=port)
