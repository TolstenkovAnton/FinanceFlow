import spacy
from currency_converter import CurrencyConverter


nlp = spacy.load('ru_core_news_sm')

CATEGORY_KEYWORDS = {
    "Доходы": ["зарплата", "доход", "заработок", "премия", "выручка"],
    "Еда": ["еда", "продукты", "ресторан", "кафе", "пицца", "бургер", "кофе"],
    "Транспорт": ["транспорт", "бензин", "такси", "метро", "автобус", "поезд", "билет"],
    "Коммунальные услуги": ["коммуналка", "свет", "вода", "газ", "отопление", "интернет"],
    "Развлечения": ["кино", "театр", "концерт", "отдых", "парк", "музей", "игры"],
}

def categorize_transactions(transactions):
    categories = {}

    for tr in transactions:
        desc = tr["description"]
        doc = nlp(desc.lower())

        lemmas = set([token.lemma_ for token in doc if not token.is_stop and token.is_alpha])

        matched_category = "Прочее"

        for category, keywords in CATEGORY_KEYWORDS.items():
            keywords_set = set(keywords)
            if lemmas.intersection(keywords_set):
                matched_category = category
                break

        categories.setdefault(matched_category, 0)
        categories[matched_category] += tr["amount"]

    return categories

c = CurrencyConverter(fallback_on_wrong_date=True)

def convert_all_to_currency(transactions, target_currency):
    result = []
    for t in transactions:
        t_copy = dict(t)
        amount = t_copy["amount"]
        from_currency = t_copy["currency"]
        if from_currency != target_currency:
            amount = c.convert(amount, from_currency, target_currency)
        t_copy["amount"] = round(amount, 2)
        t_copy["currency"] = target_currency
        result.append(t_copy)
    return result
