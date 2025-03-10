"""
Terminal Client for Securely Obtaining IPEKs

This client demonstrates how a payment terminal would:
1. Register with the IPEK service
2. Generate and use RSA key pairs
3. Request an IPEK with proper authentication
4. Decrypt and verify the received IPEK
"""
import random
import requests
import json
import uuid
import base64
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.backends import default_backend
import os

from dotenv import load_dotenv


class TerminalClient:
    def __init__(self, terminal_id, api_key, service_url="http://localhost:8000"):
        """
        Initialize the terminal client

        Args:
            terminal_id (str): Unique identifier for this terminal
            service_url (str): Base URL of the IPEK service
        """
        self.terminal_id = terminal_id
        self.service_url = service_url
        self.api_key = api_key
        self.private_key = None
        self.public_key = None
        self.service_public_key = None
        self.full_ksn = None

        # Check if we have keys already, if not generate them
        self._load_or_generate_keys()

    def _load_or_generate_keys(self):
        """Load existing keys or generate new ones"""
        key_file = f"{self.terminal_id}_private_key.pem"

        if os.path.exists(key_file):
            # Load existing keys
            with open(key_file, "rb") as f:
                self.private_key = serialization.load_pem_private_key(
                    f.read(),
                    password=None,
                    backend=default_backend()
                )
                self.public_key = self.private_key.public_key()
            print(f"Loaded existing keys for terminal {self.terminal_id}")
        else:
            # Generate new keys
            self.private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048,
            )
            self.public_key = self.private_key.public_key()

            # Save the private key
            with open(key_file, "wb") as f:
                f.write(self.private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption()
                ))

            # Save the public key
            with open(f"{self.terminal_id}_public_key.pem", "wb") as f:
                f.write(self.public_key.public_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PublicFormat.SubjectPublicKeyInfo
                ))
            print(f"Generated new keys for terminal {self.terminal_id}")

    def register(self):
        """Register the terminal with the IPEK service"""
        try:
            # Prepare registration payload
            payload = {
                "terminal_id": self.terminal_id,
                "public_key": self.public_key.public_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PublicFormat.SubjectPublicKeyInfo
                ).decode()
            }

            # Send registration request
            response = requests.post(
                f"{self.service_url}/p2pe/register-terminal-for-remote-key-injection",
                json=payload,
                headers={"Authorization": f"Bearer {self.api_key}"}
            )

            if response.status_code != 200:
                print(f"Registration failed with status {response.status_code}")
                print(response.json())
                return False

            # Store the service's public key
            response_data = response.json()
            print(f"RESPONSE DATA: {response_data}")
            print(f"RESPONSE DATA MESSAGE: {response_data['message']}")
            self.full_ksn = response_data["message"]["full_ksn"]
            self.service_public_key = serialization.load_pem_public_key(
                response_data["message"]["service_public_key"].encode(),
                backend=default_backend()
            )

            # Save service public key
            with open("service_public_key.pem", "wb") as f:
                f.write(self.service_public_key.public_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PublicFormat.SubjectPublicKeyInfo
                ))

            print(f"Terminal {self.terminal_id} registered successfully")
            return True
        except Exception as e:
            print(f"Registration error: {str(e)}")
            raise

    def _sign_payload(self, payload):
        """Sign a payload with the terminal's private key"""
        if isinstance(payload, dict):
            # Convert dict to sorted JSON string for consistent signatures
            payload = json.dumps(payload, sort_keys=True).encode()
        elif isinstance(payload, str):
            payload = payload.encode()

        signature = self.private_key.sign(
            payload,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )

        return base64.b64encode(signature).decode()

    def _verify_signature(self, payload, signature):
        """Verify a signature from the service"""
        if isinstance(payload, dict):
            # Convert dict to sorted JSON string for consistent verification
            payload = json.dumps(payload, sort_keys=True).encode()
        elif isinstance(payload, str):
            payload = payload.encode()

        try:
            # Verify the signature
            self.service_public_key.verify(
                base64.b64decode(signature),
                payload,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            return True
        except Exception as e:
            print(f"Signature verification failed: {str(e)}")
            return False

    def _decrypt_ipek(self, encrypted_ipek):
        """Decrypt the IPEK using the terminal's private key"""
        try:
            # Decode from base64
            encrypted_bytes = base64.b64decode(encrypted_ipek)

            # Decrypt with the private key
            decrypted_ipek = self.private_key.decrypt(
                encrypted_bytes,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )

            # Convert to hex
            return decrypted_ipek.hex().upper()
        except Exception as e:
            print(f"IPEK decryption failed: {str(e)}")
            raise

    def request_ipek(self):
        """
        Request an IPEK from the service

        Returns:
            dict: containing the decrypted IPEK, KSN, and KCV if successful
            None: if request fails
        """
        try:
            # Generate a nonce
            nonce = str(uuid.uuid4())

            # Prepare payload - KSN is now fully managed by the server
            payload = {
                "terminal_id": self.terminal_id,
                "full_ksn": self.full_ksn,
                "nonce": nonce,
            }

            # Sign the payload
            signature = self._sign_payload(payload)
            payload["signature"] = signature
            payload["full_ksn"] = self.full_ksn

            # Send the request
            response = requests.post(
                f"{self.service_url}/p2pe/get-key-from-registered-terminal-for-remote-key-injection",
                json=payload,
                headers={"Authorization": f"Bearer {self.api_key}"}
            )

            if response.status_code != 200:
                print(f"IPEK request failed with status {response.status_code}")
                print(response.json())
                return None

            # Get the response
            response_data = response.json()

            # Verify the signature
            signature = response_data.pop("signature")
            if not self._verify_signature(response_data, signature):
                print("Response signature verification failed!")
                return None

            # Verify the nonce matches
            if response_data["nonce"] != nonce:
                print("Nonce mismatch! Possible replay attack.")
                return None

            # Decrypt the IPEK
            encrypted_ipek = response_data["encrypted_ipek"]
            ipek = self._decrypt_ipek(encrypted_ipek)

            # Return the values
            return {
                "ipek": ipek,
                "ksn": response_data["ksn"],
                "kcv": response_data["kcv"],
                "request_id": response_data["request_id"]
            }

        except Exception as e:
            print(f"Error requesting IPEK: {str(e)}")
            return None


def randomize_number(num_str):
    # Convert the string to a list of digits
    digits = list(num_str)
    # Shuffle the list in place
    random.shuffle(digits)
    # Join the digits back into a string
    return ''.join(digits)


if __name__ == "__main__":
    # load environment
    load_dotenv()

    # get api key
    api_key = os.getenv("API_KEY")

    # Example usage
    terminal_id = f"AECD{randomize_number('123456')}"  # Use a unique terminal ID

    # Create the terminal client
    terminal = TerminalClient(terminal_id, api_key)

    # Register with the service (only needs to be done once)
    terminal.register()

    # Request an IPEK - the server now fully manages KSN generation
    result = terminal.request_ipek()

    if result:
        print("\nSuccessfully received IPEK:")
        print(f"IPEK: {result['ipek']}")
        print(f"KSN: {result['ksn']}")
        print(f"KCV: {result['kcv']}")
    else:
        print("Failed to get IPEK")
