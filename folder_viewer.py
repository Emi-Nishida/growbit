# folder_viewer.py
import os
from pathlib import Path

# フォルダパス
folder_path = r"C:\Users\emi24\Downloads\Tech0\Github\root_prod"

# 除外するフォルダ名（仮想環境など）
EXCLUDE_FOLDERS = {'.venv', 'venv', '__pycache__', '.git', 'node_modules'}

print("=" * 60)
print("📁 フォルダ情報取得ツール")
print("=" * 60)

if os.path.exists(folder_path):
    print(f"✅ フォルダが見つかりました: {folder_path}\n")
    
    folder_count = 0
    file_count = 0
    
    print("📂 フォルダ・ファイル情報（.venvなど除外）")
    print("-" * 60)
    
    for root, dirs, files in os.walk(folder_path):
        # 除外フォルダをスキップ
        dirs[:] = [d for d in dirs if d not in EXCLUDE_FOLDERS]
        
        folder_count += len(dirs)
        file_count += len(files)
        
        rel_path = os.path.relpath(root, folder_path)
        if rel_path == ".":
            print(f"\n📁 [ルート]")
        else:
            print(f"\n📁 {rel_path}")
        
        if dirs:
            print("  └ フォルダ:")
            for d in dirs:
                print(f"    📁 {d}")
        
        if files:
            print("  └ ファイル:")
            for f in files:
                file_path = os.path.join(root, f)
                try:
                    file_size = os.path.getsize(file_path)
                    print(f"    📄 {f} ({file_size:,} bytes)")
                except:
                    print(f"    📄 {f}")
    
    print("\n" + "=" * 60)
    print(f"📊 合計: {folder_count}個のフォルダ、{file_count}個のファイル")
    print("=" * 60)
    
    # ツリー構造（簡易版）
    print("\n🌳 フォルダツリー構造（.venv除外）")
    print("-" * 60)
    
    path = Path(folder_path)
    
    def print_tree(directory, prefix="", is_last=True, depth=0, max_depth=3):
        """ツリー構造で表示（深さ制限付き）"""
        if depth > max_depth:
            return
            
        try:
            contents = sorted(directory.iterdir(), key=lambda x: (x.is_file(), x.name))
            # 除外フォルダをフィルタ
            contents = [c for c in contents if c.name not in EXCLUDE_FOLDERS]
        except PermissionError:
            return
        
        for i, item in enumerate(contents):
            is_last_item = i == len(contents) - 1
            
            if item.is_dir():
                print(f"{prefix}{'└── ' if is_last_item else '├── '}📁 {item.name}")
                extension = "    " if is_last_item else "│   "
                print_tree(item, prefix + extension, is_last_item, depth + 1, max_depth)
            else:
                print(f"{prefix}{'└── ' if is_last_item else '├── '}📄 {item.name}")
    
    print(f"📁 {path.name}")
    print_tree(path)

else:
    print(f"❌ フォルダが見つかりません: {folder_path}")

print("\n💡 除外されたフォルダ:", ", ".join(EXCLUDE_FOLDERS))