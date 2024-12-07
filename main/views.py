from django.shortcuts import render
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
import plotly.express as px
import plotly.io as pio
from sklearn.neighbors import BallTree

def index(request):
    # Загружаем данные
    data = pd.read_csv('dataset/UnionR.csv')

    # Обработка данных
    data_cleaned = data.dropna(subset=['Широта', 'Долгота', 'Рейтинг'])
    data_cleaned['Широта'] = pd.to_numeric(data_cleaned['Широта'], errors='coerce')
    data_cleaned['Долгота'] = pd.to_numeric(data_cleaned['Долгота'], errors='coerce')
    data_cleaned = data_cleaned.dropna(subset=['Широта', 'Долгота'])

    # Функция для расчета плотности магазинов и среднего рейтинга соседей
    def calculate_density_and_avg_rating(data, radius=0.5):
        coords = np.radians(data[['Широта', 'Долгота']].values)
        tree = BallTree(coords, metric='haversine')
        
        radius_in_radians = radius / 6371.0  # 6371 - радиус Земли в км
        densities = []
        avg_ratings = []
        
        for i, coord in enumerate(coords):
            indices = tree.query_radius([coord], r=radius_in_radians)[0]
            density = len(indices) - 1  # минус 1, чтобы не считать сам магазин
            densities.append(density)
            
            ratings = data.iloc[indices]['Рейтинг'].values
            avg_rating = np.mean(ratings[ratings != 0])  # Исключаем нулевые рейтинги, если они есть
            avg_ratings.append(avg_rating)
        
        return densities, avg_ratings

    # Применяем функцию для расчета плотности и среднего рейтинга
    data_cleaned['Плотность магазинов'], data_cleaned['Средний рейтинг соседей'] = calculate_density_and_avg_rating(data_cleaned)

    # Создание целевой переменной для обучения модели
    data_cleaned['Выигрышность'] = (data_cleaned['Плотность магазинов'] * 0.5) - (data_cleaned['Средний рейтинг соседей'] * 0.5)

    # Подготовка данных для обучения модели
    X = data_cleaned[['Плотность магазинов', 'Средний рейтинг соседей']]  # Фичи
    y = data_cleaned['Выигрышность']  # Целевая переменная

    # Разделяем данные на обучающую и тестовую выборки
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Обучаем модель линейной регрессии
    model = LinearRegression()
    model.fit(X_train, y_train)

    # Предсказания
    data_cleaned['Предсказанная выигрышность'] = model.predict(X)

    # Получаем выбранный район из параметров URL (если есть)
    district = request.GET.get('district', None)  # Получаем параметр 'district' из URL

    if district:
        data_cleaned = data_cleaned[data_cleaned['Район'] == district]  # Фильтруем данные по району

    # Топ N мест с наивысшей выигрышностью
    top_n = 5
    top_places = data_cleaned.nlargest(top_n, 'Предсказанная выигрышность')

    # Подготовка hover_data
    hover_data = {}
    for column in ['Наименование', 'Рейтинг', 'Адрес', 'Предсказанная выигрышность']:
        if column in top_places.columns and top_places[column].notnull().any():
            hover_data[column] = True

    # Визуализация топовых мест на карте
    fig = px.scatter_mapbox(data_cleaned,
                            lat='Широта',
                            lon='Долгота',
                            color='Предсказанная выигрышность',
                            hover_name='Наименование',
                            hover_data=hover_data,
                            title="Рекомендации по местам для открытия магазина",
                            template="plotly",
                            color_continuous_scale="Viridis")

    fig.update_layout(
        mapbox_style="open-street-map",
        margin={"r":0, "t":0, "l":0, "b":0},
        showlegend=True,
        coloraxis_colorbar=dict(title="Предсказанная выигрышность"),
        autosize=True
    )

    graph_html = pio.to_html(fig, full_html=False)
    
    # Список районов для фильтрации (получаем уникальные районы из данных)
    districts = data_cleaned['Район'].unique()

    return render(request, 'main/index.html', {
        'graph_html': graph_html,
        'districts': districts,  # Передаем список районов в шаблон
        'top_places': top_places
    })
