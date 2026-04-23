//SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

contract DataStore {
    enum State {
        UNINIT,
        INIT,
        ACTIVE
    }

    address public immutable producer;
    string public dataProducerPublicKey;
    string public description;
    uint256 public price;
    uint256 public totalBlocks;
    
    string public encryptedDataCID;
    string public sharesFolderCID;
    
    bytes32 public merkleRoot;
    bytes32 public sampleCommitment;

    uint256 public immutable deploymentHeight;
    uint256 public immutable kAfter;
    uint256 public constant MAX_K_AFTER = 100;
    
    bytes32 public randomSeed;
    uint256 public sampleIndex;
    bool public isRevealed;

    bytes32 public reqID;

    State public state;

    event ContractDeployed(
        bytes32 indexed reqID,
        address indexed producer,
        uint256 deploymentHeight,
        uint256 totalBlocks,
        uint256 kAfter
    );
    
    event SampleRevealed(
        bytes32 indexed reqID,
        uint256 sampleIndex,
        bytes32 randomSeed,
        uint256 revealHeight
    );
    
    event Finalized(
        bytes32 indexed reqID,
        string sharesFolderCID,
        bytes32 sampleCommitment,
        uint256 finalizeHeight
    );

    modifier onlyProducer() {
        require(msg.sender == producer, "Only producer can call");
        _;
    }

    modifier atState(State _state) {
        require(state == _state, "Invalid state");
        _;
    }

    constructor(
        string memory _pkDP,
        string memory _description,
        uint256 _price,
        uint256 _totalBlocks,
        string memory _encryptedDataCID,
        bytes32 _merkleRoot,
        uint256 _kAfter,
        uint256 _nonce
    ) {
        require(_totalBlocks > 0, "Total blocks must be > 0");
        require(_kAfter > 0 && _kAfter <= MAX_K_AFTER, "Invalid kAfter");
        require(bytes(_encryptedDataCID).length > 0, "Empty CID");
        
        producer = msg.sender;
        
        dataProducerPublicKey = _pkDP;
        description = _description;
        price = _price;
        totalBlocks = _totalBlocks;
        encryptedDataCID = _encryptedDataCID;
        merkleRoot = _merkleRoot;
        
        deploymentHeight = block.number;
        kAfter = _kAfter;
        
        reqID = keccak256(abi.encodePacked(_pkDP, block.number, _nonce));
        
        state = State.INIT;
        isRevealed = false;
        
        emit ContractDeployed(reqID, producer, deploymentHeight, totalBlocks, kAfter);
    }

    function reveal() external atState(State.INIT) returns (uint256) {
        require(block.number >= deploymentHeight + kAfter, "Too early to reveal");
        require(!isRevealed, "Already revealed");
        
        bytes32 seed = bytes32(0);
        
        for (uint256 i = 1; i <= kAfter; i++) {
            uint256 targetBlock = deploymentHeight + i;
            
            require(block.number - targetBlock < 256, "Block too old to retrieve hash");
            
            bytes32 blockHash = blockhash(targetBlock);
            require(blockHash != bytes32(0), "Block hash not available");
            
            seed = seed ^ blockHash;
        }
        
        randomSeed = seed;
        
        sampleIndex = uint256(seed) % totalBlocks;
        isRevealed = true;
        
        emit SampleRevealed(reqID, sampleIndex, randomSeed, block.number);
        
        return sampleIndex;
    }

    function finalize(
        string memory _sharesFolderCID,
        bytes32 _sampleCommitment
    ) external onlyProducer atState(State.INIT) {
        require(isRevealed, "Must reveal first");
        require(bytes(_sharesFolderCID).length > 0, "Empty shares CID");
        require(_sampleCommitment != bytes32(0), "Empty commitment");
        
        sharesFolderCID = _sharesFolderCID;
        sampleCommitment = _sampleCommitment;
        
        state = State.ACTIVE;
        
        emit Finalized(reqID, _sharesFolderCID, _sampleCommitment, block.number);
    }

    function getStatus() external view returns (
        State currentState,
        uint256 currentBlock,
        bool canReveal,
        bool canFinalize
    ) {
        currentState = state;
        currentBlock = block.number;
        canReveal = (state == State.INIT) && 
                    (block.number >= deploymentHeight + kAfter) && 
                    !isRevealed &&
                    (block.number - (deploymentHeight + kAfter) < 256);
        canFinalize = (state == State.INIT) && isRevealed;
    }

    function getRandomnessParams() external view returns (
        uint256 _deploymentHeight,
        uint256 _kAfter,
        uint256 _targetRevealBlock,
        bytes32 _randomSeed,
        uint256 _sampleIndex
    ) {
        return (
            deploymentHeight,
            kAfter,
            deploymentHeight + kAfter,
            randomSeed,
            sampleIndex
        );
    }
}

