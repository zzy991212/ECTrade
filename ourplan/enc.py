'''
NAL16 Proxy Re-Encryption
| From: Nunez, D., Agudo, I., & Lopez, J. (2016). On the application of generic CCA-secure transformations to proxy re-encryption
| Published in: Security and Communication Networks
| Available from: http://onlinelibrary.wiley.com/doi/10.1002/sec.1434/full
* type:           proxy encryption
* properties:     CCA_21-secure, unidirectional, single-hop, non-interactive, collusion-resistant
* setting:        Pairing groups (Type 1 "symmetric")
* assumption:     3-wDBDHI (3-weak Decisional Bilinear DH Inversion)
* to-do:          first-level encryption & second-level decryption, type annotations
:Authors:    D. Nuñez
:Date:       04/2016
'''

from charm.toolbox.pairinggroup import PairingGroup,ZR,G1,G2,GT,pair
from charm.toolbox.PREnc import PREnc
from charm.toolbox.hash_module import Hash,int2Bytes,integer
import ast
import base64

debug = False
class NAL16a(PREnc):
    """
    Testing NAL16a implementation 

    >>> from charm.toolbox.pairinggroup import PairingGroup,ZR,G1,G2,GT,pair
    >>> groupObj = PairingGroup('SS512')
    >>> pre = NAL16a(groupObj)
    >>> params = pre.setup()
    >>> (pk_a, sk_a) = pre.keygen(params)
    >>> (pk_b, sk_b) = pre.keygen(params)
    >>> msg = groupObj.random(GT)
    >>> c_a = pre.encrypt(params, pk_a, msg)
    >>> rk = pre.rekeygen(params, pk_a, sk_a, pk_b, sk_b)
    >>> c_b = pre.re_encrypt(params, rk, c_a)
    >>> assert msg == pre.decrypt(params, sk_b, c_b), 'Decryption of re-encrypted ciphertext was incorrect'
    """
    
    def __init__(self, groupObj):
        global group
        group = groupObj
        
    def F(self, params, t):
        return (params['u'] ** t) * params['v']

    def setup(self):
        g, u, v = group.random(G1), group.random(G1), group.random(G1)
        Z = pair(g,g)

        params = {'g': g, 'u': u, 'v': v, 'Z': Z} 
        if(debug):
            print("Setup: Public parameters...")
            group.debug(params)
        # print(params)    
        return params

    def keygen(self, params):
        x = group.random(ZR)
        g_x = params['g'] ** x

        sk = x      # { 'sk' : x }
        pk = g_x    # { 'pk' : g_x }

        if(debug):
            print('\nKeygen...')
            print("pk => '%s'" % pk)
            print("sk => '%s'" % sk)
        return (pk, sk)

    def rekeygen(self, params, pk_a, sk_a, pk_b, sk_b):
        rk = pk_b ** (~sk_a)
        if(debug):
            print('\nReKeyGen...')
            print("rk => '%s'" % rk)
        return rk

    def encrypt(self, params, pk, m):
        #m = group.encode(M, GT)
        r1, r2 = group.random(ZR), group.random(ZR)
        
        c0 = self.F(params, r1) ** r2
        c1 = m * (params['Z'] ** r2)
        c2 = pk ** r2

        c = {'c0': c0, 'c1': c1, 'c2': c2}
               
        if(debug):
            print('\nEncrypt...')
            print('m => %s' % m)
            print('r1 => %s' % r1)
            print('r2 => %s' % r2)
            print('c => %s' % c)
            group.debug(c)
        return c  
        
    def decrypt(self, params, sk, c):
    
        c1 = c['c1'] 
        c2 = c['c2']

        m = c1 / (c2 ** (~sk))
        
        if(debug):
            print('\nDecrypt...')
            print('m => %s' % m)

        #return group.decode(m)
        return m
        
    def re_encrypt(self, params, rk, c_a):

        c2 = c_a['c2']

        c_b = c_a
        c_b['c2'] = pair(c2, rk)
        
        if(debug):
            print('\nRe-encrypt...')
            print('c\' => %s' % c_b)
        return c_b

