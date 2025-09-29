import requests
import os
from dotenv import load_dotenv
from terminaltables import AsciiTable


def download_hh_vacanies(language):
    url = "https://api.hh.ru/vacancies"
    all_vacancies = []
    page = 0
    found = 0
    while True:
        params = {
            "text": language, #ключевые слова поиска, используем названия языков программирования
            "per_page": 100, #количество вакансий на странице
            "page": page, #номер страницы для их перебора
            "area": 113, #где ищем вакансии,113 - Москва
            "only_with_salary": "true", #берем только вакансии с указанной зарплатой
            "period": "30" #за какой период собираем вакансии, 30 дней по умолчанию
        }
        response = requests.get(url, params=params)
        response.raise_for_status()
        vacancies = response.json()

        if page == 0:
            found = vacancies["found"]
        all_vacancies.extend(vacancies["items"])
        if not vacancies.get("more"):
            break
        page += 1

    return found, all_vacancies


def download_superjob_vacanies(language):
    url = "https://api.superjob.ru/2.0/vacancies/"
    superjob_app_key = os.environ.get("SUPERJOB_APP_KEY")
    headers = {
        "X-Api-App-Id": superjob_app_key
    }
    all_vacancies = []
    page = 0
    found = 0
    while True:
        params = {
            "catalogues": "Разработка, программирование", #каталог, в котором ищем вакансии
            "keyword": language, #ключевые слова поиска, используем названия языков программирования
            "town": 4,  # Москва
            "count": 50,  # Количество вакансий на страницу
            "page": page #номер страницы для их перебора
        }
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        vacancies = response.json()

        if page == 0:
            found = vacancies["total"]
        all_vacancies.extend(vacancies["objects"])
        if not vacancies.get("more"):
            break
        page += 1
    return found, all_vacancies


def average_salary_calculator(min_salary, max_salary):
    if min_salary and max_salary:
        return (max_salary + min_salary) / 2
    elif min_salary:
        return min_salary * 1.2
    elif max_salary:
        return max_salary * 0.8
    else:
        return None

def predict_rub_salary_for_hh(vacancy):
    salary = vacancy["salary"]
    if salary['currency'] == 'RUR':
        min_salary = salary['from']
        max_salary = salary['to']
        return average_salary_calculator(min_salary, max_salary)
    else:
        return None


def predict_rub_salary_for_superJob(vacancy):
    min_salary = vacancy.get('payment_from', 0)
    max_salary = vacancy.get('payment_to', 0)
    return average_salary_calculator(min_salary, max_salary)

def make_table(title, rows):
    header = ['Язык программирования', 'Вакансий найдено',
                            'Вакансий обработано', 'Средняя зарплата']

    table_data = [[title], header] + rows
    return AsciiTable(table_data).table

def collect_salary_statistics(sources, languages):
    for cite, download_function, predict_function in sources:
        rows = []
        for language in languages:
            found, items = download_function(language)
            salaries = []
            for vacancy in items:
                predicted_salary = predict_function(vacancy)
                if predicted_salary:
                    salaries.append(predicted_salary)
            vacancies_processed = len(salaries)
            average_salary = int(sum(salaries) / vacancies_processed) if salaries else 0
            rows.append([language, found, vacancies_processed, average_salary])
        print(make_table(cite, rows))


if __name__ == '__main__':
    load_dotenv()
    languages = ("java", "python", "javascript")
    sources = [
        ("SuperJob Moscow", download_superjob_vacanies, predict_rub_salary_for_superJob),
        ("Headhunter Moscow", download_hh_vacanies, predict_rub_salary_for_hh),
    ]
    collect_salary_statistics(sources, languages)
