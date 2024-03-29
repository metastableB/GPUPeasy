#!/usr/bin/env python
from gpupeasy.webapp.peasyWebGUI import GPUPeasyWebGUI

if __name__ == "__main__":
    ## Configuration
    backendHost = '0.0.0.0'
    backendPort = '8844'
    guiHost = '0.0.0.0'
    guiPort = '4005'
    debug = True
    ## End Configuration

    frontend = GPUPeasyWebGUI(backendHost, backendPort, debug=debug)
    frontend.run(host=guiHost, port=guiPort)