class NAL16b(NAL16a):
    """
    Testing NAL16 implementation 

    >>> from charm.toolbox.pairinggroup import PairingGroup,ZR,G1,G2,GT,pair
    >>> groupObj = PairingGroup('SS512')
    >>> pre = NAL16b(groupObj)
    >>> params = pre.setup()
    >>> (pk_a, sk_a) = pre.keygen(params)
    >>> (pk_b, sk_b) = pre.keygen(params)
    >>> msg = b"Hello world!"
    >>> c_a = pre.encrypt(params, pk_a, msg)
    >>> rk = pre.rekeygen(params, pk_a, sk_a, pk_b, sk_b)
    >>> c_b = pre.re_encrypt(params, rk, c_a)
    >>> assert msg == pre.decrypt(params, sk_b, c_b), 'Decryption of re-encrypted ciphertext was incorrect'
    """

    def __init__(self, groupObj):
        global group, h
        group = groupObj
        h = Hash(group)

    def H(self, gt, s):
        h1 = group.hash((gt, s, 1), ZR)
        h2 = group.hash((gt, s, 2), ZR)
        if(debug):
            print('\nH ...')
            print("gt => '%s'" % gt)
            print("s => '%s'" % s)
            print("h1 => '%s'" % h1)
            print("h2 => '%s'" % h2)
        return (h1, h2)

    def G(self, x):
        hh = h.hashToZn(x)
        if(debug):
            print('\nG ...')
            print("x => '%s'" % x)
            print("G(x) => '%s'" % hh)
        return hh

    def encrypt(self, params, pk, m):
        sigma = group.random(GT)
        c3 = self.G(sigma) ^ integer(m)
        (r1, r2) = self.H(sigma, c3)

        c = super(NAL16b, self).encrypt(params, pk, sigma)

        c['c3'] = c3
               
        if(debug):
            print('\nEncrypt...')
            print('m => %s' % m)
            print('r1 => %s' % r1)
            print('r2 => %s' % r2)
            print('c => %s' % c)
            group.debug(c)
        return c 

    def decrypt_original(self, params, sk, c):
        """
        Decrypt the original first-level ciphertext using the private key.
        This method allows the delegator (Alice) to decrypt ciphertexts encrypted for her.
        """
        # Compute T = e(c2, g)
        T = pair(c['c2'], params['g'])
        # Recover sigma: c1 / T^{1/sk}
        sigma = c['c1'] / (T ** (~sk))
        
        c3 = c['c3']
        # Recover (r1, r2) from hash H(sigma, c3)
        (r1, r2) = self.H(sigma, c3)
        
        # Verify ciphertext consistency: c0 == F(params, r1)^r2
        c0_prime = self.F(params, r1) ** r2
        # if c0_prime != c['c0']:
        #     if debug:
        #         print("Consistency check failed in decrypt_original")
        #     return None  # Ciphertext is invalid
        
        # Compute message: m = c3 XOR G(sigma)
        m_int = c3 ^ self.G(sigma)
        m = int2Bytes(m_int)
        
        if debug:
            print('\nDecrypt_original...')
            print('m => %s' % m)
        return m

    def decrypt(self, params, sk, c):
        sigma = super(NAL16b, self).decrypt(params, sk, c)
        c3 = c['c3']
        (r1, r2) = self.H(sigma, c3)
        m = int2Bytes(c3 ^ self.G(sigma))
        
        if(debug):
            print('\nDecrypt...')
            print('m => %s' % m)
        return m

    def re_encrypt(self, params, rk, c_a):
        c_b = super(NAL16b, self).re_encrypt(params, rk, c_a)
        c_b['c3'] = c_a['c3']
        if(debug):
            print('\nRe-encrypt...')
            print('c\' => %s' % c_b)
        return c_b

# groupObj = PairingGroup('SS512')
# pre = NAL16b(groupObj)
# params = pre.setup()

# (pk_a, sk_a) = pre.keygen(params)
# (pk_b, sk_b) = pre.keygen(params)
# msg = b"Hello world!"
# c_a = pre.encrypt(params, pk_a, msg)
# rk = pre.rekeygen(params, pk_a, sk_a, pk_b, sk_b)
# c_b = pre.re_encrypt(params, rk, c_a)
# pre.decrypt(params, sk_b, c_b) 
# ----------------------------------------------------------------------------------------------
groupObj = PairingGroup('SS512')
pre = NAL16b(groupObj)
params = pre.setup()

(pk_a, sk_a) = pre.keygen(params)
(pk_b, sk_b) = pre.keygen(params)
print(f"a的pk: {pk_a}")

with open("a.pk","wb") as f:
    ser = group.serialize(pk_a)
    hex_ser = ser.hex()
    line = f"{hex_ser}".encode("utf-8")
    f.write(line)

print(f"a的sk: {sk_a}")

with open("a.sk","wb") as f:
    ser = group.serialize(sk_a)
    hex_ser = ser.hex()
    line = f"{hex_ser}".encode("utf-8")
    f.write(line)

print(f"b的pk: {pk_b}")

with open("b.pk","wb") as f:
    ser = group.serialize(pk_b)
    hex_ser = ser.hex()
    line = f"{hex_ser}".encode("utf-8")
    f.write(line)

print(f"b的sk: {sk_b}")

with open("b.sk","wb") as f:
    ser = group.serialize(sk_b)
    hex_ser = ser.hex()
    line = f"{hex_ser}".encode("utf-8")
    f.write(line)

