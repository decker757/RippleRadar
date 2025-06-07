from xrpl.clients import JsonRpcClient
from xrpl.models.requests.account_info import AccountInfo
from xrpl.models.transactions import TrustSet
from xrpl.models.amounts import IssuedCurrencyAmount
from xrpl.transaction import autofill_and_sign
from xrpl.transaction import submit_and_wait
from xrpl.models.requests import AccountLines
from xrpl.models.requests import AccountTx


import json
import xrpl



JSON_RPC_URL = "https://s.altnet.rippletest.net:51234/"
client = JsonRpcClient(JSON_RPC_URL)

#Account Info
def get_account_info(address):
    acc_info = AccountInfo(
        account=address,
        ledger_index="validated",
        strict=True,
    )
    response = client.request(acc_info)
    account_data = response.result["account_data"]
    
    return account_data

#Get Account Balance in XRP
def get_balance(address):
    return float(get_account_info(address)["Balance"])/1000000

class Transaction:
    @staticmethod
    def prepare_transaction(value, from_account, to_account):
        return xrpl.models.transactions.Payment(
            account=from_account,
            amount=xrpl.utils.xrp_to_drops(value),
            destination=to_account,
        )

    @staticmethod
    def sign_transaction(payment, wallet, client):
        signed_tx = xrpl.transaction.autofill_and_sign(payment, client, wallet)
        max_ledger = signed_tx.last_ledger_sequence
        tx_id = signed_tx.get_hash()
        return signed_tx, max_ledger, tx_id

    @staticmethod
    def submit_transaction(signed_tx, client):
        try:
            tx_response = xrpl.transaction.submit_and_wait(signed_tx, client)
            return tx_response
        except xrpl.transaction.XRPLReliableSubmissionException as e:
            raise Exception(f"Submit failed: {e}")

    @staticmethod
    def get_balance(address, client):
        acc_info = AccountInfo(
            account=address,
            ledger_index="validated",
            strict=True,
        )
        response = client.request(acc_info)
        new_balance_drops = response.result["account_data"]["Balance"]
        return float(new_balance_drops) / 1_000_000

    @staticmethod
    def print_transaction_results(tx_response, tx_id):
        print(json.dumps(tx_response.result, indent=4, sort_keys=True))
        print(f"Explorer link: https://testnet.xrpl.org/transactions/{tx_id}")
        metadata = tx_response.result.get("meta", {})
        if metadata.get("TransactionResult"):
            print("Result code:", metadata["TransactionResult"])
        if metadata.get("delivered_amount"):
            print("XRP delivered:", xrpl.utils.drops_to_xrp(
                metadata["delivered_amount"]))

    @staticmethod
    def execute(value, from_account, from_wallet, to_account, client):
        payment = Transaction.prepare_transaction(value, from_account, to_account)
        signed_tx, max_ledger, tx_id = Transaction.sign_transaction(payment, from_wallet, client)
        tx_response = Transaction.submit_transaction(signed_tx, client)
        Transaction.print_transaction_results(tx_response, tx_id)
        return Transaction.get_balance(from_account, client)
    
    @staticmethod
    def get_transaction_history(address, limit = 10):
        tx_request = AccountTx(
            account=address,
            ledger_index_min=-1,
            ledger_index_max=-1,
            limit=limit,
            binary=False,
            forward=False,
        )
        response = client.request(tx_request)
        return response.result.get("transactions", [])


class TrustLine:
    @staticmethod
    def create_trustline(wallet, issuer_address, currency_code, limit, client):
        """
        Establishes a trustline between the wallet and the issuer for a specific currency.

        Args:
            wallet (xrpl.wallet.Wallet): The user's XRPL wallet.
            issuer_address (str): The address of the token issuer.
            currency_code (str): Currency code (e.g. "USD").
            limit (float): The trust limit amount.
            client (xrpl.clients.JsonRpcClient): The XRPL client object.

        Returns:
            dict: XRPL response from transaction submission.
        """

        trust_set_tx = TrustSet(
            account=wallet.classic_address,
            limit_amount=IssuedCurrencyAmount(
                currency=currency_code,
                issuer=issuer_address,
                value=str(limit)
            )
        )
        signed_tx = autofill_and_sign(trust_set_tx, client, wallet)  
        response = submit_and_wait(signed_tx, client)
        return response.result
    
    @staticmethod
    def delete_trustline(wallet, issuer_address, currency_code, client):
        """
        Deletes a trust line by setting its limit to 0.

        Args:
            wallet (xrpl.wallet.Wallet): The user's XRPL wallet.
            issuer_address (str): The issuer of the token.
            currency_code (str): The currency code of the trustline.
            client (xrpl.clients.JsonRpcClient): XRPL client.

        Returns:
            dict: XRPL response.
        """
        trust_delete_tx = TrustSet(
            account=wallet.classic_address,
            limit_amount=IssuedCurrencyAmount(
                currency=currency_code,
                issuer=issuer_address,
                value="0"  # Setting limit to 0 removes trustline
            )
        )
        signed_tx = autofill_and_sign(trust_delete_tx, client, wallet)
        response = submit_and_wait(signed_tx, client)
        return response.result
    
class TrustLineAnalytics:
    @staticmethod
    def decode_currency(currency_hex):
        try:
            decoded = bytes.fromhex(currency_hex).decode("ascii").rstrip('\x00')
            return decoded
        except Exception:
            return currency_hex  # fallback to raw if invalid ASCII
        
    @staticmethod
    def get_trustlines(address):
        result = client.request(AccountLines(account=address)).result
        return result.get("lines", [])
    
    @staticmethod
    def summarize_trustlines(address):
        lines = TrustLineAnalytics.get_trustlines(address)
        summary = {
            "total_trustlines": 0,
            "currencies": {},
        }

        for line in lines:
            currency = TrustLineAnalytics.decode_currency(line["currency"])
            issuer = line["account"]
            balance = float(line["balance"])
            limit = float(line["limit"])

            if (
                float(line["balance"]) == 0 and
                float(line["limit"]) == 0 and
                float(line.get("limit_peer", 0)) == 0
            ):
                continue

            summary["total_trustlines"] += 1

            if currency not in summary["currencies"]:
                summary["currencies"][currency] = []

            summary["currencies"][currency].append({
                "issuer": issuer,
                "balance": balance,
                "limit": limit,
            })

        currency_summary = {}
        for currency, entries in summary["currencies"].items():
            total_balance = sum(e["balance"] for e in entries)
            total_limit = sum(e["limit"] for e in entries)
            currency_summary[currency + "_summary"] = {
                "total_balance": total_balance,
                "total_limit": total_limit
            }

        summary["currencies"].update(currency_summary)  # safe to do after iteration

        return summary