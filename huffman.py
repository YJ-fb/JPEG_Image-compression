from tqdm import tqdm
from typing import Dict, List, Tuple

def int_to_bytes(n: int) -> bytes:
    """返回整数对应的二进制比特串 例如 50 -> b'\x50'"""
    return bytes([n])

def bytes_to_int(b: bytes) -> int:
    """返回比特串对应的整数 例如 b'\x50' -> 50"""
    return b[0]

def bytes_fre(bytes_str: bytes):
    """统计目标文本的字符频数, 返回频数字典
    例如b'\x4F\x56\x4F' -> {b'\x4F':2, b'\x56':1}
    """
    fre_dic = [0 for _ in range(256)]
    for item in bytes_str:
        fre_dic[item] += 1
    return {int_to_bytes(x): fre_dic[x] for x in range(256) if fre_dic[x] != 0}

class Node:
    """Node结点，用于构建二叉数"""
    def __init__(self, value, weight, lchild, rchild):
        self.value = value
        self.weight = weight
        self.lchild = lchild
        self.rchild = rchild

    def build(fre_dic: Dict[bytes, int]) -> Dict[bytes, str]:
        """通过字典构建Huffman编码，返回对应的编码字典
        例如 {b'\x4F':1, b'\x56':1} -> {b'\x4F':'0', b'\x56':'1'}
        """

        def dlr(current: Node, huffman_code: str, _huffman_dic: Dict[bytes, str]):
            """递归遍历二叉树求对应的Huffman编码"""
            if current is None:
                return
            else:
                if current.lchild is None and current.rchild is None:
                    _huffman_dic[current.value] = huffman_code
                else:
                    dlr(current.lchild, huffman_code + '0', _huffman_dic)
                    dlr(current.rchild, huffman_code + '1', _huffman_dic)

        if not fre_dic:
            return {}
        elif len(fre_dic) == 1:
            return {value: '0' for value in fre_dic.keys()}
        # 初始化森林, 权重weight小的在后
        node_lst = [Node(value, weight, None, None) for value, weight in fre_dic.items()]
        node_lst.sort(key=lambda item: item.weight, reverse=True)
        # 构建Huffman树
        while len(node_lst) > 1:
            # 合并最后两棵树
            node_2 = node_lst.pop()
            node_1 = node_lst.pop()
            node_add = Node(None, node_1.weight + node_2.weight, node_1, node_2)
            node_lst.append(node_add)
            # 调整森林
            index = len(node_lst) - 1
            while index and node_lst[index - 1].weight <= node_add.weight:
                node_lst[index] = node_lst[index - 1]
                index = index - 1
            node_lst[index] = node_add
        # 获取Huffman编码
        huffman_dic = {key: '' for key in fre_dic.keys()}
        dlr(node_lst[0], '', huffman_dic)
        return huffman_dic

    def encode(str_bytes: bytes, huffman_dic: Dict[bytes, str], visualize: bool = False) -> Tuple[bytes, int]:
        """Huffman编码
        输入待编码文本, Huffman字典huffman_dic
        返回末端填充位数padding和编码后的文本
        """
        bin_buffer = ''
        padding = 0
        # 生成整数->bytes的字典
        dic = [int_to_bytes(item) for item in range(256)]
        # 将bytes字符串转化成bytes列表
        read_buffer = [dic[item] for item in str_bytes]
        write_buffer = bytearray([])
        # 循环读入数据，同时编码输出
        for item in tqdm(read_buffer, unit='byte', disable=not visualize):
            bin_buffer = bin_buffer + huffman_dic[item]
            while len(bin_buffer) >= 8:
                write_buffer.append(int(bin_buffer[:8:], 2))
                bin_buffer = bin_buffer[8::]

        # 将缓冲区内的数据填充后输出
        if bin_buffer:
            padding = 8 - len(bin_buffer)
            bin_buffer = bin_buffer.ljust(8, '0')
            write_buffer.append(int(bin_buffer, 2))

        return bytes(write_buffer), padding
    def decode(str_bytes: bytes, huffman_dic: Dict[bytes, str], padding: int, visualize: bool = False):
        """Huffman解码
        输入待编码文本, Huffman字典huffman_dic, 末端填充位padding
        返回编码后的文本
        """
        if not huffman_dic:  # 空字典，直接返回
            return b''
        elif len(huffman_dic) == 1:  # 字典长度为1，添加冗余结点，使之后续能够正常构建码树
            huffman_dic[b'OVO'] = 'OVO'
        # 初始化森林, 短码在前，长码在后, 长度相等的码字典序小的在前
        node_lst = [Node(value, weight, None, None) for value, weight in huffman_dic.items()]
        node_lst.sort(key=lambda _item: (len(_item.weight), _item.weight), reverse=False)
        # 构建Huffman树
        while len(node_lst) > 1:
            # 合并最后两棵树
            node_2 = node_lst.pop()
            node_1 = node_lst.pop()
            node_add = Node(None, node_1.weight[:-1:], node_1, node_2)
            node_lst.append(node_add)
            # 调整森林
            node_lst.sort(key=lambda _item: (len(_item.weight), _item.weight), reverse=False)
        # 解密文本
        read_buffer, buffer_size = [], 0
        # 生成字符->二进制列表的映射
        dic = [list(map(int, bin(item)[2::].rjust(8, '0'))) for item in range(256)]
        # 将str_bytes转化为二进制列表
        for item in str_bytes:
            read_buffer.extend(dic[item])
            buffer_size = buffer_size + 8
        read_buffer = read_buffer[0: buffer_size - padding:]
        buffer_size = buffer_size - padding
        write_buffer = bytearray([])

        current = node_lst[0]

        for pos in tqdm(range(0, buffer_size, 8), unit='byte', disable=not visualize):
            for item in read_buffer[pos:pos + 8]:
                # 根据二进制数移动current
                if item:
                    current = current.rchild
                else:
                    current = current.lchild
                # 到达叶结点，打印字符并重置current
                if current.lchild is None and current.rchild is None:
                    write_buffer.extend(current.value)
                    current = node_lst[0]

        return bytes(write_buffer)
