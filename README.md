<h1 align="center">
    Data Exchange Agreements (DEXA) SDKs
</h1>

<p align="center">
    <a href="/../../commits/" title="Last Commit"><img src="https://img.shields.io/github/last-commit/decentralised-dataexchange/dexa-sdk?style=flat"></a>
    <a href="/../../issues" title="Open Issues"><img src="https://img.shields.io/github/issues/decentralised-dataexchange/dexa-sdk?style=flat"></a>
    <a href="./LICENSE" title="License"><img src="https://img.shields.io/badge/License-Apache%202.0-green.svg?style=flat"></a>
</p>

<p align="center">
  <a href="#about">About</a> •
  <a href="#release-status">Release Status</a> •
  <a href="#contributing">Contributing</a> •
  <a href="#licensing">Licensing</a>
</p>

## About

This repository hosts the source code for DEXA SDKs and is part of the deliverables for Provenance services with smart data agreement ([PS-SDA](https://ontochain.ngi.eu/content/ps-sda)) project that has received funding from the European Union’s Horizon 2020 research and innovation programme under grant agreement No 957338. It implements common functions for DEXA that is used to implement dexa-protocols. 
## Release Status

Not released, work in progress.

## Installation

Requirements:
- Python 3.8.9 or higher

### Plugin Installation

Install this plugin into the virtual environment:

```sh
$ pip install dexa-sdk
```

### Usage

Hyperledger aries agents with DEXA protocols enabled can be created using DEXA SDK. Sample script is given below:

In `agent.py`, copy the following.

```python
from dexa_sdk.agent.commands.start import execute

args = [
    "-it",
    "http",
    "0.0.0.0",
    "8006",
    "-ot",
    "http",
    "-e",
    "http://localhost:8006/",
    "--label",
    "Data Source",
    "--admin",
    "0.0.0.0",
    "8005",
    "--admin-insecure-mode",
    "--auto-accept-requests",
    "--auto-ping-connection",
    "--auto-respond-credential-proposal",
    "--auto-respond-credential-offer",
    "--auto-respond-credential-request",
    "--auto-store-credential",
    "--auto-respond-presentation-proposal",
    "--auto-respond-presentation-request",
    "--auto-verify-presentation",
    "--genesis-url",
    "https://indy.igrant.io/genesis",
    "--wallet-type",
    "indy",
    "--wallet-name",
    "Data Source",
    "--log-level",
    "info",
    "--wallet-key",
    "Data Source",
    "--webhook-url",
    "http://localhost:8005/webhooks",
    "--public-invites",
    "--plugin",
    "mydata_did",
    "--plugin",
    "dexa_protocol",
    "--eth-node-rpc",
    "<ethereum node rpc endpoint>",
    "--intermediary-eth-private-key",
    "<data intermediary ethereum private key>",
    "--org-eth-private-key",
    "<org ethereum private key>",
    "--contract-address",
    "<contract address>"
]

execute(args)
```

and run by executing `python agent.py`.

#### Using docker

```sh
docker run -it igrantio/dexa-sdk:0.1.8 -- -it http 0.0.0.0 8006 -ot http -e http://localhost:8006/ --label Data Source --admin 0.0.0.0 8005 --admin-insecure-mode --auto-accept-requests --auto-ping-connection --auto-respond-credential-proposal --auto-respond-credential-offer --auto-respond-credential-request --auto-store-credential --auto-respond-presentation-proposal --auto-respond-presentation-request --auto-verify-presentation --genesis-url https://indy.igrant.io/genesis --wallet-type indy --wallet-name Data Source --log-level info --wallet-key Data Source --webhook-url http://localhost:8005/webhooks --public-invites --plugin mydata_did --plugin dexa_protocol --eth-node-rpc <ethereum node rpc endpoint> --intermediary-eth-private-key <data intermediary ethereum private key>  --org-eth-private-key <org ethereum private key> --contract-address <contract address>
```

## Contributing

Feel free to improve the plugin and send us a pull request. If you found any problems, please create an issue in this repo.

## Licensing
Copyright (c) 2022-25 LCubed AB (iGrant.io), Sweden

Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License.

You may obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0.

Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the LICENSE for the specific language governing permissions and limitations under the License.
