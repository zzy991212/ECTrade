# ECTrade: An Efficient and Credible Scheme for Blockchain-based Data Trading

This repository contains the reproducible implementation of the ECTrade scheme proposed in our VLDB 2026 paper: ECTrade: An Efficient and Credible Scheme for Blockchain-based Data Trading.

📄 Paper Link: [VLDB 2026 Submission]
⚠️ This repository focuses exclusively on experiment reproduction. For theoretical details, please refer to the original paper.

📋 Environment Requirements
All experiments are conducted under the following exact environment. Deviations may lead to inconsistent results.

| Component | Recommended Version | Description |
|----------|---------------------|-------------|
| Python | 3.8 ~ 3.10 | Core programming environment |
| Charm-Crypto | 0.50 | Cryptographic library for pairing-based cryptography |
| Solidity | 0.8.19 | Smart contract language |
| IPFS | 0.28.0+ | Decentralized data storage |
| Ganache CLI | latest | Local Ethereum test chain |
| Node.js | 16.x+ | For contract deployment & testing |
| Linux System | Ubuntu 18.04 / 20.04 | Recommended operating system |

📁 Code Structure
```
├── 📁 contracts (smart contracts for 3 schemes)
├── 📁 experiment (experiment codes, datas, figure codes)
├── 📁 fairswap (Fairswap)
├── 📁 infocom (NRDT)
├── 📁 ourplan (ECTrade)
├── 📁 PyFHE-master (FHE test codes from github)
├── 📁 util (some utils)
├── 📜 README.md 
```

🚀 How to Start?
1. Clone the Repository
```bash
git clone https://github.com/zzy991212/ECTrade.git
cd ECTrade
```
2. Install Dependencies and Environment components from Internet

3. Run the relevant code according to the paper's workflow
- Authentication Phase

    1. Generate `pk`,`sk` of DP and DC, set global parameters *by yourself*.

- Preparation Phase

    1. Use a `.txt` file, encrypt it through the `PRE` module, divid it into several blocks and caculate the merkle root, store these in IPFS.
    2. Update messages in `DataStore` contract, deploy it in `eth` private chain *(you can also deploy it in public chain)*.
    3. Wait for sample revelation, and caculate the sample block through `OSS` algorithm, update messages in the contract, store these in IPFS.

- Trade Phase

    1.Deploy the `DataExchange` contract, execute workflow.

- Arbitration Phase

    1.Simulate *by yourself*.



📄 License
This code is released under the CC BY-NC-ND 4.0 license, same as the original paper. For commercial use, please contact the authors.
