import numpy as np
import pandas as pd
from scipy.ndimage import gaussian_filter
import os

# Налаштування параметрів
num_points = 100000  # Кількість точок
area_size = 1000  # Розмір області в метрах (x, y: [0, 1000])
max_depth = 500  # Максимальна глибина в метрах
objects = ["sand", "rock", "coral", "reef", "empty"]  # Типи об'єктів

# Функція для генерації плавного рельєфу
def generate_smooth_terrain(x, y, area_size, max_depth):
    # Комбінація кількох синусоїд для природного рельєфу
    depth = (
        100 * np.sin(2 * np.pi * x / 500) * np.cos(2 * np.pi * y / 500) +
        50 * np.sin(2 * np.pi * x / 200) * np.cos(2 * np.pi * y / 200) +
        20 * np.sin(2 * np.pi * x / 100) * np.cos(2 * np.pi * y / 100)
    )
    # Нормалізація та масштабування до [0, max_depth]
    depth = (depth - np.min(depth)) / (np.max(depth) - np.min(depth)) * max_depth
    # Додавання невеликого шуму та згладжування
    noise = np.random.normal(0, 10, x.shape)
    depth = depth + noise
    # Застосовуємо гаусівське згладжування
    depth = gaussian_filter(depth, sigma=5)
    return np.clip(depth, 0, max_depth)

# Функція для генерації плавного розподілу об'єктів
def generate_smooth_objects(x, y, area_size):
    # Ініціалізація поля ймовірностей для кожного типу об'єкта
    object_probs = np.zeros((len(x), len(objects)))
    
    # Центри кластерів для кожного типу об'єкта
    n_clusters = 10
    for i, obj in enumerate(objects):
        # Випадкові центри кластерів
        centers = np.random.uniform(0, area_size, (n_clusters, 2))
        for center in centers:
            # Гаусівська функція для плавного розподілу ймовірностей
            dist = np.sqrt((x - center[0])**2 + (y - center[1])**2)
            prob = np.exp(-dist**2 / (2 * 50**2))  # Сигма = 50 для кластера
            object_probs[:, i] += prob
    
    # Нормалізація ймовірностей
    object_probs /= np.sum(object_probs, axis=1, keepdims=True)
    
    # Вибір об'єкта для кожної точки
    object_indices = np.array([np.random.choice(len(objects), p=probs) for probs in object_probs])
    return np.array(objects)[object_indices]

# Генерація координат x, y
np.random.seed(42)  # Для відтворюваності
x = np.random.uniform(0, area_size, num_points)
y = np.random.uniform(0, area_size, num_points)

# Генерація плавного рельєфу
z = generate_smooth_terrain(x, y, area_size, max_depth)

# Генерація плавного розподілу об'єктів
object_types = generate_smooth_objects(x, y, area_size)

# Створення DataFrame
data = pd.DataFrame({
    "x": x,
    "y": y,
    "depth": z,
    "object_type": object_types
})

# Збереження у CSV файл
output_path = "terrain_map.csv"
data.to_csv(output_path, index=False)
print(f"CSV файл збережено за шляхом: {os.path.abspath(output_path)}")
