document.addEventListener('DOMContentLoaded', function() {
    // Theme Toggle
    const themeToggle = document.getElementById('themeToggle');
    const html = document.documentElement;
    const themeIcon = themeToggle.querySelector('i');

    function toggleTheme() {
        const currentTheme = html.getAttribute('data-theme');
        const newTheme = currentTheme === 'light' ? 'dark' : 'light';
        html.setAttribute('data-theme', newTheme);
        themeIcon.className = newTheme === 'light' ? 'fas fa-moon' : 'fas fa-sun';
        localStorage.setItem('theme', newTheme);
    }

    // Load saved theme
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme) {
        html.setAttribute('data-theme', savedTheme);
        themeIcon.className = savedTheme === 'light' ? 'fas fa-moon' : 'fas fa-sun';
    }

    themeToggle.addEventListener('click', toggleTheme);

    // Active navigation highlight
    const sections = document.querySelectorAll('section');
    const navLinks = document.querySelectorAll('.nav-links a');

    window.addEventListener('scroll', () => {
        let current = '';
        sections.forEach(section => {
            const sectionTop = section.offsetTop;
            const sectionHeight = section.clientHeight;
            if (scrollY >= (sectionTop - sectionHeight / 3)) {
                current = section.getAttribute('id');
            }
        });

        navLinks.forEach(link => {
            link.classList.remove('active');
            if (link.getAttribute('href').slice(1) === current) {
                link.classList.add('active');
            }
        });
    });

    // FAQ Accordion
    document.querySelectorAll('.faq-question').forEach(question => {
        question.addEventListener('click', () => {
            const answer = question.nextElementSibling;
            const isOpen = answer.style.display === 'block';
            
            // Close all answers
            document.querySelectorAll('.faq-answer').forEach(a => {
                a.style.display = 'none';
            });

            // Open clicked answer if it was closed
            if (!isOpen) {
                answer.style.display = 'block';
            }
        });
    });

    // Contact Form
    const contactForm = document.getElementById('contactForm');
    contactForm.addEventListener('submit', (e) => {
        e.preventDefault();
        // Simulate form submission
        alert('Спасибо за ваше сообщение! Мы свяжемся с вами в ближайшее время.');
        contactForm.reset();
    });
});

document.addEventListener('DOMContentLoaded', function () {
    const filtersForm = document.getElementById('filtersForm');

    filtersForm.addEventListener('submit', function (event) {
        event.preventDefault();

        const formData = new FormData(filtersForm);
        const params = new URLSearchParams(formData).toString();

        fetch(`?${params}`, {
            method: 'GET',
            headers: { 'X-Requested-With': 'XMLHttpRequest' },
        })
            .then(response => response.text())
            .then(html => {
                // Обновляем только секцию с анализом
                const analysisSection = document.querySelector('#analysis');
                const parser = new DOMParser();
                const doc = parser.parseFromString(html, 'text/html');
                const newContent = doc.querySelector('#analysis');
                if (analysisSection && newContent) {
                    analysisSection.innerHTML = newContent.innerHTML;
                }
                // Обновляем URL в браузере
                history.pushState(null, '', `?${params}`);
            })
            .catch(error => console.error('Ошибка при обновлении фильтров:', error));
    });
});

document.addEventListener('DOMContentLoaded', function () {
    if (typeof initMap === 'function') {
        initMap();
    } else {
        console.error('Функция initMap не найдена.');
    }
});

document.getElementById('top5Checkbox').addEventListener('change', function () {
    const isChecked = this.checked;

    // Получить данные для карты (например, из скрытых элементов)
    const allLocations = JSON.parse(document.getElementById('map-data').textContent || '[]');
    const filteredLocations = isChecked ? allLocations.slice(0, 5) : allLocations;

    if (typeof initMap === 'function') {
        initMap(filteredLocations);
    }
});

function initMap(locations = []) {
    // Убедитесь, что контейнер для карты существует
    const mapContainer = document.getElementById('map');
    if (!mapContainer) {
        console.error('Контейнер карты не найден.');
        return;
    }

    // Очищаем предыдущую карту (если нужно)
    mapContainer.innerHTML = '';

    // Инициализация карты (пример для Google Maps)
    const map = new google.maps.Map(mapContainer, {
        zoom: 12,
        center: { lat: locations[0]?.latitude || 0, lng: locations[0]?.longitude || 0 },
    });

    // Добавляем метки
    locations.forEach(location => {
        new google.maps.Marker({
            position: { lat: location.latitude, lng: location.longitude },
            map: map,
            title: location.name,
        });
    });
}



