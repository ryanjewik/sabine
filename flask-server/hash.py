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
if ph.verify("$argon2id$v=19$m=65536,t=2,p=1$urawdSIxHjLVcxe0rqE3rA$8av3470lc5483B0m0p6dWHT8HBBLmgbOogVoNjhp2bA", password):
    print("Password verification successful")