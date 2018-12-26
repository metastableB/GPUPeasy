from gpupeasy.core.server import GPUPeasyServer


if __name__ == '__main__':
    ## Configuration
    gpuList = ['0', '1', '2']
    debug = True
    host = '0.0.0.0'
    port = '8888'
    logdir = '/var/gpupeasy/'
    ## End configuration
    gpu = GPUPeasyServer(gpuList, debug=debug, logdir=logdir)
    gpu.run(host=host, port=port)
