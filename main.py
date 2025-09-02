import requests
import os
from dotenv import load_dotenv
from terminaltables import AsciiTable


def download_hh_vacancy(language):
    url = "https://api.hh.ru/vacancies"
    all_vacancies = []
    pages = 25
    found = 0
    for page in range(pages):
        params = {
            "text": language,
            "per_page": 100,
            "page": page,
            "area": 113,
            "only_with_salary": "true",
            "period": "30"
        }
        response = requests.get(url, params=params)
        response.raise_for_status()
        vacancies = response.json()
        if page == 0:
            found = vacancies["found"]
        all_vacancies.extend(vacancies["items"])
        if vacancies.get("pages") and page >= vacancies["pages"] - 1:
            break

    return {"found": found, "items": all_vacancies}


def download_superjob_vacancy(superjob_app_key, language):
    url = "https://api.superjob.ru/2.0/vacancies/"
    headers = {
        "X-Api-App-Id": superjob_app_key
    }
    all_vacancies = []
    pages = 25
    found = 0
    for page in range(pages):
        params = {
            "catalogues": "Разработка, программирование",
            "keyword": language,
            "town": 4,  # Москва
            "count": 50,  # Количество вакансий на страницу
            "page": page
        }
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        vacancies = response.json()
        if page == 0:
            found = vacancies["total"]
        all_vacancies.extend(vacancies["objects"])
        if vacancies.get("pages") and page >= vacancies["pages"] - 1:
            break
    return {"found": found, "items": all_vacancies}


def predict_rub_salary_for_hh(salary):
    if salary['currency'] == 'RUR':
        min_salary = salary['from']
        max_salary = salary['to']
        if min_salary and max_salary:
            return (max_salary + min_salary) / 2
        elif min_salary:
            return min_salary * 1.2
        elif max_salary:
            return max_salary * 0.8
        else:
            return None
    else:
        return None


def predict_rub_salary_for_superJob(vacancy):
    min_salary = vacancy.get('payment_from', 0)
    max_salary = vacancy.get('payment_to', 0)
    if min_salary and max_salary:
        return (max_salary + min_salary) / 2
    elif min_salary:
        return min_salary * 1.2
    elif max_salary:
        return max_salary * 0.8
    else:
        return None


if __name__ == '__main__':
    load_dotenv()
    superjob_app_key = os.environ.get("SUPERJOB_APP_KEY")
    languages = "java", "python", "javascript"
    table_data_superjob = [['SuperJob Moscow'],
                           ['Язык программирования', 'Вакансий найдено', 'Вакансий обработано', 'Средняя зарплата']
                           ]
    for language in languages:
        vacancies = download_superjob_vacancy(superjob_app_key, language)
        salaries = []
        for vacancy in vacancies["items"]:
            predict_salary = predict_rub_salary_for_superJob(vacancy)
            if predict_salary:
                salaries.append(predict_salary)
        average_salary = int(sum(salaries) / len(salaries)) if salaries else 0
        table_data_superjob.append([language, vacancies['found'], len(salaries), average_salary])
    table_superjob = AsciiTable(table_data_superjob)
    print(table_superjob.table)

    table_data_hh = [['HeadHunter Moscow'],
                     ['Язык программирования', 'Вакансий найдено', 'Вакансий обработано', 'Средняя зарплата']
                     ]
    for language in languages:
        vacancies = download_hh_vacancy(language)
        salaries = []
        for vacancy in vacancies["items"]:
            salary = vacancy["salary"]
            predict_salaryd = predict_rub_salary_for_hh(salary)
            if predict_salary:
                salaries.append(predict_salary)
        average_salary = int(sum(salaries) / len(salaries))
        table_data_hh.append([language, vacancies['found'], len(salaries), average_salary])
    table_hh = AsciiTable(table_data_hh)
    print(table_hh.table)
