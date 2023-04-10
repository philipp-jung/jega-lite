import random
import datetime

from ..basis import DataCorruption


class BrokenCharacters(DataCorruption):
    """
    Mimics cases where text is processed with the wrong encoding (e.g., when
    crawled from the web)
    """

    def __init__(self, column, fraction) -> None:
        self.column = column
        self.fraction = fraction
        super().__init__()

    def transform(self, data):
        corrupted_data = data.copy(deep=True)

        replacements = {
            "a": "á",
            "A": "Á",
            "e": "é",
            "E": "É",
            "o": "ớ",
            "O": "Ớ",
            "u": "ú",
            "U": "Ú",
        }

        for index, row in corrupted_data.iterrows():
            if random.random() < self.fraction:
                column_value = row[self.column]

                for character, replacement in replacements.items():
                    column_value = str(column_value).replace(character, replacement)

                corrupted_data.at[index, self.column] = column_value

        return corrupted_data


class WildCharacter(DataCorruption):
    """
    Inspired by the rayyan dataset from Mahdavi et al. 2019, the � character
    is either randomly added, or one � replaces one char, or two �� replace one
    char.
    """

    def __init__(self, column, fraction) -> None:
        self.column = column
        self.fraction = fraction
        super().__init__()

    def transform(self, data):
        actions = ['add', 'replace', 'double_replace']
        corrupted_data = data.copy(deep=True)

        for index, row in corrupted_data.iterrows():
            if random.random() < self.fraction:
                column_value = row[self.column]

                action = random.choice(actions)
                pos = random.randint(0, len(column_value)-1)
                if action == 'add':
                    column_value = column_value[:pos] + '�' + column_value[pos:]
                elif action == 'replace':
                    column_value = column_value[:pos] + '�' + column_value[pos+1:]
                elif action == 'double_replace':
                    column_value = column_value[:pos] + '��' + column_value[pos+1:]

                corrupted_data.at[index, self.column] = column_value

        return corrupted_data

class BrokenFormat(DataCorruption):
    """
    Inspired by the rayyan dataset from Mahdavi et al. 2019, mix up the date
    formatting in a column.
    """

    def __init__(self, column, fraction) -> None:
        self.column = column
        self.fraction = fraction
        super().__init__()

    def transform(self, data):
        date_patterns = ["%d-%m-%Y", "%Y-%m-%d", "%m-%d-%Y"]
        working_format = None
        date = None

        test_value = data.iloc[0, self.column]
        for p in date_patterns:  # find right date format
            try:
                date = datetime.datetime.strptime(test_value, p).date()
                working_format = p
            except:
                pass

        if working_format is None:  # could not parse date
            return data

        corrupted_data = data.copy(deep=True)
        bad_format = random.choice([f for f in date_patterns if f != working_format])

        for index, row in corrupted_data.iterrows():
            if random.random() < self.fraction:
                column_value = row[self.column]
                corrupted_value = datetime.datetime.strptime(column_value,
                                                             working_format)\
                                                             .date()\
                                                             .strftime(bad_format)
                corrupted_data.at[index, self.column] = column_value

        return corrupted_data
