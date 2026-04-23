// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/**
 * @title NonRepudiableIoTDataTrading
 * @dev 修复版 - 解决资金处理和权限问题
 */
contract NonRepudiableIoTDataTrading {
    // 参与者地址
    address public dataOwner;
    address public dataBuyer;
    address public arbitrator;
    
    // 交易状态
    enum TradeStatus { 
        Created,        // 合约创建
        Requested,      // 数据已请求
        ProofPublished, // 证明已发布
        DepositMade,    // 押金已存
        S2Published,    // S2已发布
        Completed,      // 交易完成
        OnChainArbitration, // 链上仲裁中
        OffChainArbitration // 链下仲裁中
    }
    TradeStatus public status;
    
    // 交易数据结构
    struct TradeData {
        bytes32 tagS;       // Tag(S) = Hash(S1) XOR Hash(S2)
        bytes32 hashS1;     // Hash(S1)
        bytes32 s2;         // 小数据块S2 (256位)
        uint256 payment;    // 支付金额 (wei)
        uint256 ownerDeposit; // 所有者押金
        uint256 buyerDeposit; // 买家押金
        bool ownerMalicious; // 所有者是否恶意
        bool buyerMalicious; // 买家是否恶意
    }
    TradeData public trade;
    
    // 事件定义
    event DataRequested(address indexed buyer, uint256 payment, uint256 buyerDeposit);
    event ProofPublished(bytes32 tagS, bytes32 hashS1);
    event DepositsMade(uint256 ownerDeposit, uint256 buyerDeposit);
    event S2Published(bytes32 s2);
    event PaymentReleased(address indexed to, uint256 amount);
    event OnChainArbitrationInitiated(address indexed initiator);
    event OnChainArbitrationResult(bool ownerMalicious, bool buyerMalicious);
    event OffChainArbitrationInitiated();
    event OffChainArbitrationResult(bool ownerMalicious, bool buyerMalicious);
    
    // 仅允许仲裁者修改的特殊状态
    modifier onlyArbitrator() {
        require(msg.sender == arbitrator, "Only arbitrator can call");
        _;
    }
    
    // 合约构造函数
    constructor(
        address _dataOwner,
        address _dataBuyer,
        address _arbitrator,
        uint256 _payment
    ) {
        dataOwner = _dataOwner;
        dataBuyer = _dataBuyer;
        arbitrator = _arbitrator;
        trade.payment = _payment;
        status = TradeStatus.Created;
    }
    
    // ===================== 核心交易流程 =====================
    
    // 步骤1: 数据买家请求数据
    function requestData() external payable {
        require(msg.sender == dataBuyer, "Only buyer can request");
        require(status == TradeStatus.Created, "Invalid status");
        require(msg.value >= trade.payment, "Insufficient payment");
        
        // 买家支付金额存入合约
        trade.buyerDeposit = msg.value - trade.payment; // 正确计算押金部分
        
        status = TradeStatus.Requested;
        emit DataRequested(msg.sender, trade.payment, trade.buyerDeposit);
    }
    
    // 步骤2: 数据所有者发布证明
    function publishProof(bytes32 _tagS, bytes32 _hashS1) external {
        require(msg.sender == dataOwner, "Only owner can publish");
        require(status == TradeStatus.Requested, "Invalid status");
        
        trade.tagS = _tagS;
        trade.hashS1 = _hashS1;
        
        status = TradeStatus.ProofPublished;
        emit ProofPublished(_tagS, _hashS1);
    }
    
    // 步骤3: 双方存入押金
    function makeDeposit() external payable {
        require(
            status == TradeStatus.ProofPublished, // 修复：仅在ProofPublished状态允许存款
            "Invalid status: Only after proof published"
        );
        
        if (msg.sender == dataOwner) {
            trade.ownerDeposit = msg.value;
            if (trade.buyerDeposit > 0) {
                status = TradeStatus.DepositMade;
                emit DepositsMade(msg.value, trade.buyerDeposit);
            }
        } else if (msg.sender == dataBuyer) {
            // 买家押金已在requestData中设置，这里不允许额外存款
            revert("Buyer deposit already set in requestData");
        } else {
            revert("Unauthorized");
        }
    }
    
    // 步骤4: 数据所有者发布S2
    function publishS2(bytes32 _s2) external {
        require(msg.sender == dataOwner, "Only owner can publish");
        require(status == TradeStatus.DepositMade, "Invalid status");
        
        trade.s2 = _s2;
        status = TradeStatus.S2Published;
        emit S2Published(_s2);
    }
    
    // 步骤5: 完成交易（仅买家可调用）
    function completeTrade() external {
        require(msg.sender == dataBuyer, "Only buyer can complete"); // 修复：仅买家可调用
        require(status == TradeStatus.S2Published, "Invalid status");
        require(!trade.buyerMalicious && !trade.ownerMalicious, "Malicious party detected");
        
        // 支付给数据所有者（服务费）
        payable(dataOwner).transfer(trade.payment);
        
        // 退还押金
        payable(dataOwner).transfer(trade.ownerDeposit);
        payable(dataBuyer).transfer(trade.buyerDeposit); // 正确退还买家押金
        
        status = TradeStatus.Completed;
        emit PaymentReleased(dataOwner, trade.payment);
    }
    
    // ===================== 仲裁流程 =====================
    
    // 步骤6: 发起链上仲裁
    function initiateOnChainArbitration() external {
        require(msg.sender == dataBuyer, "Only buyer can initiate");
        require(status == TradeStatus.S2Published, "Invalid status");
        
        status = TradeStatus.OnChainArbitration;
        emit OnChainArbitrationInitiated(msg.sender);
        
        // 自动执行仲裁（使用预提交的证明）
        _performOnChainArbitration();
    }
    
    // 链上仲裁逻辑
    function _performOnChainArbitration() internal {
        // 计算 Hash(S2)
        bytes32 computedHashS2 = keccak256(abi.encodePacked(trade.s2));
        
        // 验证 Tag(S) = Hash(S1) XOR Hash(S2)
        if (trade.tagS == trade.hashS1 ^ computedHashS2) {
            // 验证成功，买家恶意
            trade.buyerMalicious = true;
        } else {
            // 验证失败，所有者恶意
            trade.ownerMalicious = true;
        }
        
        // 处理资金
        if (trade.buyerMalicious) {
            // 买家恶意：支付给所有者，没收买家押金
            payable(dataOwner).transfer(trade.payment + trade.ownerDeposit);
            payable(arbitrator).transfer(trade.buyerDeposit);
        } else {
            // 所有者恶意：退款给买家，没收所有者押金
            payable(dataBuyer).transfer(trade.payment + trade.buyerDeposit);
            payable(arbitrator).transfer(trade.ownerDeposit);
        }
        
        emit OnChainArbitrationResult(trade.ownerMalicious, trade.buyerMalicious);
    }
    
    // 步骤7: 发起链下仲裁
    function initiateOffChainArbitration() external onlyArbitrator {
        require(status == TradeStatus.OnChainArbitration, "Invalid status");
        
        status = TradeStatus.OffChainArbitration;
        emit OffChainArbitrationInitiated();
    }
    
    // 步骤8: 提交链下仲裁结果（仅仲裁者调用）
    function submitOffChainArbitrationResult(
        bool _ownerMalicious, 
        bool _buyerMalicious
    ) external onlyArbitrator {
        require(status == TradeStatus.OffChainArbitration, "Invalid status");
        
        trade.ownerMalicious = _ownerMalicious;
        trade.buyerMalicious = _buyerMalicious;
        
        // 处理资金
        if (_ownerMalicious) {
            // 所有者恶意：退款给买家，没收所有者押金
            payable(dataBuyer).transfer(trade.payment + trade.buyerDeposit);
            payable(arbitrator).transfer(trade.ownerDeposit);
        } else if (_buyerMalicious) {
            // 买家恶意：支付给所有者，没收买家押金
            payable(dataOwner).transfer(trade.payment + trade.ownerDeposit);
            payable(arbitrator).transfer(trade.buyerDeposit);
        } else {
            // 无恶意行为（异常情况）：退还所有资金
            payable(dataOwner).transfer(trade.ownerDeposit);
            payable(dataBuyer).transfer(trade.payment + trade.buyerDeposit);
        }
        
        emit OffChainArbitrationResult(_ownerMalicious, _buyerMalicious);
    }
    
    // ===================== 工具函数 =====================
    
    // 获取合约余额
    function getContractBalance() public view returns (uint256) {
        return address(this).balance;
    }
    
    // 获取交易状态
    function getTradeStatus() public view returns (string memory) {
        if (status == TradeStatus.Created) return "Created";
        if (status == TradeStatus.Requested) return "Requested";
        if (status == TradeStatus.ProofPublished) return "ProofPublished";
        if (status == TradeStatus.DepositMade) return "DepositMade";
        if (status == TradeStatus.S2Published) return "S2Published";
        if (status == TradeStatus.Completed) return "Completed";
        if (status == TradeStatus.OnChainArbitration) return "OnChainArbitration";
        return "OffChainArbitration";
    }
    
    // 获取交易详情
    function getTradeDetails() public view returns (
        uint256 payment,
        uint256 ownerDeposit,
        uint256 buyerDeposit,
        bool ownerMalicious,
        bool buyerMalicious
    ) {
        return (
            trade.payment,
            trade.ownerDeposit,
            trade.buyerDeposit,
            trade.ownerMalicious,
            trade.buyerMalicious
        );
    }
}