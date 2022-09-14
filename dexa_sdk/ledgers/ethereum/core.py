import asyncio
import typing

from aries_cloudagent.config.injection_context import InjectionContext
from eth_account.signers.local import LocalAccount
from loguru import logger
from web3 import Account, Web3
from web3._utils.encoding import to_json
from web3.contract import Contract
from web3.exceptions import ContractLogicError


class EthereumClient:
    """Ethereum blockchain client"""

    def __init__(self, context: InjectionContext) -> None:
        """Initialise ethreum blockchain client"""

        # Injection context
        self._context = context

        # Logger
        self._logger = logger

        # Eth node rpc endpoint
        self._eth_node_rpc = self._context.settings.get("dexa.eth_node_rpc")

        # Eth private key of the controller
        self._org_eth_private_key = self._context.settings.get(
            "dexa.org_eth_private_key"
        )

        # Set organisation account for ethereum client
        self._org_eth_account = Account.from_key(self._org_eth_private_key)

        # Eth private key of the intermediary
        self._intermediary_eth_private_key = self._context.settings.get(
            "dexa.intermediary_eth_private_key"
        )

        # Set intermediary account for ethereum client
        self._intermediary_eth_account = Account.from_key(
            self._intermediary_eth_private_key
        )

        # Ethereum client
        self._client = Web3(Web3.HTTPProvider(self._eth_node_rpc))

        # Contract ABI
        self._contract_abi = self._context.settings.get("dexa.contract_abi")

        # Contract address
        self._contract_address = self._context.settings.get("dexa.contract_address")

        # Contract interface
        self._contract: Contract = self._client.eth.contract(
            address=self._contract_address, abi=self._contract_abi
        )

    @property
    def context(self) -> InjectionContext:
        """Accessor for injection context.

        Returns:
            InjectionContext: Injection context
        """
        return self._context

    @property
    def logger(self):
        """Accessor for logger.

        Returns:
            Logger: Logger
        """
        return self._logger

    @property
    def client(self) -> Web3:
        """Returns the client for interacting with ethereum blockchain node.

        Returns:
            Web3: Ethereum blockchain client
        """
        return self._client

    @property
    def org_account(self) -> LocalAccount:
        """Accessor for ethereum account for organisation.

        Returns:
            LocalAccount: account
        """
        return self._org_eth_account

    @property
    def org_private_key(self) -> str:
        """Accessor for organisation private key.

        Returns:
            str: private key
        """
        return self._org_eth_private_key

    @property
    def intermediary_account(self) -> LocalAccount:
        """Accessor for ethereum account for intermediary.

        Returns:
            LocalAccount: account
        """
        return self._intermediary_eth_account

    @property
    def intermediary_private_key(self) -> str:
        """Accessor for intermediary private key.

        Returns:
            str: private key
        """
        return self._intermediary_eth_private_key

    @property
    def contract_abi(self) -> str:
        """Accessor for dexa contract abi.

        Returns:
            str: smart contract abi
        """
        return self._contract_abi

    @property
    def contract_address(self) -> str:
        """Accessor for dexa contract address.

        Returns:
            str: smart contract address
        """
        return self._contract_address

    @property
    def contract(self) -> Contract:
        """Accessor for dexa contract interface.

        Returns:
            Contract: smart contract
        """
        return self._contract

    async def emit_da_did(self, did: str) -> typing.Tuple[typing.Any, typing.Any]:
        """Emit did:mydata identifier in the blockchain logs"""
        org_account = self.org_account
        org_balance = self.client.eth.get_balance(org_account.address)

        self.logger.info(f"Organisation account address: {org_account.address}")
        self.logger.info(f"Organisation account balance: {org_balance}")

        try:
            contract = self.contract
            contract_function = contract.functions.emitDADID(did)
            contract_function_txn = contract_function.buildTransaction(
                {
                    "from": org_account.address,
                    "nonce": self.client.eth.get_transaction_count(org_account.address),
                    "maxFeePerGas": 2000000000,
                    "maxPriorityFeePerGas": 1000000000,
                }
            )

            tx_create = self.client.eth.account.sign_transaction(
                contract_function_txn, org_account.privateKey
            )

            tx_hash = self.client.eth.send_raw_transaction(tx_create.rawTransaction)

            # Suspend execution and let other task run.
            await asyncio.sleep(1)

            tx_receipt = self.client.eth.wait_for_transaction_receipt(tx_hash)

            if tx_receipt.get("status") == 1:
                self.logger.info(f"Status (emitDADID): Succesfully emitted {did}")
            else:
                self.logger.info("Status (emitDADID): Failed to emit {did}")

            return (tx_hash, tx_receipt)
        except ContractLogicError as err:
            self.logger.info(f"Status (emitDADID): {err}")

    async def emit_dda_did(self, did: str) -> typing.Tuple[typing.Any, typing.Any]:
        """Emit did:mydata identifier in the blockchain logs"""
        org_account = self.org_account
        org_balance = self.client.eth.get_balance(org_account.address)

        self.logger.info(f"Organisation account address: {org_account.address}")
        self.logger.info(f"Organisation account balance: {org_balance}")

        try:
            contract = self.contract
            contract_function = contract.functions.emitDDADID(did)
            contract_function_txn = contract_function.buildTransaction(
                {
                    "from": org_account.address,
                    "nonce": self.client.eth.get_transaction_count(org_account.address),
                    "maxFeePerGas": 2000000000,
                    "maxPriorityFeePerGas": 1000000000,
                }
            )

            tx_create = self.client.eth.account.sign_transaction(
                contract_function_txn, org_account.privateKey
            )

            tx_hash = self.client.eth.send_raw_transaction(tx_create.rawTransaction)

            # Suspend execution and let other task run.
            await asyncio.sleep(1)

            tx_receipt = self.client.eth.wait_for_transaction_receipt(tx_hash)

            if tx_receipt.get("status") == 1:
                self.logger.info(f"Status (emitDDADID): Succesfully emitted {did}")
            else:
                self.logger.info("Status (emitDDADID): Failed to emit {did}")

            return (tx_hash, tx_receipt)
        except ContractLogicError as err:
            self.logger.info(f"Status (emitDDADID): {err}")

    async def add_organisation(self) -> None:
        """Add organisation to the whitelist"""
        org_account = self.org_account
        org_balance = self.client.eth.get_balance(org_account.address)

        self.logger.info(f"Organisation account address: {org_account.address}")
        self.logger.info(f"Organisation account balance: {org_balance}")

        intermediary_account = self.intermediary_account
        intermediary_balance = self.client.eth.get_balance(intermediary_account.address)

        self.logger.info(
            f"Intermediary account address: {intermediary_account.address}"
        )
        self.logger.info(f"Intermediary account balance: {intermediary_balance}")
        self.logger.info(
            f"Transaction count: \
                {self.client.eth.get_transaction_count(intermediary_account.address)}"
        )

        try:
            contract = self.contract
            contract_function = contract.functions.addOrganisation(org_account.address)
            contract_function_txn = contract_function.buildTransaction(
                {
                    "from": intermediary_account.address,
                    "nonce": self.client.eth.get_transaction_count(
                        intermediary_account.address
                    ),
                    "maxFeePerGas": 2000000000,
                    "maxPriorityFeePerGas": 1000000000,
                }
            )

            tx_create = self.client.eth.account.sign_transaction(
                contract_function_txn, intermediary_account.privateKey
            )

            tx_hash = self.client.eth.send_raw_transaction(tx_create.rawTransaction)

            self.logger.info(f"Transaction hash (addOrganisation): {tx_hash.hex()}")

            tx_receipt = self.client.eth.wait_for_transaction_receipt(tx_hash)

            self.logger.info(
                f"Transaction receipt (addOrganisation): {to_json(tx_receipt)}"
            )

            if tx_receipt.get("status") == 1:
                self.logger.info(
                    "Status (addOrganisation): Added organisation to whitelist."
                )
            else:
                self.logger.info(
                    "Status (addOrganisation): Organisation is already present in whitelist."
                )
        except ContractLogicError as err:
            self.logger.info(f"Status (addOrganisation): {err}")
