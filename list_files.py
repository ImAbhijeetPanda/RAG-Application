import os

def list_files(start_path='.'):
    for root, dirs, files in os.walk(start_path):
        rel_root = os.path.relpath(root, start_path)
        if rel_root == '.':
            rel_root = ''
        for d in dirs:
            print(os.path.join(rel_root, d) + '/')
        for f in files:
            print(os.path.join(rel_root, f))

if __name__ == "__main__":
    print("Project directory listing:\n")
    list_files('.')


