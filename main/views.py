from django.shortcuts import render
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
import plotly.express as px
import plotly.io as pio
import requests
from sklearn.neighbors import BallTree


def index(request):
    try:
        # Загружаем данные
        data = pd.read_csv('dataset/UnionR.csv')

        if data.empty:
            return render(request, 'main/index.html', {'graph_html': '<p>Нет данных</p>'})

        # Очистка данных
        data_cleaned = data.dropna(subset=['Широта', 'Долгота', 'Рейтинг'])
        data_cleaned['Широта'] = pd.to_numeric(data_cleaned['Широта'], errors='coerce')
        data_cleaned['Долгота'] = pd.to_numeric(data_cleaned['Долгота'], errors='coerce')
        data_cleaned = data_cleaned.dropna(subset=['Широта', 'Долгота'])

        # Рассчитываем плотность и средний рейтинг
        def calculate_density_and_avg_rating(data, radius=0.5):
            coords = np.radians(data[['Широта', 'Долгота']].values)
            tree = BallTree(coords, metric='haversine')

            radius_in_radians = radius / 6371.0
            densities = []
            avg_ratings = []

            for i, coord in enumerate(coords):
                indices = tree.query_radius([coord], r=radius_in_radians)[0]
                density = len(indices) - 1
                densities.append(density)

                ratings = data.iloc[indices]['Рейтинг'].values
                avg_rating = np.mean(ratings[ratings != 0])
                avg_ratings.append(avg_rating)

            return densities, avg_ratings

        data_cleaned['Плотность магазинов'], data_cleaned['Средний рейтинг соседей'] = calculate_density_and_avg_rating(data_cleaned)
        data_cleaned['Выигрышность'] = (data_cleaned['Плотность магазинов'] * 0.5) - (data_cleaned['Средний рейтинг соседей'] * 0.5)
        
        # Обучение модели
        X = data_cleaned[['Плотность магазинов', 'Средний рейтинг соседей']]
        y = data_cleaned['Выигрышность']
        model = LinearRegression()
        model.fit(X, y)
        data_cleaned['Предсказанная выигрышность'] = model.predict(X)

        # Применяем фильтры
        district = request.GET.get('district', 'all')
        top_only = request.GET.get('top_only') == 'true'

        filtered_data = data_cleaned.copy()
        if district != 'all':
            filtered_data = filtered_data[filtered_data['Район'] == district]
        if top_only:
            filtered_data = filtered_data.nlargest(5, 'Предсказанная выигрышность')

        # Генерация карты
        if not filtered_data.empty:
            fig = px.scatter_mapbox(filtered_data,
                                    lat='Широта',
                                    lon='Долгота',
                                    color='Предсказанная выигрышность',
                                    hover_name='Наименование',
                                    hover_data=['Рейтинг', 'Адрес', 'Предсказанная выигрышность']
                                    )
            fig.update_layout(
                mapbox_style="open-street-map",
                mapbox=dict(
                    center=dict(
                        lat=filtered_data['Широта'].mean(),
                        lon=filtered_data['Долгота'].mean()
                    ),
                    zoom=11
                ),
                margin={"r": 0, "t": 0, "l": 0, "b": 0},
                height=600
            )
            graph_html = pio.to_html(fig, full_html=False)
        else:
            graph_html = "<p>Нет данных для отображения</p>"

        top_locations = data_cleaned.nlargest(5, 'Предсказанная выигрышность')
        top_locations_summary = top_locations[['Наименование', 'Адрес', 'Предсказанная выигрышность']].to_dict(orient="records")

        # Отладочный вывод
        print("Топовые места:", top_locations_summary)

        # Получаем анализ от Gemini
        gemini_analysis, gemini_debug = fetch_gemini_analysis(top_locations_summary)

        context = {
            'graph_html': graph_html,
            'districts': ['all'] + list(data_cleaned['Район'].unique()),
            'current_district': district,
            'top_only': 'checked' if top_only else '',
            'gemini_analysis': gemini_analysis,
            'gemini_debug': gemini_debug,  # Для вывода отладочной информации
        }

        return render(request, 'main/index.html', context)
    except Exception as e:
        return render(request, 'main/index.html', {'graph_html': f"<p>Ошибка: {e}</p>"})


def fetch_gemini_analysis(data):
    """
    Отправляет данные о топ-5 местах в Gemini API и возвращает анализ.

    Args:
        data (list): Список топовых мест с выигрышностью.

    Returns:
        tuple: (анализ, отладочная информация)
    """
    api_key = "AIzaSyCiTNGZ_RtRfoBZrRSEnkXQSXwinciRpts"
    gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key={api_key}"

    locations_description = "\n".join(
        [f"{i+1}. {loc['Наименование']} ({loc['Адрес']}): Выигрышность {loc['Предсказанная выигрышность']:.2f}"
         for i, loc in enumerate(data)]
    )

    prompt = (
    f"Вот данные о топ-5 местах с высокой выигрышностью:\n{locations_description}\n\n"
    "Выигрышность определяется как разница между плотностью магазинов и средним рейтингом соседей. "
    "Высокая плотность магазинов в районе указывает на большую вероятность привлечения клиентов, "
    "в то время как высокий рейтинг соседей может свидетельствовать о хорошем обслуживании и популярности района. "
    "Таким образом, место с высокой выигрышностью представляет собой оптимальное сочетание этих факторов.\n\n"
    "Объясните, почему эти места выделяются и что можно улучшить для их дальнейшего развития. "
    "Например, можно обратить внимание на повышение качества обслуживания или расширение ассортимента в магазинах. "
    "Кроме того, предложите возможные стратегии для увеличения плотности магазинов в этих районах.\n\n"
    "Также, если клиент решит открыть магазин в одном из этих мест, он может сэкономить значительную сумму. "
    "Для оценки экономии используйте информацию о плотности магазинов и рейтинге соседей, а также учитывайте, "
    "что магазин с высокой выигрышностью может привлечь больше клиентов, снизив затраты на маркетинг и увеличив продажи."
    )


    payload = {
        "contents": [{
            "parts": [{
                "text": prompt
            }]
        }]
    }

    headers = {"Content-Type": "application/json"}

    try:
        print("Отправляемый запрос:", payload)
        response = requests.post(gemini_url, json=payload, headers=headers)
        response.raise_for_status()
        response_data = response.json()
        print("Ответ API:", response_data)

        # Извлечение анализа
        candidates = response_data.get("candidates", [])
        gemini_response = candidates[0]["content"]["parts"][0]["text"] if candidates else "Нет ответа от Gemini"

        # Отладочная информация
        print("Ответ Gemini API:", gemini_response)
        return gemini_response, response_data

    except requests.exceptions.RequestException as e:
        print(f"Ошибка при запросе к Gemini API: {e}")
        return f"Ошибка API Gemini: {e}", None
