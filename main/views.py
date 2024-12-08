from django.shortcuts import render
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
import plotly.express as px
import plotly.io as pio
from sklearn.neighbors import BallTree
import logging

# Настройка логгера
logger = logging.getLogger('main')

def index(request):
    logger.info("Старт обработки запроса в index")

    try:
        # Загружаем данные
        logger.debug("Загружаем данные из файла")
        data = pd.read_csv('dataset/UnionR.csv')

        # Проверка на наличие данных
        if data.empty:
            logger.warning("Файл пустой или данные отсутствуют")
            return render(request, 'main/index.html', {'graph_html': '<p>Нет данных</p>'})

        logger.info(f"Загружено {len(data)} записей")

        # Обработка данных
        data_cleaned = data.dropna(subset=['Широта', 'Долгота', 'Рейтинг'])
        data_cleaned['Широта'] = pd.to_numeric(data_cleaned['Широта'], errors='coerce')
        data_cleaned['Долгота'] = pd.to_numeric(data_cleaned['Долгота'], errors='coerce')
        data_cleaned = data_cleaned.dropna(subset=['Широта', 'Долгота'])

        if data_cleaned.empty:
            logger.warning("Данные после очистки пусты")
            return render(request, 'main/index.html', {'graph_html': '<p>Нет данных для отображения</p>'})

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
            data_cleaned = data_cleaned[data_cleaned['Район'] == district]
            if data_cleaned.empty:
                logger.warning(f"Район '{district}' не найден или данные пусты")
                return render(request, 'main/index.html', {
                    'graph_html': '<p>Данные для выбранного района отсутствуют</p>',
                    'districts': data['Район'].unique()
                })

        # Топ N мест с наивысшей выигрышностью
        top_n = 5
        top_places = data_cleaned.nlargest(top_n, 'Предсказанная выигрышность')

        if top_places.empty:
            logger.warning("Топовые места отсутствуют")
            return render(request, 'main/index.html', {
                'graph_html': '<p>Топовые места не найдены</p>',
                'districts': data['Район'].unique()
            })

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
            margin={"r": 0, "t": 0, "l": 0, "b": 0},
            showlegend=True,
            coloraxis_colorbar=dict(title="Предсказанная выигрышность"),
            autosize=True
        )

        graph_html = pio.to_html(fig, full_html=False)

        # Список районов для фильтрации (получаем уникальные районы из данных)
        districts = data['Район'].unique()

        logger.info("Успешное завершение обработки запроса")

        return render(request, 'main/index.html', {
            'graph_html': graph_html,
            'districts': districts,  # Передаем список районов в шаблон
            'top_places': top_places
        })

    except Exception as e:
        logger.error(f"Произошла ошибка: {e}", exc_info=True)
        return render(request, 'main/index.html', {
            'graph_html': f"<p>Ошибка: {e}</p>"
        })
