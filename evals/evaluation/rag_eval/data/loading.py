import json

def print_json_keys(json_file):
  """
  打印JSON文件中所有的键

  Args:
    json_file: JSON文件路径
  """

  with open(json_file, 'r') as f:
    data = json.load(f)
  import pdb;pdb.set_trace()
  def traverse(data):
    if isinstance(data, dict):
      for key in data:
        print(key)
        traverse(data[key])
    elif isinstance(data, list):
      for item in data:
        traverse(item)

  traverse(data)

# 示例用法
json_file = 'single_data.json'  # 替换为你的JSON文件路径
print_json_keys(json_file)
