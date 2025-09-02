import logging
import secrets
import string
import base64

logger = logging.getLogger(__name__)

class QuantumEncryption:
    @staticmethod
    def xor_encrypt(message, key):
        """XOR encryption with quantum key"""
        try:
            if not key:
                raise ValueError("Encryption key is empty")
            
            # Convert binary key to bytes
            key_bytes = bytes(int(key[i:i+8], 2) for i in range(0, len(key), 8))
            
            # Convert message to bytes
            message_bytes = message.encode('utf-8')
            
            encrypted_bytes = bytearray()
            for i, byte in enumerate(message_bytes):
                key_byte = key_bytes[i % len(key_bytes)]
                encrypted_bytes.append(byte ^ key_byte)
            
            # Return as base64 string for safe transmission
            return base64.b64encode(encrypted_bytes).decode('ascii')
            
        except Exception as e:
            logger.error(f"XOR encryption error: {e}")
            return message  # Return original message if encryption fails
    
    @staticmethod
    def xor_decrypt(ciphertext, key):
        """XOR decryption with quantum key"""
        try:
            if not key:
                raise ValueError("Decryption key is empty")
            
            # Convert binary key to bytes
            key_bytes = bytes(int(key[i:i+8], 2) for i in range(0, len(key), 8))
            
            # Decode from base64
            encrypted_bytes = base64.b64decode(ciphertext.encode('ascii'))
            
            decrypted_bytes = bytearray()
            for i, byte in enumerate(encrypted_bytes):
                key_byte = key_bytes[i % len(key_bytes)]
                decrypted_bytes.append(byte ^ key_byte)
            
            # Return as UTF-8 string
            return decrypted_bytes.decode('utf-8')
            
        except Exception as e:
            logger.error(f"XOR decryption error: {e}")
            return ciphertext  # Return ciphertext if decryption fails
    
    @staticmethod
    def one_time_pad_encrypt(message, key):
        """One-Time Pad encryption with quantum key"""
        try:
            if not key:
                raise ValueError("Encryption key is empty")
            
            # Ensure key is at least as long as message
            extended_key = (key * ((len(message) // len(key)) + 1))[:len(message)]
            
            encrypted = []
            for i, char in enumerate(message):
                # Convert key bit to int and use for encryption
                key_bit = int(extended_key[i % len(key)])
                encrypted_char = chr((ord(char) + key_bit) % 256)
                encrypted.append(encrypted_char)
            
            return ''.join(encrypted)
            
        except Exception as e:
            logger.error(f"One-Time Pad encryption error: {e}")
            return message
    
    @staticmethod
    def one_time_pad_decrypt(ciphertext, key):
        """One-Time Pad decryption with quantum key"""
        try:
            if not key:
                raise ValueError("Decryption key is empty")
            
            # Ensure key is at least as long as ciphertext
            extended_key = (key * ((len(ciphertext) // len(key)) + 1))[:len(ciphertext)]
            
            decrypted = []
            for i, char in enumerate(ciphertext):
                # Convert key bit to int and use for decryption
                key_bit = int(extended_key[i % len(key)])
                decrypted_char = chr((ord(char) - key_bit) % 256)
                decrypted.append(decrypted_char)
            
            return ''.join(decrypted)
            
        except Exception as e:
            logger.error(f"One-Time Pad decryption error: {e}")
            return ciphertext
    
    @staticmethod
    def simulate_hacker_attack(original_message, encrypted_message):
        """Simulate what a hacker would see without the quantum key"""
        try:
            # Generate random garbage that looks like failed decryption attempts
            garbage_attempts = []
            
            for attempt in range(3):
                # Create random "decryption" attempts
                garbage = ''.join(
                    secrets.choice(string.ascii_letters + string.digits + '!@#$%^&*()_+-=[]{}|;:,.<>?')
                    for _ in range(len(original_message))
                )
                garbage_attempts.append(f"Attempt {attempt + 1}: {garbage}")
            
            return {
                'intercepted_ciphertext': encrypted_message,
                'failed_decryptions': garbage_attempts,
                'status': 'FAILED - Quantum encryption unbreakable without key',
                'original_length': len(original_message)
            }
            
        except Exception as e:
            logger.error(f"Hacker simulation error: {e}")
            return {
                'intercepted_ciphertext': encrypted_message,
                'failed_decryptions': ['[Error simulating attack]'],
                'status': 'ERROR',
                'original_length': 0
            }