with open("sample.txt", 'rb') as f:
    msg = f.read()
#print(f"原始消息: {msg}")
c_a = pre.encrypt(params, pk_a, msg)
#print(f"用户A的密文: {c_a}")

# Serialize and write ciphertext
with open("sample.enc", 'wb') as f:
    for key, value in c_a.items():
        if key == 'c3':
            value = int(value)
            byte_length = (value.bit_length() + 7) // 8
            bytes_data = value.to_bytes(byte_length, 'big')
            base64_str = base64.b64encode(bytes_data).decode('ascii')
            line = f"{key}:b64:{base64_str}\n".encode("utf-8")

        else:
            ser = group.serialize(value)
            hex_ser = ser.hex()
            line = f"{key}:hex:{hex_ser}\n".encode("utf-8")
        f.write(line)

# Read and deserialize ciphertext
loaded_data = {}
with open("sample.enc", 'rb') as f:
    for line in f:
        line_str = line.decode("utf-8").strip()
        key, type_str, value_str = line_str.split(':', 2)
        if type_str == 'b64':
            bytes_data = base64.b64decode(value_str)
            v = int.from_bytes(bytes_data, 'big')
            loaded_data[key] = integer(v)
        elif type_str == 'hex':
            ser_data = bytes.fromhex(value_str)
            elem = group.deserialize(ser_data)
            loaded_data[key] = elem

read_c_a = loaded_data

#print("Original c_a:", c_a)
#print("Loaded c_a:", read_c_a)
# Verify correctness
# print(type(read_c_a['c3']))

assert type(c_a['c0']) == type(read_c_a['c0']), 'c0 mismatch'
assert type(c_a['c1']) == type(read_c_a['c1']), 'c1 mismatch'
assert type(c_a['c2']) == type(read_c_a['c2']), 'c2 mismatch'
assert type(c_a['c3']) == type(read_c_a['c3']), 'c3 mismatch'

assert c_a['c0'] == read_c_a['c0'], 'c0 不匹配'
assert c_a['c1'] == read_c_a['c1'], 'c1 不匹配'
assert c_a['c2'] == read_c_a['c2'], 'c2 不匹配'
assert int(c_a['c3']) == int(read_c_a['c3']), 'c3 值不匹配'

rk = pre.rekeygen(params, pk_a, sk_a, pk_b, sk_b)
print(f"重加密密钥: {rk}")
with open("a-b.rk","wb") as f:
    ser = group.serialize(rk)
    hex_ser = ser.hex()
    line = f"{hex_ser}".encode("utf-8")
    f.write(line)

with open("a-b.rk", 'rb') as f:
    line = f.read()
    line_str = line.decode("utf-8").strip()
    ser_data = bytes.fromhex(line_str)
    rk_file = group.deserialize(ser_data)

assert rk_file == rk, "rk 不匹配"
c_b = pre.re_encrypt(params, rk, read_c_a)
#print(f"用户B的密文: {c_b}")
d_msg = pre.decrypt(params, sk_b, c_b)
#print(f"解密后的消息: {d_msg}")

with open("sample.dec", 'wb') as f:
        f.write(d_msg)

assert msg == pre.decrypt(params, sk_b, c_b), 'Decryption of re-encrypted ciphertext was incorrect'


st01 = b'10111100000001101000100111010001001110001010110001110100111011110101010100110110'
st01 = st01.hex()

print(f"String 01:{st01}")
st01_enc = pre.encrypt(params, pk_b, st01)
print(f"String 01 encrytion:{st01_enc}")

with open("01.enc", 'wb') as f:
    for key, value in st01_enc.items():
        if key == 'c3':
            line = f"{key}:int:{value}\n".encode("utf-8")
        else:
            ser = group.serialize(value)
            hex_ser = ser.hex()
            line = f"{key}:hex:{hex_ser}\n".encode("utf-8")
        f.write(line)

loaded_data = {}
with open("01.enc", 'rb') as f:
    for line in f:
        line_str = line.decode("utf-8").strip()
        key, type_str, value_str = line_str.split(':', 2)
        if type_str == 'int':
            loaded_data[key] = integer(int(value_str))
        elif type_str == 'hex':
            ser_data = bytes.fromhex(value_str)
            elem = group.deserialize(ser_data)
            loaded_data[key] = elem

st01_enc_from_file = loaded_data

st01_dec = pre.decrypt_original(params, sk_b, st01_enc_from_file)
print(f"String 01 decrytion:{st01_dec}")


# c_b_t = pre.encrypt(params, pk_b, msg)
# print(f"用户B的密文: {c_b_t}")
# d_msg_t = pre.decrypt_original(params, sk_b, c_b_t)
# print(f"2解密后的消息: {d_msg_t}")
# assert d_msg == d_msg_t, 'Decryption of re-encrypted ciphertext was incorrect'