from currency_app import models
from sqlalchemy.exc import IntegrityError
import requests
import xml.etree.ElementTree as ET

def save_currencies(db, currency_data):
    currency_data = currency_data.dict()

    # Приводим поле 'code' к верхнему регистру
    code = currency_data['code'].upper()

    # Проверка наличия валюты в базе данных
    existing_currency = db.query(models.Currency).filter_by(code=code).first()

    # Если валюта не найдена, записываем её в базу данных
    if not existing_currency:
        currency_data['code'] = code  # Обновляем поле 'code' в исходных данных
        new_currency = models.Currency(**currency_data)
        db.add(new_currency)
        try:
            db.commit()
            return {"success": f"Валюта {new_currency.name}, id:({new_currency.id}) успешно добавлена в базу данных."}
        except IntegrityError:
            db.rollback()
            return {"error": "Ошибка при сохранении валюты: дублирование ключа."}
    else:
        return {"error": f"Валюта {existing_currency.name}, id:({existing_currency.id}) уже присутствует в базе данных."}


def fetch_and_parse_xml(url):
    response = requests.get(url)
    xml_data = response.content
    root = ET.fromstring(xml_data)
    return root


def currencies_list(db):

    url = 'https://www.cbr.ru/scripts/XML_valFull.asp'
    root = fetch_and_parse_xml(url)

    currencies = []
    added_currencies = 0

    for item in root.findall('.//Item'):
        name = item.find('Name').text
        iso_char_code = item.find('ISO_Char_Code').text
        if iso_char_code is None:
            continue
        currencies.append({'name': name, 'iso_char_code': iso_char_code})

    for currency in currencies: 
        existing_currency = db.query(models.Currency).filter(models.Currency.code == currency['iso_char_code']).first()
        if not existing_currency is None:
            continue
        try:
            new_currency = models.Currency(code=currency['iso_char_code'], name=currency['name'])
            db.add(new_currency)
            db.commit()
            added_currencies += 1
        except IntegrityError:
            db.rollback()  # В случае ошибки откатываем изменения
            
    return {"message": f"Currencies added successfully. Total new additions: {added_currencies}"}

