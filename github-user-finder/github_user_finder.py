import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
import requests
import threading

class GitHubUserFinder:
    def __init__(self, root):
        self.root = root
        self.root.title("GitHub User Finder - Поиск пользователей")
        self.root.geometry("850x600")
        self.root.resizable(True, True)
        
        # Данные
        self.favorites = []
        self.current_user = None
        self.load_favorites()
        
        # --- Верхняя панель поиска ---
        search_frame = tk.Frame(root)
        search_frame.pack(pady=10, padx=10, fill="x")
        
        tk.Label(search_frame, text="Поиск пользователя GitHub:", font=("Arial", 12)).pack(side="left")
        
        self.search_entry = tk.Entry(search_frame, font=("Arial", 12), width=30)
        self.search_entry.pack(side="left", padx=10)
        self.search_entry.bind("<Return>", lambda e: self.search_user())
        
        self.search_btn = tk.Button(search_frame, text="🔍 Найти", command=self.search_user, bg="lightblue", font=("Arial", 10))
        self.search_btn.pack(side="left", padx=5)
        
        # --- Статус ---
        self.status_label = tk.Label(root, text="Введите имя пользователя для поиска", fg="gray")
        self.status_label.pack(pady=5)
        
        # --- Основная область (две колонки) ---
        main_frame = tk.Frame(root)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Левая колонка - результаты поиска
        left_frame = tk.LabelFrame(main_frame, text="📋 Результаты поиска", padx=5, pady=5)
        left_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))
        
        # Таблица результатов
        columns = ("Логин", "ID", "Тип", "Ссылка")
        self.result_tree = ttk.Treeview(left_frame, columns=columns, show="headings", height=15)
        self.result_tree.heading("Логин", text="Логин")
        self.result_tree.heading("ID", text="ID")
        self.result_tree.heading("Тип", text="Тип")
        self.result_tree.heading("Ссылка", text="Ссылка")
        self.result_tree.column("Логин", width=120)
        self.result_tree.column("ID", width=80)
        self.result_tree.column("Тип", width=80)
        self.result_tree.column("Ссылка", width=200)
        self.result_tree.pack(fill="both", expand=True)
        
        # Кнопка добавления в избранное
        add_fav_btn = tk.Button(left_frame, text="⭐ Добавить в избранное", command=self.add_to_favorites, bg="lightgreen", font=("Arial", 10))
        add_fav_btn.pack(pady=5)
        
        # Правая колонка - избранное
        right_frame = tk.LabelFrame(main_frame, text="⭐ Избранные пользователи", padx=5, pady=5)
        right_frame.pack(side="right", fill="both", expand=True, padx=(5, 0))
        
        # Таблица избранных
        fav_columns = ("Логин", "ID", "Ссылка")
        self.fav_tree = ttk.Treeview(right_frame, columns=fav_columns, show="headings", height=15)
        self.fav_tree.heading("Логин", text="Логин")
        self.fav_tree.heading("ID", text="ID")
        self.fav_tree.heading("Ссылка", text="Ссылка")
        self.fav_tree.column("Логин", width=120)
        self.fav_tree.column("ID", width=80)
        self.fav_tree.column("Ссылка", width=200)
        self.fav_tree.pack(fill="both", expand=True)
        
        # Кнопка удаления из избранного
        remove_fav_btn = tk.Button(right_frame, text="❌ Удалить из избранного", command=self.remove_from_favorites, bg="lightcoral", font=("Arial", 10))
        remove_fav_btn.pack(pady=5)
        
        # --- Нижняя панель ---
        bottom_frame = tk.Frame(root)
        bottom_frame.pack(pady=10, fill="x")
        
        self.save_btn = tk.Button(bottom_frame, text="💾 Сохранить избранное в JSON", command=self.save_favorites, bg="lightyellow", font=("Arial", 10))
        self.save_btn.pack(side="left", padx=5)
        
        self.load_btn = tk.Button(bottom_frame, text="📂 Загрузить избранное из JSON", command=self.load_favorites, bg="lightyellow", font=("Arial", 10))
        self.load_btn.pack(side="left", padx=5)
        
        self.clear_btn = tk.Button(bottom_frame, text="🗑️ Очистить избранное", command=self.clear_favorites, bg="lightcoral", font=("Arial", 10))
        self.clear_btn.pack(side="left", padx=5)
        
        # Обновляем отображение избранных
        self.update_favorites_display()
    
    def search_user(self):
        """Поиск пользователя через GitHub API"""
        username = self.search_entry.get().strip()
        
        # Валидация
        if not username:
            messagebox.showerror("Ошибка", "Поле поиска не может быть пустым!")
            return
        
        self.status_label.config(text=f"Поиск пользователя '{username}'...", fg="orange")
        self.search_btn.config(state="disabled")
        
        # Запускаем поиск в отдельном потоке
        thread = threading.Thread(target=self._search_api, args=(username,))
        thread.daemon = True
        thread.start()
    
    def _search_api(self, username):
        """Выполнение API запроса к GitHub"""
        try:
            url = f"https://api.github.com/users/{username}"
            headers = {"Accept": "application/vnd.github.v3+json"}
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                user_data = response.json()
                self.root.after(0, self.display_user, user_data)
                self.root.after(0, lambda: self.status_label.config(text=f"✅ Найден пользователь: {user_data['login']}", fg="green"))
            elif response.status_code == 404:
                self.root.after(0, lambda: messagebox.showerror("Ошибка", f"Пользователь '{username}' не найден!"))
                self.root.after(0, lambda: self.status_label.config(text="❌ Пользователь не найден", fg="red"))
            else:
                self.root.after(0, lambda: messagebox.showerror("Ошибка", f"Ошибка API: {response.status_code}"))
                self.root.after(0, lambda: self.status_label.config(text="❌ Ошибка API", fg="red"))
        except requests.exceptions.RequestException as e:
            self.root.after(0, lambda: messagebox.showerror("Ошибка", f"Ошибка сети: {str(e)}"))
            self.root.after(0, lambda: self.status_label.config(text="❌ Ошибка сети", fg="red"))
        finally:
            self.root.after(0, lambda: self.search_btn.config(state="normal"))
    
    def display_user(self, user_data):
        """Отображение найденного пользователя в таблице"""
        # Очищаем предыдущие результаты
        for row in self.result_tree.get_children():
            self.result_tree.delete(row)
        
        # Добавляем пользователя
        self.result_tree.insert("", tk.END, values=(
            user_data.get("login", "N/A"),
            user_data.get("id", "N/A"),
            user_data.get("type", "N/A"),
            user_data.get("html_url", "N/A")
        ))
        
        # Сохраняем данные пользователя для добавления в избранное
        self.current_user = user_data
    
    def add_to_favorites(self):
        """Добавление выбранного пользователя в избранное"""
        if not self.current_user:
            messagebox.showwarning("Внимание", "Сначала найдите пользователя!")
            return
        
        # Проверяем, не добавлен ли уже
        for fav in self.favorites:
            if fav["login"] == self.current_user["login"]:
                messagebox.showinfo("Информация", f"Пользователь {self.current_user['login']} уже в избранном!")
                return
        
        # Добавляем в избранное
        fav_data = {
            "login": self.current_user["login"],
            "id": self.current_user["id"],
            "url": self.current_user["html_url"],
            "type": self.current_user.get("type", "")
        }
        self.favorites.append(fav_data)
        self.update_favorites_display()
        self.save_favorites()
        messagebox.showinfo("Успех", f"Пользователь {self.current_user['login']} добавлен в избранное!")
    
    def remove_from_favorites(self):
        """Удаление выбранного пользователя из избранного"""
        selection = self.fav_tree.selection()
        if not selection:
            messagebox.showwarning("Внимание", "Выберите пользователя в списке избранных!")
            return
        
        item = self.fav_tree.item(selection[0])
        login = item["values"][0]
        
        self.favorites = [fav for fav in self.favorites if fav["login"] != login]
        self.update_favorites_display()
        self.save_favorites()
        messagebox.showinfo("Успех", f"Пользователь {login} удалён из избранного!")
    
    def update_favorites_display(self):
        """Обновление таблицы избранных"""
        for row in self.fav_tree.get_children():
            self.fav_tree.delete(row)
        
        for fav in self.favorites:
            self.fav_tree.insert("", tk.END, values=(
                fav["login"],
                fav["id"],
                fav["url"]
            ))
    
    def save_favorites(self):
        """Сохранение избранных в JSON файл"""
        try:
            with open("favorites.json", "w", encoding="utf-8") as f:
                json.dump(self.favorites, f, ensure_ascii=False, indent=4)
            self.status_label.config(text="✅ Избранное сохранено в favorites.json", fg="green")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить: {e}")
    
    def load_favorites(self):
        """Загрузка избранных из JSON файла"""
        if not os.path.exists("favorites.json"):
            messagebox.showinfo("Информация", "Файл favorites.json не найден")
            return
        
        try:
            with open("favorites.json", "r", encoding="utf-8") as f:
                self.favorites = json.load(f)
            self.update_favorites_display()
            self.status_label.config(text="✅ Избранное загружено из favorites.json", fg="green")
            messagebox.showinfo("Успех", f"Загружено {len(self.favorites)} пользователей!")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить: {e}")
    
    def clear_favorites(self):
        """Очистка всего списка избранных"""
        if messagebox.askyesno("Подтверждение", "Вы уверены, что хотите очистить весь список избранных?"):
            self.favorites = []
            self.update_favorites_display()
            self.save_favorites()
            messagebox.showinfo("Успех", "Список избранных очищен!")

if __name__ == "__main__":
    # Проверка установки библиотек
    try:
        import requests
    except ImportError:
        import subprocess
        subprocess.check_call(["pip", "install", "requests"])
        import requests
    
    root = tk.Tk()
    app = GitHubUserFinder(root)
    root.mainloop()