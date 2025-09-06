import tkinter as tk
from tkinter import ttk
import subprocess
import os
import json
from threading import Thread
import time

# Размеры планшета
TABLET_WIDTH_MM = 121.9
TABLET_HEIGHT_MM = 76.2

# Имена устройств xinput из вашего вывода
STYLUS_NAME = "HUION H420 Pen Pen (0)"
PAD_NAME = "HUION H420 Pad"

# Масштаб GUI
SCALE = 4

# Config file
CONFIG_FILE = "huion_config.json"

class HuionConfigurator:
    def __init__(self, root):
        self.root = root
        self.root.title("Настройка Huion H420")

        self.load_config()

        # Tabs
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill="both", expand=True)

        # Tab1: Рабочая область
        self.tab_area = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_area, text="Рабочая область")

        # Canvas для отображения области
        self.canvas = tk.Canvas(self.tab_area, width=TABLET_WIDTH_MM * SCALE, height=TABLET_HEIGHT_MM * SCALE, bg="white")
        self.canvas.pack(pady=10)

        self.canvas.create_rectangle(0, 0, TABLET_WIDTH_MM * SCALE, TABLET_HEIGHT_MM * SCALE, outline="black", dash=(2,2))
        self.rect_x1 = self.config.get("left", 0) * SCALE
        self.rect_y1 = self.config.get("top", 0) * SCALE
        self.rect_x2 = self.config.get("right", TABLET_WIDTH_MM) * SCALE
        self.rect_y2 = self.config.get("bottom", TABLET_HEIGHT_MM) * SCALE
        self.rect = self.canvas.create_rectangle(self.rect_x1, self.rect_y1, self.rect_x2, self.rect_y2, outline="blue", width=2)

        self.handles = []
        self.create_handles()

        self.selected_handle = None
        self.canvas.bind("<Button-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)

        # Поля для числового ввода
        input_frame = ttk.Frame(self.tab_area)
        input_frame.pack(pady=10)

        tk.Label(input_frame, text="Left (mm):").grid(row=0, column=0, padx=5, pady=2)
        self.left_entry = tk.Entry(input_frame, width=8)
        self.left_entry.insert(0, self.config.get("left", 0))
        self.left_entry.grid(row=0, column=1, padx=5, pady=2)
        self.left_entry.bind("<Return>", lambda e: self.update_from_entries())

        tk.Label(input_frame, text="Top (mm):").grid(row=0, column=2, padx=5, pady=2)
        self.top_entry = tk.Entry(input_frame, width=8)
        self.top_entry.insert(0, self.config.get("top", 0))
        self.top_entry.grid(row=0, column=3, padx=5, pady=2)
        self.top_entry.bind("<Return>", lambda e: self.update_from_entries())

        tk.Label(input_frame, text="Right (mm):").grid(row=1, column=0, padx=5, pady=2)
        self.right_entry = tk.Entry(input_frame, width=8)
        self.right_entry.insert(0, self.config.get("right", TABLET_WIDTH_MM))
        self.right_entry.grid(row=1, column=1, padx=5, pady=2)
        self.right_entry.bind("<Return>", lambda e: self.update_from_entries())

        tk.Label(input_frame, text="Bottom (mm):").grid(row=1, column=2, padx=5, pady=2)
        self.bottom_entry = tk.Entry(input_frame, width=8)
        self.bottom_entry.insert(0, self.config.get("bottom", TABLET_HEIGHT_MM))
        self.bottom_entry.grid(row=1, column=3, padx=5, pady=2)
        self.bottom_entry.bind("<Return>", lambda e: self.update_from_entries())

        update_btn = tk.Button(input_frame, text="Обновить область", command=self.update_from_entries)
        update_btn.grid(row=2, column=0, columnspan=4, pady=5)

        # Tab2: Настройки кнопок
        self.tab_buttons = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_buttons, text="Настройки кнопок")

        # Express keys (3 кнопки на планшете)
        tk.Label(self.tab_buttons, text="Кнопка 1 на планшете:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.key1_var = tk.StringVar(value=self.config.get("key1", "Ctrl+Z"))
        key1_combo = ttk.Combobox(self.tab_buttons, textvariable=self.key1_var, width=15)
        key1_combo['values'] = ('Ctrl+Z', 'Ctrl+Y', 'Ctrl+C', 'Ctrl+V', 'Ctrl+S', 'Alt', 'Shift', 'Enter', 'Escape')
        key1_combo.grid(row=0, column=1, padx=5, pady=2)

        tk.Label(self.tab_buttons, text="Кнопка 2 на планшете:").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        self.key2_var = tk.StringVar(value=self.config.get("key2", "Ctrl+Y"))
        key2_combo = ttk.Combobox(self.tab_buttons, textvariable=self.key2_var, width=15)
        key2_combo['values'] = ('Ctrl+Z', 'Ctrl+Y', 'Ctrl+C', 'Ctrl+V', 'Ctrl+S', 'Alt', 'Shift', 'Enter', 'Escape')
        key2_combo.grid(row=1, column=1, padx=5, pady=2)

        tk.Label(self.tab_buttons, text="Кнопка 3 на планшете:").grid(row=2, column=0, sticky="w", padx=5, pady=2)
        self.key3_var = tk.StringVar(value=self.config.get("key3", "Alt"))
        key3_combo = ttk.Combobox(self.tab_buttons, textvariable=self.key3_var, width=15)
        key3_combo['values'] = ('Ctrl+Z', 'Ctrl+Y', 'Ctrl+C', 'Ctrl+V', 'Ctrl+S', 'Alt', 'Shift', 'Enter', 'Escape')
        key3_combo.grid(row=2, column=1, padx=5, pady=2)

        # Pen buttons (2 кнопки на пере)
        tk.Label(self.tab_buttons, text="Боковая кнопка 1 пера:").grid(row=3, column=0, sticky="w", padx=5, pady=2)
        self.pen1_var = tk.StringVar(value=self.config.get("pen1", "Right Click"))
        pen1_combo = ttk.Combobox(self.tab_buttons, textvariable=self.pen1_var, width=15)
        pen1_combo['values'] = ('Right Click', 'Middle Click', 'Left Click', 'Double Click', 'Escape')
        pen1_combo.grid(row=3, column=1, padx=5, pady=2)

        tk.Label(self.tab_buttons, text="Боковая кнопка 2 пера:").grid(row=4, column=0, sticky="w", padx=5, pady=2)
        self.pen2_var = tk.StringVar(value=self.config.get("pen2", "Middle Click"))
        pen2_combo = ttk.Combobox(self.tab_buttons, textvariable=self.pen2_var, width=15)
        pen2_combo['values'] = ('Right Click', 'Middle Click', 'Left Click', 'Double Click', 'Escape')
        pen2_combo.grid(row=4, column=1, padx=5, pady=2)

        # Checkboxes
        self.disable_keys = tk.BooleanVar(value=self.config.get("disable_keys", False))
        tk.Checkbutton(self.tab_buttons, text="Отключить кнопки планшета", variable=self.disable_keys).grid(row=5, column=0, columnspan=2, sticky="w", padx=5, pady=5)

        self.disable_pen_buttons = tk.BooleanVar(value=self.config.get("disable_pen_buttons", False))
        tk.Checkbutton(self.tab_buttons, text="Отключить кнопки пера", variable=self.disable_pen_buttons).grid(row=6, column=0, columnspan=2, sticky="w", padx=5, pady=5)

        # Buttons
        button_frame = tk.Frame(root)
        button_frame.pack(fill="x", pady=10)

        apply_button = tk.Button(button_frame, text="Применить", command=self.apply_all, width=15)
        apply_button.pack(side="left", padx=10)

        reset_button = tk.Button(button_frame, text="Сброс", command=self.reset, width=15)
        reset_button.pack(side="left", padx=10)

        test_button = tk.Button(button_frame, text="Тест устройств", command=self.test_devices, width=15)
        test_button.pack(side="left", padx=10)

        # Кнопка для osu! - теперь она будет настраивать правильную область
        osu_button = tk.Button(button_frame, text="Настройка osu!", command=self.setup_osu_mode, width=15)
        osu_button.pack(side="left", padx=10)

    def load_config(self):
        self.config = {}
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r") as f:
                self.config = json.load(f)

    def save_config(self):
        with open(CONFIG_FILE, "w") as f:
            json.dump(self.config, f)

    def create_handles(self):
        for handle in self.handles:
            self.canvas.delete(handle)
        self.handles = []
        size = 10
        positions = [
            (self.rect_x1 - size/2, self.rect_y1 - size/2, self.rect_x1 + size/2, self.rect_y1 + size/2),
            (self.rect_x2 - size/2, self.rect_y1 - size/2, self.rect_x2 + size/2, self.rect_y1 + size/2),
            (self.rect_x1 - size/2, self.rect_y2 - size/2, self.rect_x1 + size/2, self.rect_y2 + size/2),
            (self.rect_x2 - size/2, self.rect_y2 - size/2, self.rect_x2 + size/2, self.rect_y2 + size/2)
        ]
        for pos in positions:
            handle = self.canvas.create_rectangle(pos, fill="red")
            self.handles.append(handle)

    def on_press(self, event):
        for i, handle in enumerate(self.handles):
            coords = self.canvas.coords(handle)
            if coords[0] <= event.x <= coords[2] and coords[1] <= event.y <= coords[3]:
                self.selected_handle = i
                break

    def on_drag(self, event):
        if self.selected_handle is None:
            return
        x = max(0, min(event.x, TABLET_WIDTH_MM * SCALE))
        y = max(0, min(event.y, TABLET_HEIGHT_MM * SCALE))
        if self.selected_handle == 0:
            self.rect_x1 = x
            self.rect_y1 = y
        elif self.selected_handle == 1:
            self.rect_x2 = x
            self.rect_y1 = y
        elif self.selected_handle == 2:
            self.rect_x1 = x
            self.rect_y2 = y
        elif self.selected_handle == 3:
            self.rect_x2 = x
            self.rect_y2 = y
        self.canvas.coords(self.rect, self.rect_x1, self.rect_y1, self.rect_x2, self.rect_y2)
        self.create_handles()

    def on_release(self, event):
        self.selected_handle = None
        # Обновляем числовые значения при отпускании мыши
        self.update_entries_from_rect()

    def update_entries_from_rect(self):
        """Обновляет поля ввода из текущих координат прямоугольника"""
        self.left_entry.delete(0, tk.END)
        self.left_entry.insert(0, f"{self.rect_x1 / SCALE:.1f}")
        self.top_entry.delete(0, tk.END)
        self.top_entry.insert(0, f"{self.rect_y1 / SCALE:.1f}")
        self.right_entry.delete(0, tk.END)
        self.right_entry.insert(0, f"{self.rect_x2 / SCALE:.1f}")
        self.bottom_entry.delete(0, tk.END)
        self.bottom_entry.insert(0, f"{self.rect_y2 / SCALE:.1f}")

    def update_from_entries(self):
        """Обновляет прямоугольник из полей ввода"""
        try:
            left = float(self.left_entry.get())
            top = float(self.top_entry.get())
            right = float(self.right_entry.get())
            bottom = float(self.bottom_entry.get())
            
            # Проверяем корректность значений
            left = max(0, min(left, TABLET_WIDTH_MM))
            top = max(0, min(top, TABLET_HEIGHT_MM))
            right = max(left + 1, min(right, TABLET_WIDTH_MM))
            bottom = max(top + 1, min(bottom, TABLET_HEIGHT_MM))
            
            self.rect_x1 = left * SCALE
            self.rect_y1 = top * SCALE
            self.rect_x2 = right * SCALE
            self.rect_y2 = bottom * SCALE
            
            self.canvas.coords(self.rect, self.rect_x1, self.rect_y1, self.rect_x2, self.rect_y2)
            self.create_handles()
            print(f"Область обновлена: {left}x{top} - {right}x{bottom} mm")
            
        except ValueError:
            print("Ошибка: Введите корректные числа")

    def apply_matrix(self):
        """Применяет матрицу преобразования через xinput"""
        try:
            left = float(self.left_entry.get())
            top = float(self.top_entry.get())
            right = float(self.right_entry.get())
            bottom = float(self.bottom_entry.get())
            
            # Нормализуем координаты относительно размеров планшета
            norm_left = left / TABLET_WIDTH_MM
            norm_top = top / TABLET_HEIGHT_MM
            norm_right = right / TABLET_WIDTH_MM
            norm_bottom = bottom / TABLET_HEIGHT_MM

            if norm_right <= norm_left or norm_bottom <= norm_top:
                print("Ошибка: область слишком мала")
                return False

            scale_x = 1.0 / (norm_right - norm_left)
            scale_y = 1.0 / (norm_bottom - norm_top)
            trans_x = -norm_left * scale_x
            trans_y = -norm_top * scale_y

            matrix = f"{scale_x:.6f} 0 {trans_x:.6f} 0 {scale_y:.6f} {trans_y:.6f} 0 0 1"
            
            print(f"Применяемая матрица: {matrix}")
            
            result = subprocess.run(["xinput", "set-prop", STYLUS_NAME, "Coordinate Transformation Matrix"] + matrix.split(), 
                                  capture_output=True, text=True, check=True, timeout=10)
            print("Матрица преобразования применена успешно")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"Ошибка xinput: {e.stderr}")
            return False
        except Exception as e:
            print(f"Ошибка применения матрицы: {e}")
            return False

    def get_device_id(self, device_name):
        """Получает ID устройства по имени"""
        try:
            result = subprocess.run(["xinput", "list", "--id-only", device_name], 
                                  capture_output=True, text=True, check=True)
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            print(f"Устройство {device_name} не найдено")
            return None

    def disable_device(self, device_name):
        """Отключает устройство"""
        device_id = self.get_device_id(device_name)
        if device_id:
            subprocess.run(["xinput", "disable", device_id])
            print(f"Устройство {device_name} отключено")

    def enable_device(self, device_name):
        """Включает устройство"""
        device_id = self.get_device_id(device_name)
        if device_id:
            subprocess.run(["xinput", "enable", device_id])
            print(f"Устройство {device_name} включено")

    def setup_osu_mode(self):
        """Специальные настройки для osu! - АБСОЛЮТНОЕ позиционирование"""
        print("=== Настройка для osu! ===")
        
        # 1. Сначала сбрасываем все настройки
        self.disable_relative_mode()
        
        # 2. Даем системе время применить изменения
        time.sleep(0.5)
        
        # 3. Настраиваем небольшую область в центре для точности
        center_x = TABLET_WIDTH_MM / 2
        center_y = TABLET_HEIGHT_MM / 2
        area_size = 40  # 40mm область
        
        # Устанавливаем новые значения
        self.rect_x1 = (center_x - area_size/2) * SCALE
        self.rect_y1 = (center_y - area_size/2) * SCALE  
        self.rect_x2 = (center_x + area_size/2) * SCALE
        self.rect_y2 = (center_y + area_size/2) * SCALE
        
        # Обновляем GUI
        self.canvas.coords(self.rect, self.rect_x1, self.rect_y1, self.rect_x2, self.rect_y2)
        self.create_handles()
        self.update_entries_from_rect()
        
        # 4. Применяем матрицу преобразования
        if self.apply_matrix():
            print("✓ Область для osu! настроена")
        
        # 5. Отключаем кнопки планшета
        self.disable_device(PAD_NAME)
        
        # 6. Настраиваем кнопки пера (только левая кнопка активна)
        stylus_id = self.get_device_id(STYLUS_NAME)
        if stylus_id:
            subprocess.run(["xinput", "set-button-map", stylus_id, "1", "0", "0"])
            print("✓ Кнопки пера настроены")
        
        print("✓ Настройки для osu! применены")
        print("В игре osu! включите: Options → Input → Tablet mode: Enabled")
        print("Если курсор все еще не работает, перезапустите игру")

    def disable_relative_mode(self):
        """Отключает относительный режим и возвращает абсолютное позиционирование"""
        try:
            stylus_id = self.get_device_id(STYLUS_NAME)
            if stylus_id:
                # Сбрасываем матрицу преобразования
                matrix = "1 0 0 0 1 0 0 0 1"
                subprocess.run(["xinput", "set-prop", STYLUS_NAME, "Coordinate Transformation Matrix"] + matrix.split(), 
                             check=True, capture_output=True)
                
                # Проверяем и отключаем относительный режим если он есть
                result = subprocess.run(["xinput", "list-props", stylus_id], 
                                      capture_output=True, text=True, check=True)
                
                lines = result.stdout.split('\n')
                for line in lines:
                    if "Relative Mode" in line and "(" in line:
                        prop_id = line.split('(')[1].split(')')[0]
                        subprocess.run(["xinput", "set-prop", stylus_id, prop_id, "0"], 
                                     check=True, capture_output=True)
                        print("✓ Относительный режим отключен")
                        break
                
                print("✓ Абсолютное позиционирование восстановлено")
                
        except Exception as e:
            print(f"Ошибка отключения относительного режима: {e}")

    def remap_buttons(self):
        """Переназначает кнопки через xinput"""
        # Для кнопок планшета
        if self.disable_keys.get():
            self.disable_device(PAD_NAME)
        else:
            self.enable_device(PAD_NAME)

        # Для кнопки пера
        if self.disable_pen_buttons.get():
            # Отключаем кнопки пера через переназначение на несуществующие кнопки
            stylus_id = self.get_device_id(STYLUS_NAME)
            if stylus_id:
                subprocess.run(["xinput", "set-button-map", stylus_id, "1", "0", "0"])
                print("Кнопки пера отключены")
        else:
            # Восстанавливаем стандартные кнопки
            stylus_id = self.get_device_id(STYLUS_NAME)
            if stylus_id:
                subprocess.run(["xinput", "set-button-map", stylus_id, "1", "2", "3"])
                print("Кнопки пера включены")

    def test_devices(self):
        """Тестирование устройств"""
        print("=== Тест устройств ===")
        devices = [STYLUS_NAME, PAD_NAME]
        for device in devices:
            device_id = self.get_device_id(device)
            if device_id:
                print(f"✓ {device} найден (ID: {device_id})")
                
                # Проверяем текущую матрицу преобразования
                try:
                    result = subprocess.run(["xinput", "list-props", device_id], 
                                          capture_output=True, text=True, check=True)
                    if "Coordinate Transformation Matrix" in result.stdout:
                        print(f"  Матрица преобразования доступна")
                    else:
                        print(f"  Матрица преобразования недоступна")
                except:
                    print(f"  Не удалось проверить свойства")
            else:
                print(f"✗ {device} не найден")

    def apply_all(self):
        """Применяет все настройки"""
        print("=== Применение настроек ===")
        
        # Убедимся, что относительный режим выключен
        self.disable_relative_mode()
        
        # Обновляем область из полей ввода
        self.update_from_entries()
        
        # Применяем матрицу преобразования
        if self.apply_matrix():
            print("✓ Область планшета настроена")
        else:
            print("✗ Ошибка настройки области")
        
        # Настраиваем кнопки
        self.remap_buttons()
        
        # Сохраняем конфигурацию
        self.config["left"] = float(self.left_entry.get())
        self.config["top"] = float(self.top_entry.get())
        self.config["right"] = float(self.right_entry.get())
        self.config["bottom"] = float(self.bottom_entry.get())
        self.config["disable_keys"] = self.disable_keys.get()
        self.config["disable_pen_buttons"] = self.disable_pen_buttons.get()
        self.config["key1"] = self.key1_var.get()
        self.config["key2"] = self.key2_var.get()
        self.config["key3"] = self.key3_var.get()
        self.config["pen1"] = self.pen1_var.get()
        self.config["pen2"] = self.pen2_var.get()

        self.save_config()
        print("✓ Настройки применены и сохранены")

    def reset(self):
        """Сбрасывает все настройки"""
        print("=== Сброс настроек ===")
        
        # Убедимся, что относительный режим выключен
        self.disable_relative_mode()
        
        # Сброс области
        self.rect_x1 = 0
        self.rect_y1 = 0
        self.rect_x2 = TABLET_WIDTH_MM * SCALE
        self.rect_y2 = TABLET_HEIGHT_MM * SCALE
        self.canvas.coords(self.rect, self.rect_x1, self.rect_y1, self.rect_x2, self.rect_y2)
        self.create_handles()
        self.update_entries_from_rect()
        
        # Сброс матрицы преобразования
        matrix = "1 0 0 0 1 0 0 0 1"
        try:
            subprocess.run(["xinput", "set-prop", STYLUS_NAME, "Coordinate Transformation Matrix"] + matrix.split(), check=True)
            print("✓ Матрица преобразования сброшена")
        except subprocess.CalledProcessError:
            print("✗ Ошибка при сбросе матрицы")
        
        # Включение всех устройств
        self.enable_device(PAD_NAME)
        stylus_id = self.get_device_id(STYLUS_NAME)
        if stylus_id:
            subprocess.run(["xinput", "set-button-map", stylus_id, "1", "2", "3"])
            print("✓ Кнопки сброшены")
        
        # Сброс чекбоксов
        self.disable_keys.set(False)
        self.disable_pen_buttons.set(False)
        
        print("✓ Все настройки сброшены")

if __name__ == "__main__":
    root = tk.Tk()
    app = HuionConfigurator(root)
    root.mainloop()