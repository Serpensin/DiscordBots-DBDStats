import ast
import os


def remove_prints_from_line(file_path, line_number):
    with open(file_path, 'r') as f:
        tree = ast.parse(f.read())
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == 'print':
                if hasattr(node, 'lineno') and node.lineno >= line_number:
                    node_str = ast.dump(node).replace('\n', '')
                    with open(file_path, 'r') as f:
                        file_content = f.readlines()
                    file_content[node.lineno-1] = '# ' + file_content[node.lineno-1]
                    with open(file_path, 'w') as f:
                        f.writelines(file_content)
                        
                        
if __name__ == '__main__':
    file_path = os.abspath('main.py')
    line_number = 144
    remove_prints_from_line(file_path, line_number)
    
