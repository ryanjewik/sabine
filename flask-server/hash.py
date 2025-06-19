from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError


password = "Certifiedweeb02!"
ph = PasswordHasher(
        time_cost=2,  # Time cost for hashing
        memory_cost=2**16,  # Memory cost in KB
        parallelism=1,  # Number of parallel threads
        hash_len=32,  # Length of the hash
        salt_len=16  # Length of the salt
    )
hashed_password = ph.hash(password)
print(f"Hashed password: {hashed_password}")
print("--------------------------------------------------------------------------------------------------------------------------------------")
password2 = "Certifiedweeb02!"
ph2 = PasswordHasher(
        time_cost=2,  # Time cost for hashing
        memory_cost=2**16,  # Memory cost in KB
        parallelism=1,  # Number of parallel threads
        hash_len=32,  # Length of the hash
        salt_len=16  # Length of the salt
    )
hashed_password2 = ph2.hash(password2)
print(f"Hashed password: {hashed_password}")