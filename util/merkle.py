import hashlib

def sha256(data):
    """计算输入数据的SHA-256哈希值"""
    return hashlib.sha256(data.encode('utf-8')).hexdigest()

def build_merkle_tree(hashes):
    """
    从给定的哈希数组构建Merkle树
    
    参数:
    hashes (list): 包含n个哈希字符串的数组
    
    返回:
    list: 表示Merkle树的二维列表，每个子列表是树的一层
    """
    if not hashes:
        return []
    
    # 复制原始哈希列表作为树的第一层
    tree = [hashes.copy()]
    
    # 循环构建每一层，直到到达根节点
    current_level = hashes
    while len(current_level) > 1:
        next_level = []
        for i in range(0, len(current_level), 2):
            # 获取左右子节点
            left = current_level[i]
            # 如果是奇数个节点，最后一个节点会与自身哈希
            right = current_level[i + 1] if i + 1 < len(current_level) else left
            
            # 连接并哈希左右子节点
            combined = left + right
            parent_hash = sha256(combined)
            next_level.append(parent_hash)
        
        # 将新层添加到树中
        tree.append(next_level)
        # 更新当前层为新创建的层
        current_level = next_level
    
    return tree

def get_root(merkle_tree):
    """获取Merkle树的根哈希"""
    return merkle_tree[-1][0] if merkle_tree else None

def get_merkle_proof(merkle_tree, index):
    """
    为指定索引的叶子节点生成Merkle证明路径
    
    参数:
    merkle_tree (list): 已构建的Merkle树
    index (int): 叶子节点的索引
    
    返回:
    list: Merkle证明路径，每个元素是一个元组 (hash_value, is_left)
    """
    proof = []
    current_index = index
    
    # 从叶子节点开始向上遍历每一层，直到根节点的上一层
    for i in range(len(merkle_tree) - 1):
        current_level = merkle_tree[i]
        
        # 确定兄弟节点的位置和值
        if current_index % 2 == 0:
            # 当前节点是左子节点，兄弟节点在右边
            sibling_index = current_index + 1
            is_left = False
        else:
            # 当前节点是右子节点，兄弟节点在左边
            sibling_index = current_index - 1
            is_left = True
        
        # 如果兄弟节点存在，添加到证明中
        if sibling_index < len(current_level):
            proof.append((current_level[sibling_index], is_left))
        
        # 计算父节点的索引，向上移动一层
        current_index = current_index // 2
    
    return proof

