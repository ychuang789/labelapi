import re

string = 'efiin;o3284劉先生 Wirjn星期一'
pattern = '\d'

if __name__ == '__main__':
    result = re.findall(pattern, string)
    print(result)
