import hashlib
from typing import List, Optional, Tuple

class MerkleTree:
    def __init__(self, hashes: List[bytes]):
        """初始化Merkle树"""
        self.hashes = hashes
        self.tree = self._build_tree()
        
    def _build_tree(self) -> List[List[bytes]]:
        """构建完整的Merkle树，返回各层哈希列表"""
        tree = [self.hashes.copy()]
        current_level = self.hashes.copy()
        
        while len(current_level) > 1:
            next_level = []
            for i in range(0, len(current_level), 2):
                left = current_level[i]
                # 右节点存在则拼接，不存在则使用左节点
                right = current_level[i + 1] if i + 1 < len(current_level) else left
                parent_hash = self._hash_pair(left, right)
                next_level.append(parent_hash)
            tree.append(next_level)
            current_level = next_level
            
        return tree
    
    def _hash_pair(self, left: bytes, right: bytes) -> bytes:
        """计算两个哈希值的组合哈希"""
        return hashlib.sha256(left + right).digest()
    
    def get_parent_hash(self, index: int) -> Optional[Tuple[bytes, int]]:
        """
        获取指定索引哈希的父节点哈希值及父节点所在层级
        返回: (父节点哈希值, 父节点所在层级索引)
        """
        if index < 0 or index >= len(self.hashes):
            return None, -1
            
        # 第0层是原始哈希数组
        current_level = 0
        current_index = index
        
        # 如果已经是根节点，没有父节点
        if len(self.tree) == 1:
            return None, -1
            
        # 父节点在当前层的上一层
        parent_level = current_level + 1
        # 计算父节点在父层中的索引
        parent_index = current_index // 2
        
        return self.tree[parent_level][parent_index], parent_level

def main():
    # 示例：生成100个随机哈希值作为输入
    sample_hashes = [hashlib.sha256(f"file_{i}".encode()).digest() for i in range(1, 101)]
    
    # 构建Merkle树
    merkle_tree = MerkleTree(sample_hashes)
    
    while True:
        try:
            input_num = int(input("\n请输入哈希编号(1-100，0退出): "))
            if input_num == 0:
                break
            if 1 <= input_num <= 100:
                index = input_num - 1  # 转换为0-based索引
                parent_hash, level = merkle_tree.get_parent_hash(index)
                
                if parent_hash:
                    print(f"哈希 #{input_num} 的父节点哈希值:")
                    print(f"层级: {level}")
                    print(f"哈希值: {parent_hash.hex()}")
                else:
                    print(f"哈希 #{input_num} 已是根节点，没有父节点。")
            else:
                print("请输入1-100之间的数字。")
        except ValueError:
            print("输入无效，请输入数字。")

if __name__ == "__main__":
    main()    