# 示例使用
if __name__ == "__main__":
    # 示例哈希数组
    hashes = [
"130fa2f1b5379d29e813322c5a69622d9f24b1fad549c74fdf8e2a12514c65df",
"27ad857d4d15f8cd0e23e8f568f223428bf88d52a33b4dafd793e0591131b21d",
"e1543d5947789c4131ed7ca3c222c2b3db8bf3252b08f5b56a04c26f224c91da",
"c9c4fbb37337a155aa0377e10126a03922da89bd27949b89903ad56d5d476e0e",
"d8d3d82c52a142c1a0ef8c8a4970d43813ef23a361ca7dfbe3814229c71f4565",
"c047ba8b1f6bd3e241d20532f9d71963d9bc2f7301e44d99962f98a92edd696d",
"d6b3c39a35800f16f81551754db065cecd90b0904319e27daa7d145acf6f01a2",
"f55712225791dd0ba55307070b823275ffae5d1309cba6789eb8592bcfb4a95d",
"9da3c8051b93b1ade8a96d20c119319cc7ccd1820e5ce9e7e27ea29ce7fda8dd",
"96294718f3c68f23ee99ab927cab6eb5011c527a9a08680d107033ea53a74312",
"4a005d5e4a4f6e8bd334ee826c0fb06a9971daa8d5b4ee7a38f6c637d0ca1865",
"8ad50c3027761ed76c547475a2d579aa2a792ed7903ae8cc4058d6cc7fbf3c94",
"c1a686acdbcbc08c2066059eac55b048bedd20b9b1d3131e48c3d1c84f530b73",
"da7981dbbcb2a050345872c32ec1a123dd8d8ebc9d107dff1f55c6d272e90d46",
"3f3b2f20a9c3001d4b2d105a32114ea053a87eadd3463b5946815c86317f5e82",
"322e2048c803680e6d3855b80f743dffacb08ca59dc98d5c25e1d17c2656ac10",
"39d3679de3709c333a37f3e354ee7e52450fce7a0239bc6f4d2e368343feac84",
"b4ba24cd0f1b8b5261cdfbf01d17a1ab71599aa3c02e8411242a74a3fc905872",
"34a709341802813e6f96af498a16673958a3a58eb2a6c53f08b64af5f0e4d6e2",
"97c516e0e51a1dcbc52e3aa8ae102c3e2097a6014360311f81ffdb73c57702e4",
"3e36dcea399c75a6f76c0b6eef520ec53d62185b48c68ba20bdec396122ffe4c",
"89de4b372126de0e6aa9d9cfeb7f7330e72930b81f0f134568cf28a709aade8f",
"a8d5ad897d03823bded7d335109896fb650bb91f55399885ace9088cc49ec216",
"1c0c6485de5c817b33d640b9bb49422110674a8e6275a08e2f3745a05d47c2ae",
"1b9a41f3150d0f57ce4822effaf92933817855f4f466d054431979594b0cf809",
"0a5d04d566c05a2b38abd7205a9a5d1d632026d03f6b25f460f86d0c357bf870",
"953179179de1772e0130b4241eb7e18b17d8fae910fc351c09d8bd1ae23c3897",
"67118f1d20786b01b30f5135f50ca083460c4b60060ad160ece40d451ac2da1b",
"0709f9293b14f30a3127428873ce5afca157d0b404a30c6c24f599e997bf0f10",
"9f858fe99c3986573bf4abb8f1526657c6f75033b0409b1e8bce3dc0f8e4c48e",
"8f0da83db7c839f8acfe914bacaef8a073c9f280bc9f754711369f9fe98480db",
"ab2745a1c76fe93f064981ce1c682d87cb4ebfaefaabec0d65f1c8a6c250fff7",
"fb4e2422f8ade2729a0420c1dbf16e331347633c157b28b9acb3cf77aeae08e6",
"63d3b74e7a529261f4b7bd49808c38c905999432b22661820f31e8699878e3b2",
"9e6113622caf7940f8303a1a022cecc9c158bac94252a413b4b39cd3b90957d8",
"473c63490dd978e550607c2bc9e4005885b55c4dcf8d8003666f883978a0520f",
"78a7eb9031a2519bb86440af185a2f11801157334dfdade9794dc37dc1929355",
"3b07486f48bfcfa12d982dc564ec1fd05e654aed222a40cbb83d206b1f3766b9",
"820c3ff60fc54d3b8518cbe71b9e5de7f12642b8cbc8925e2eda7af30574df01",
"1991dfbea608b035bb73d147a4edb993dc88cd7d18fcc324f84b500147574733",
"4f10ab82d8dc76dcfbba5e7cb755c2368ef17576f9eb7051870d40504642ed5c",
"6e17ce01963949471da3a4a8d35dbfe369a0287ac56b9455e4217a4c583fe076",
"523d6c7cc02b6aef07dc6325d7d7204730bfdcb815f868e81b68dace9caa04bc",
"ea37d888a6da17c31158f7ef9fe1d73b8bee307513b38ea271003ef1b5096119",
"184944a755b4726533e7f6a164cb16a43856cffca401e8aa42b89a54501ff17d",
"6b13f762104260fcb3be1c134631864bcb8065a4f7a94e03e5049f33eea2dd68",
"f9e8987cdfa5f9ef53b0b6ec283db949feda8ee43cd62bfda7abcb1a5ef47dcc",
"ed7fe4a7f8c39b92f71f83ef6671c8a817292c33704847bb2f7074226a856cb9",
"317520b8c30cd8b08b1d43c5c6d5d6b62a90b61d57db13b625f627c1702c68f7",
"f8cea480b8615f4cf02cc901c4463f2b101caf539556ba4b1d85f97bcb8e74c7",
"0533cbd53c653a64eddf46d139729eefeef8d5a958110452dcdec3b131ffb5e8",
"952042d2bf10933473ad15c09ac678bc16f1b2e0106b147b5a10a9275dd9f5b7",
"9f1c9843f93b498d75c595f07bf460d909e759586a4b91823d840cbbe14700f1",
"867ed84aa733d83636b657df532500fb5511d7b9f7997fedce4e5c21bb81ea9a",
"7c0c3dcb534a63509c0a5e9736bb06feb4d74d247ef886872066bb2d91ac4504",
"20e117f45e6c21666b451bce32164c0b5f8e4eb23d253d8f1a6a7bb7ec6a3d86",
"9f7c9011db2011b4ec89ed2190335a198bf2f1323412de14dce673050d763840",
"ee9c44e51dcb946487689012f3257531a50c06e11a232e43dce9f394d477cfb5",
"43201132ed02086393d6f898a8c57835a951eea4073f563765399b3c0d4dea74",
"78c6a57e591a08383e17b0b05162b099c10c8b3a47fb83b988d68c03b9be8844",
"dbb2a8ec19cc7f4038e09ac0259302a209179ce7dbd473b0e5705540f697c8e3",
"b0f3e81744d9a6d47cfa15bb689d69d458e29216c57daf0a238fa88b8029f151",
"673e8dacf43e23db017071c0a2bcfc9184c7a16870d8ecc924f562ee00c9733b",
"c21830d130c3e4a7b59aa0c29a31fc959cec0c15cf445911445e495b8efe2370",
"10295bf6f778ee81e1b1b581ba5f1f15bf9c80b78e2f2661dafa370eaf1d7b40",
"9b18604646f614902a9f28cf743f67ab341b6ae0542814ef6513f687d7001e5b",
"807ba53157be653826c3ed2704eeabb113827c9e7a00f595d75f4a92b606e8cb",
"443628d38733feead27655cafc677dd4288e07d9320d7b229ff30e044af383a7",
"70bec3400b995d67e098423d449bbde6a99552954f2cb25519058e9c9e3161b4",
"918b4fde23e1d10afe56153000b5a5237e6f16f63fa9a2fc9e70152758a8f064",
"c15fb33fdac321896faaf62398b701a036f5b3803b41a12fc5ff441c23eb6036",
"a49589ffafe1fa845e09dbde690530d189aff7268af2741605926202b66c5640",
"bce97dc125f8e77004ef79b120e32380fa9c59e39919e1ec2c88bc544f9b1f7e",
"8e34b9e2422e2403fe5b14e8fc4ff2551cfc647d3618a3f46c129375ac84e157",
"fac3f668667b64c69427d909956d6afc5cc455e8a1cef138047c24e38a052604",
"fc3db70b5c2556775873a521e13914f59036b2f5ef7a4234d19dc53f2266b155",
"757ea8e21d6477d45b59cba7757aad04825212179b9da42c4dfcaa46bc5af235",
"959b9234792190c796e2a19aacb9d3b40244c22acffe40c48d3f1a766cce6a6b",
"c22b5bf41a00addc8724058d489b6fff4920684ac237f96445dfc1339854f294",
"ffca1e35f6b2a62c53e3f2e4ea78d8a8cc255857130f16b6fd416feb6827f82a",
"a37c38bea334f0a299f806aa579250af8eb524294968439abee3147d89b4cc11",
"82992bc35181fb13bd75874940184763519af26bf48ee3d82745578dd3c04777",
"e5e28ddd007e033a9e882411403926ac2e2c67537eec0687ea6aa915b1865bef",
"74681d52d22c6bb34d6282a846b11fae8a47559c6caaa6331dd9755dc7b997b7",
"f9c11afef733a5c9685f0982f2acb7eefeb2e52e41551f524123bd2ad31884bd",
"2ce39e99df53b86048d2e73e1e8819bc42f1aba0715d2dbeb146e05f5f05746d",
"cc85a027b50eed3f7f7ec4b8102c3b36cea68100be3ab3a7d3030d32368261e8",
"b68a06f795ffdef0364de1bc9d932b41a5d0fc1dffb2f3d7e62601adf877b8fd",
"341368615ca9f3bed4cdcb33e466bb5a29a329a9918b5c1843444c396ab27ce5",
"e4391edcf8898adbdab3e5379303d5dcec84c553c788b36fdfc7a2970c183ac5",
"fb9b91a347a0e5eeccdd51a3db71f09623ab6bfee5d17083d4e51ebd9f235aff",
"16bf67ffc758dab7ce61256dd4abe916e39110abafa2ff06b1462f0abbf7346e",
"7b854ea19aaa3eef2765753ccc43d3cebd2d0b0ae6bd22acacbfe1050f8ef019",
"9a3e8a2963b2f189f48ca583a4d27e80035aa4ad07a6da9258535284fa221f5f",
"8b284e3fad89ce30176b73c34c019ead86dc886049d9f93e2b622ee5898cc4cb",
"241880cad0ade45a45ffad20a73ae416842484125ed09d1833021ca3e8c7d3a1",
"9c2194d3aeef7fe700f143d96531508662da1072749d288e4db4af5bb29bb932",
"5e6e3c6ea63410037ab5f508e2d8c1627175d76a0a39ea9aaaaf77bc2e145bf7",
"6711ba904260ca99445bd53d4baefb801a48c18dde55f732d68369547ef41b51",
"41aa33e34e56ebd2a594b6d21654f33cf806fcb058ed55afd57d5702d7b7fbf5",
"1945af67e5e752291be911a5af59d9090db170e5210fbde675e0de0681a7c1df",
    ]
    
    # 构建Merkle树
    merkle_tree = build_merkle_tree(hashes)
    
    # 输出每层的哈希
    for i, level in enumerate(merkle_tree):
        print(f"Level {i}: {level}")
    
    # 输出根哈希
    print(f"Merkle Root: {get_root(merkle_tree)}")
    
    # 为第3个块（索引2）生成Merkle证明路径
    block_index = 100
    proof = get_merkle_proof(merkle_tree, block_index)
    
    print(f"\nProof for block at index {block_index}:")
    for i, (hash_value, is_left) in enumerate(proof):
        print(f"Step {i+1}: {'Left' if is_left else 'Right'} sibling = {hash_value}")