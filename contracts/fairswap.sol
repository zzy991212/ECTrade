pragma solidity ^0.4.23;

/**
 * @title FairSwapFileSale
 * @dev 实现论文中"FairSwap: How to fairly exchange digital goods"的大文件公平交易协议
 * 核心机制：通过智能合约作为裁判，利用简洁的不当行为证明实现低成本公平交换（论文1-5节）
 */
contract FairSwapFileSale {
    // 常量定义（符合论文1-47节Merkle树结构要求，编译期确定长度）
    uint public DEPTH;
    uint public CHUNK_LENGTH;
    uint public FILE_CHUNKS;

    // 协议阶段（对应论文1-134节协议流程）
    enum Stage {
        Created,       // 合约创建
        Initialized,   // 卖家提交承诺与Merkle根
        Accepted,      // 买家冻结资金
        KeyRevealed,   // 卖家揭示解密密钥
        Finished       // 交易完成
    }

    // 核心参数
    Stage public phase = Stage.Created;       // 当前阶段
    uint public timeout;                      // 各阶段超时时间（秒）
    address public sender;                    // 卖家地址
    address public receiver;                  // 买家地址
    uint public price;                        // 交易价格（wei）

    // 论文1-126节定义的关键哈希值
    bytes32 public keyCommit;        // 密钥k的承诺（H(k||d)）
    bytes32 public ciphertextRoot;   // 加密数据z的Merkle树根（r_z）
    bytes32 public fileRoot;         // 目标文件的Merkle树根（h）
    bytes32 public key;              // 解密密钥（揭示后存储）

    // 事件日志（跟踪协议关键步骤）
    event Initialized(bytes32 keyCommit, bytes32 ciphertextRoot, bytes32 fileRoot);
    event Accepted(uint amount);
    event KeyRevealed(bytes32 key);
    event Complained(string reason, bool success);
    event Finished(address recipient, uint amount);

    /**
     * @dev 构造函数：初始化参与方和基础参数
     * @param _receiver 买家地址
     * @param _price 交易价格（wei）
     * @param _timeout 各阶段超时时间（秒）
     */
    constructor(
        address _receiver,
        uint _price,
        uint _timeoutStep,
        uint _depth,
        uint _chunkLength,
        uint _fileChunks
    ) public {
        require(_receiver != address(0), "无效买家地址");
        require(_price > 0, "价格必须大于0");
        require(_timeoutStep > 0, "超时必须大于0");
        require(_depth > 0 && _chunkLength > 0 && _fileChunks > 0, "参数无效");

        sender = msg.sender;
        receiver = _receiver;
        price = _price;
        timeout = now + _timeout;  // 初始化阶段超时时间
                DEPTH = _depth;
        CHUNK_LENGTH = _chunkLength;
        FILE_CHUNKS = _fileChunks;
    }

    /**
     * @dev 权限修饰符：限制操作仅在指定阶段、指定地址且未超时的情况下执行
     * 对应论文1-134节的阶段权限控制
     */
    modifier allowed(address _party, Stage _stage) {
        require(phase == _stage, "当前阶段不允许此操作");
        require(now < timeout, "操作已超时");
        require(msg.sender == _party, "无操作权限");
        _;
    }

    /**
     * @dev 卖家初始化：提交密钥承诺和Merkle根（论文1-161节步骤）
     * @param _keyCommit 密钥k的承诺（H(k||d)）
     * @param _ciphertextRoot 加密数据z的Merkle树根（r_z）
     * @param _fileRoot 目标文件的Merkle树根（h）
     */
    function initialize(
        bytes32 _keyCommit,
        bytes32 _ciphertextRoot,
        bytes32 _fileRoot
    ) public allowed(sender, Stage.Created) {
        require(_keyCommit != bytes32(0) && _ciphertextRoot != bytes32(0) && _fileRoot != bytes32(0), "参数不可为空");
        
        keyCommit = _keyCommit;
        ciphertextRoot = _ciphertextRoot;
        fileRoot = _fileRoot;
        phase = Stage.Initialized;
        timeout = now + timeout;  // 更新超时时间
        
        emit Initialized(_keyCommit, _ciphertextRoot, _fileRoot);
    }

    /**
     * @dev 买家接受交易：冻结资金（论文1-162节步骤）
     */
    function accept() public payable allowed(receiver, Stage.Initialized) {
        require(msg.value == price, "支付金额必须等于约定价格");
        
        phase = Stage.Accepted;
        timeout = now + timeout;
        
        emit Accepted(msg.value);
    }

    /**
     * @dev 卖家揭示密钥：验证承诺并公开解密密钥（论文1-164节步骤）
     * @param _key 解密密钥k
     * @param _d 承诺的打开值d
     */
    function revealKey(bytes32 _key, bytes32 _d) public allowed(sender, Stage.Accepted) {
        // 验证密钥与承诺一致性（论文1-304节Commit/Open算法）
        require(keccak256(abi.encodePacked(_key, _d)) == keyCommit, "密钥与承诺不符");
        
        key = _key;
        phase = Stage.KeyRevealed;
        timeout = now + timeout;
        
        emit KeyRevealed(_key);
    }

    /**
     * @dev 买家无投诉：确认文件正确，向卖家付款（论文1-167节无争议场景）
     */
    function noComplain() public allowed(receiver, Stage.KeyRevealed) {
        require(sender.send(price), "向卖家转账失败");
        phase = Stage.Finished;
        emit Finished(sender, price);
    }

    /**
     * @dev 投诉：文件根哈希不符（论文1-185节根节点验证）
     * @param _zm 加密的根节点值（z_m）
     * @param _proofZm 根节点的Merkle证明（长度为DEPTH）
     */
    function complainAboutRoot(bytes32 _zm, bytes32[DEPTH] _proofZm) public allowed(receiver, Stage.KeyRevealed) {
        // 验证zm属于加密数据z（论文1-53节Mvrfy算法）
        require(vrfy(2*(FILE_CHUNKS-1), _zm, _proofZm), "根节点Merkle证明无效");
        
        // 解密zm并验证是否等于目标根（论文1-131节Judge算法）
        bytes32 decryptedRoot = cryptSmall(2*(FILE_CHUNKS-1), _zm);
        bool isInvalid = (decryptedRoot != fileRoot);
        
        if (isInvalid) {
            require(receiver.send(price), "向买家退款失败");
            emit Complained("根哈希不符", true);
        } else {
            require(sender.send(price), "向卖家付款失败");
            emit Complained("根哈希不符", false);
        }
        phase = Stage.Finished;
    }

    /**
     * @dev 投诉：叶子节点哈希运算错误（论文1-127节叶子节点证明）
     * @param _indexOut 输出节点索引
     * @param _indexIn 输入节点起始索引
     * @param _zOut 加密的输出值（z_out）
     * @param _zIn1 加密的输入值1（z_in1）
     * @param _zIn2 加密的输入值2（z_in2）
     * @param _proofZout 输出值的Merkle证明（长度为DEPTH）
     * @param _proofZin 输入值的Merkle证明（长度为DEPTH）
     */
    function complainAboutLeaf(
        uint _indexOut,
        uint _indexIn,
        bytes32 _zOut,
        bytes32[CHUNK_LENGTH] _zIn1,
        bytes32[CHUNK_LENGTH] _zIn2,
        bytes32[DEPTH] _proofZout,
        bytes32[DEPTH] _proofZin
    ) public allowed(receiver, Stage.KeyRevealed) {
        // 验证zOut属于加密数据z
        require(vrfy(_indexOut, _zOut, _proofZout), "输出值Merkle证明无效");
        // 验证zIn1属于加密数据z
        require(vrfy(_indexIn, keccak256(abi.encodePacked(_zIn1)), _proofZin), "输入值1Merkle证明无效");
        // 验证zIn2与证明一致性
        require(_proofZin[0] == keccak256(abi.encodePacked(_zIn2)), "输入值2证明无效");

        // 解密并验证哈希运算（论文1-185节电路运算）
        bytes32[CHUNK_LENGTH] memory xIn1 = cryptLarge(_indexIn, _zIn1);
        bytes32[CHUNK_LENGTH] memory xIn2 = cryptLarge(_indexIn + 1, _zIn2);
        bytes32 xOut = cryptSmall(_indexOut, _zOut);
        bool isInvalid = (xOut != keccak256(abi.encodePacked(xIn1, xIn2)));

        if (isInvalid) {
            require(receiver.send(price), "向买家退款失败");
            emit Complained("叶子节点运算错误", true);
        } else {
            require(sender.send(price), "向卖家付款失败");
            emit Complained("叶子节点运算错误", false);
        }
        phase = Stage.Finished;
    }

    /**
     * @dev 投诉：内部节点哈希运算错误（论文1-127节内部节点证明）
     * @param _indexOut 输出节点索引
     * @param _indexIn 输入节点起始索引
     * @param _zOut 加密的输出值（z_out）
     * @param _zIn1 加密的输入值1（z_in1）
     * @param _zIn2 加密的输入值2（z_in2）
     * @param _proofZout 输出值的Merkle证明（长度为DEPTH）
     * @param _proofZin 输入值的Merkle证明（长度为DEPTH）
     */
    function complainAboutNode(
        uint _indexOut,
        uint _indexIn,
        bytes32 _zOut,
        bytes32 _zIn1,
        bytes32 _zIn2,
        bytes32[DEPTH] _proofZout,
        bytes32[DEPTH] _proofZin
    ) public allowed(receiver, Stage.KeyRevealed) {
        // 验证zOut属于加密数据z
        require(vrfy(_indexOut, _zOut, _proofZout), "输出值Merkle证明无效");
        // 验证zIn1属于加密数据z
        require(vrfy(_indexIn, _zIn1, _proofZin), "输入值1Merkle证明无效");
        // 验证zIn2与证明一致性
        require(_proofZin[0] == _zIn2, "输入值2证明无效");

        // 解密并验证哈希运算（论文1-131节Judge算法）
        bytes32 xIn1 = cryptSmall(_indexIn, _zIn1);
        bytes32 xIn2 = cryptSmall(_indexIn + 1, _zIn2);
        bytes32 xOut = cryptSmall(_indexOut, _zOut);
        bool isInvalid = (xOut != keccak256(xIn1, xIn2));

        if (isInvalid) {
            require(receiver.send(price), "向买家退款失败");
            emit Complained("内部节点运算错误", true);
        } else {
            require(sender.send(price), "向卖家付款失败");
            emit Complained("内部节点运算错误", false);
        }
        phase = Stage.Finished;
    }

    /**
     * @dev 超时处理：未完成交易时的资金分配（论文1-155节终止机制）
     */
    function refund() public {
        require(now > timeout, "未到超时时间");
        
        if (phase == Stage.Initialized) {
            // 买家未接受，终止交易
            phase = Stage.Finished;
            emit Finished(receiver, 0);
        } else if (phase == Stage.Accepted) {
            // 卖家未揭示密钥，退款给买家
            require(receiver.send(price), "买家退款失败");
            phase = Stage.Finished;
            emit Finished(receiver, price);
        } else if (phase == Stage.KeyRevealed) {
            // 买家未投诉，付款给卖家
            require(sender.send(price), "卖家收款失败");
            phase = Stage.Finished;
            emit Finished(sender, price);
        }
    }

    /**
     * @dev 解密大文件块（论文1-309节Enc/Dec算法）
     * @param _index 块索引
     * @param _ciphertext 加密的块数据
     * @return 解密后的块数据
     */
    function cryptLarge(uint _index, bytes32[CHUNK_LENGTH] _ciphertext) public view returns (bytes32[CHUNK_LENGTH]) {
        uint idx = _index * CHUNK_LENGTH;
        for (uint i = 0; i < CHUNK_LENGTH; i++) {
            bytes32 keyStream = keccak256(abi.encodePacked(key, idx)); // 密钥流生成
            _ciphertext[i] = keyStream ^ _ciphertext[i]; // XOR解密
            idx++;
        }
        return _ciphertext;
    }

    /**
     * @dev 解密Merkle树节点（论文1-313节解密逻辑）
     * @param _index 节点索引
     * @param _ciphertext 加密的节点值
     * @return 解密后的节点值
     */
    function cryptSmall(uint _index, bytes32 _ciphertext) public view returns (bytes32) {
        bytes32 keyStream = keccak256(abi.encodePacked(key, FILE_CHUNKS + _index)); // 区分文件块与中间节点
        return keyStream ^ _ciphertext; // XOR解密
    }

    /**
     * @dev Merkle证明验证（论文1-53节Mvrfy算法）
     * @param _index 元素索引
     * @param _value 元素值
     * @param _proof 证明路径（长度为DEPTH）
     * @return 证明是否有效
     */
    function vrfy(uint _index, bytes32 _value, bytes32[DEPTH] _proof) public view returns (bool) {
        bytes32 hash = _value;
        for (uint i = 0; i < DEPTH; i++) {
            if ((_index & 1) == 1) {
                // 右孩子：哈希 = H(proof[i] || hash)
                hash = keccak256(abi.encodePacked(_proof[i], hash));
            } else {
                // 左孩子：哈希 = H(hash || proof[i])
                hash = keccak256(abi.encodePacked(hash, _proof[i]));
            }
            _index = _index >> 1; // 上移至父节点索引
        }
        return hash == ciphertextRoot; // 验证是否匹配根哈希
    }

    // 限制合约仅接受买家在接受阶段的支付
    function () external payable {
        require(msg.sender == receiver && phase == Stage.Initialized, "仅允许买家在接受阶段支付");
    }
}