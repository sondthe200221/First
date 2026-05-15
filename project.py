import tkinter as tk
from tkinter import messagebox
import pyodbc
import requests

class TrieNode:
    def __init__(self):
        self.children = {}
        self.is_end_of_word = False

class Trie:
    def __init__(self):
        self.root = TrieNode()

    def insert(self, word):
        node = self.root
        for char in word:
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
        self.is_end_of_word = True

    def search_prefix(self, prefix):
        node = self.root
        for char in prefix:
            if char not in node.children:
                return [] 
            node = node.children[char]
        results = []
        self._dfs(node, prefix, results)
        return results

    def _dfs(self, node, prefix, results):
        if len(results) >= 10:
            return
        if node.is_end_of_word:
            results.append(prefix)
        
        for char, next_node in sorted(node.children.items()):
            self._dfs(next_node, prefix + char, results)
    
conn_str = (
    "Driver={ODBC Driver 17 for SQL Server};"
    "Server=.;" 
    "Database=DictionaryDB;"
    "Trusted_Connection=yes;"
)

def load_data_to_trie():
    my_trie = Trie()
    try:
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        cursor.execute("SELECT WordText FROM Words")
        for row in cursor.fetchall():
            my_trie.insert(row[0])
        conn.close()
        print("✅ Đã nạp dữ liệu từ SQL vào cây Trie.")
    except Exception as e:
        print(f"Lỗi nạp dữ liệu: {e}")
    return my_trie

dictionary_trie = load_data_to_trie() 

def fetch_and_save_word(word):
    url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            json_data = response.text
            conn = pyodbc.connect(conn_str)
            cursor = conn.cursor()
            cursor.execute("{CALL sp_InsertDictionaryJson (?)}", (json_data,))
            conn.commit()
            conn.close()
            return True
        else:
            return False
    except pyodbc.Error as e:
        print(f"SQL Note: {e}")
        return True 
    except Exception as e:
        print(f"Error: {e}")
        return False

def suggest_words(prefix):
    return dictionary_trie.search_prefix(prefix)

def on_key_release(event):
    if event.keysym == "Return":
        handle_api_search()
        return

    value = entry.get().strip()
    listbox.delete(0, tk.END)
    
    if value != "":
        data = suggest_words(value)
        if data:
            for item in data:
                listbox.insert(tk.END, item)
        else:
            listbox.insert(tk.END, "⚠️ Nhấn Enter để tìm mới từ API...")

def handle_api_search():
    word = entry.get().strip()
    if not word: return
    
    listbox.delete(0, tk.END)
    listbox.insert(tk.END, f"🔍 Đang tìm '{word}' từ API...")
    root.update()
    
    if fetch_and_save_word(word):
        messagebox.showinfo("Thành công", f"Đã cập nhật từ '{word}' vào hệ thống!")
        on_key_release(None) 
    else:
        messagebox.showwarning("Thông báo", f"Không tìm thấy từ '{word}' trên hệ thống API.")

def on_select(event):
    if listbox.curselection():
        selected = listbox.get(listbox.curselection())
        if "⚠️" not in selected and "🔍" not in selected:
            entry.delete(0, tk.END)
            entry.insert(0, selected)


root = tk.Tk()
root.title("Từ điển thông minh (Tự cập nhật)")
root.geometry("450x550")

tk.Label(root, text="Nhập từ tiếng Anh:", font=("Arial", 11, "bold")).pack(pady=10)

entry = tk.Entry(root, font=("Arial", 14), fg="blue")
entry.pack(pady=5, padx=20, fill=tk.X)
entry.bind("<KeyRelease>", on_key_release)

listbox = tk.Listbox(root, font=("Arial", 12), height=12, fg="#333")
listbox.pack(pady=5, padx=20, fill=tk.X)
listbox.bind("<<ListboxSelect>>", on_select)

tk.Label(root, text="Mẹo: Nếu không thấy gợi ý, nhấn Enter để tải dữ liệu.", 
         font=("Arial", 9, "italic"), fg="gray").pack(pady=5)

root.mainloop()