contract DataExchange {
    DataStore public immutable dataStore;

    enum State { Created, Requested, SampleSent, SampleVerified, ReKeySent, AwaitingCompletion, Arbitration, Completed, Aborted }
    State public state;

    address public consumer;
    string public consumerPublicKey;

    uint256 public producerDeposit;
    uint256 public consumerDeposit;

    bytes public encryptedSample;
    bytes public reKey;
    uint256 public sampleSentTime;
    uint256 public reKeySentTime;
    uint256 public dataExtractedTimestamp;
    uint256 public arbitrationStartTime;

    uint256 public constant VERIFY_PERIOD = 5 minutes;
    uint256 public constant FINAL_CONFIRM_PERIOD = 5 minutes;
    uint256 public constant ARBITRATION_PERIOD = 3 days;

    event DataRequested(address indexed consumer, uint256 payment, uint256 deposit);
    event SampleSent();
    event SampleVerified(bool isValid);
    event ReKeySent();
    event DataExtractionReported(address indexed reporter, bool success);
    event FinalConfirmation();
    event ArbitrationInitiated(address indexed initiator, string reason);
    event ArbitrationResolved(bool sellerWins);
    event MerkleProofVerified(address indexed verifier, bool isValid);
    event TransactionCompleted();
    event TransactionAborted(string reason);
    event DepositRefunded(address indexed recipient, uint256 amount);

    error InvalidDataStoreAddress();
    error ZeroDeposit();
    error Unauthorized();
    error InvalidState();
    error InvalidValue();
    error Timeout();
    error InvalidProofLength(uint256 expected, uint256 actual);

    modifier onlyProducer() {
        if (msg.sender != dataStore.producer()) revert Unauthorized();
        _;
    }

    modifier onlyConsumer() {
        if (msg.sender != consumer) revert Unauthorized();
        _;
    }

    modifier inState(State _state) {
        if (state != _state) revert InvalidState();
        _;
    }

    constructor(address _dataStore) payable {
        if (_dataStore == address(0)) revert InvalidDataStoreAddress();
        if (msg.value == 0) revert ZeroDeposit();
        dataStore = DataStore(_dataStore);
        producerDeposit = msg.value;
    }

    function requestData(string calldata _consumerPk) external payable inState(State.Created) {
        uint256 dataPrice = dataStore.price();
        uint256 requiredAmount = dataPrice + producerDeposit;
        require(msg.value == requiredAmount, "Invalid payment amount");
        
        consumer = msg.sender;
        consumerPublicKey = _consumerPk;
        consumerDeposit = producerDeposit;
        state = State.Requested;
        emit DataRequested(msg.sender, dataPrice, consumerDeposit);
    }

    function sendSample(bytes calldata _encryptedSample) external onlyProducer inState(State.Requested) {
        require(_encryptedSample.length > 0, "Invalid sample data");
        encryptedSample = _encryptedSample;
        sampleSentTime = block.timestamp;
        state = State.SampleSent;
        emit SampleSent();
    }

    function verifySample(bool _valid) external onlyConsumer inState(State.SampleSent) {
        require(block.timestamp <= sampleSentTime + VERIFY_PERIOD, "Verification period expired");
        
        if (!_valid) {
            refundDeposit(dataStore.producer(), producerDeposit);
            _abort("Sample verification failed");
            return;
        }
        
        state = State.SampleVerified;
        emit SampleVerified(true);
    }

    function sendReKey(bytes calldata _reKey) external onlyProducer inState(State.SampleVerified) {
        require(_reKey.length > 0, "Invalid re-encryption key");
        reKey = _reKey;
        reKeySentTime = block.timestamp;
        state = State.ReKeySent;
        emit ReKeySent();
    }

    function reportDataExtraction(bool success) external onlyConsumer inState(State.ReKeySent) {
        if (success) {
            state = State.AwaitingCompletion;
            dataExtractedTimestamp = block.timestamp;
            emit DataExtractionReported(msg.sender, true);
        } else {
            state = State.Arbitration;
            arbitrationStartTime = block.timestamp;
            emit DataExtractionReported(msg.sender, false);
            emit ArbitrationInitiated(msg.sender, "Data extraction failed");
        }
    }

    function confirmFinalReceipt() external onlyConsumer inState(State.AwaitingCompletion) {
        require(block.timestamp <= dataExtractedTimestamp + FINAL_CONFIRM_PERIOD, "Final confirmation period expired");
        
        uint256 totalAmount = dataStore.price() + producerDeposit + consumerDeposit;
        (bool success, ) = payable(dataStore.producer()).call{value: totalAmount}("");
        require(success, "Payment to producer failed");
        
        state = State.Completed;
        emit FinalConfirmation();
        emit TransactionCompleted();
    }

    function calculateTreeHeight(uint256 leafCount) public pure returns (uint256) {
        if (leafCount <= 1) {
            return 0;
        }
        uint256 height = 0;
        uint256 current = 1;
        
        while (current < leafCount) {
            height++;
            current *= 2;
        }
        return height;
    }

    function submitAndVerifyMerkleProof(bytes32[] calldata proof) external onlyProducer inState(State.Arbitration) {
        require(block.timestamp <= arbitrationStartTime + ARBITRATION_PERIOD, "Arbitration period expired");
        
        uint256 leafCount = dataStore.totalBlocks(); 
        
        uint256 expectedLength = calculateTreeHeight(leafCount);
        
        if (proof.length != expectedLength) {
            revert InvalidProofLength(expectedLength, proof.length);
        }
        
        bool isValid = verifyMerkleProofInternal(
            dataStore.merkleRoot(), 
            dataStore.sampleCommitment(), 
            dataStore.sampleIndex(), 
            proof
        );
        
        if (isValid) {
            _completeTransaction();
            emit ArbitrationResolved(true);
        } else {
            _abortTransaction("Merkle proof verification failed");
            emit ArbitrationResolved(false);
        }
        
        emit MerkleProofVerified(msg.sender, isValid);
    }

    function verifyMerkleProofInternal(
        bytes32 root,
        bytes32 leaf,
        uint256 index,
        bytes32[] memory proof
    ) internal pure returns (bool) {
        bytes32 computedHash = leaf;
        
        for (uint256 i = 0; i < proof.length; i++) {
            if (index % 2 == 0) {
                computedHash = keccak256(abi.encodePacked(computedHash, proof[i]));
            } else {
                computedHash = keccak256(abi.encodePacked(proof[i], computedHash));
            }
            index = index / 2;
        }
        
        return computedHash == root;
    }

    function abortOnTimeout() external {
        if (state == State.SampleSent && block.timestamp > sampleSentTime + VERIFY_PERIOD) {
            refundDeposit(consumer, consumerDeposit + dataStore.price());
            refundDeposit(dataStore.producer(), producerDeposit);
            _abort("Sample verification timeout");
        } else if (state == State.ReKeySent && block.timestamp > reKeySentTime + FINAL_CONFIRM_PERIOD) {
            refundDeposit(consumer, consumerDeposit + dataStore.price());
            refundDeposit(dataStore.producer(), producerDeposit);
            _abort("Final confirmation timeout");
        } else if (state == State.Arbitration && block.timestamp > arbitrationStartTime + ARBITRATION_PERIOD) {
            refundDeposit(consumer, consumerDeposit + dataStore.price());
            refundDeposit(dataStore.producer(), producerDeposit);
            _abort("Arbitration timeout");
        } else {
            revert InvalidState();
        }
    }

    function refundDeposit(address recipient, uint256 amount) private {
        (bool success, ) = payable(recipient).call{value: amount}("");
        require(success, "Refund failed");
        emit DepositRefunded(recipient, amount);
    }

    function _completeTransaction() private {
        uint256 totalAmount = dataStore.price() + producerDeposit + consumerDeposit;
        (bool success, ) = payable(dataStore.producer()).call{value: totalAmount}("");
        require(success, "Payment to producer failed");
        
        state = State.Completed;
        emit TransactionCompleted();
    }

    function _abortTransaction(string memory reason) private {
        state = State.Aborted;
        emit TransactionAborted(reason);
    }

    function _abort(string memory reason) private {
        state = State.Aborted;
        emit TransactionAborted(reason);
    }
}