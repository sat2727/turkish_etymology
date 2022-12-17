from curses.ascii import isdigit
from num2words import num2words


def main():
    tests = [
        "", None, "4569", "123.658", "456,223", "fsdfds",
        "dsfsdf45fsdf", ",555", "569,", "fsdf,5454,66,yhg",
        "fdsf,5875", "fsdfs.fsdf.555.sdf.s"
        ]

    for num in tests:
        print(num)
        print(tr_num2words(num))
        print()



def tr_num2words(num):
    """
    Converts a number to a LIST of turkish words
    if num is None/empty string/non-numeric it returns None
    Period are removed then the result is processed
    commas are the decimal point in Tr:
        if the number is a decimal it's converted
        if num is a series of comma-separated number/mixture values, the numbers are converted
    """
    if num:
        num = num.replace(".", "")
        if num.find(",") != -1:
            num_words = []
            num_comps = num.split(",")
            if len(num_comps) == 2:
                if num_comps[0].isdigit() and num_comps[1].isdigit():
                    num_list = make_list(num2words(num_comps[0], lang="tr"))
                    for word in num_list:
                        num_words.append(word)
                    num_words.append("virgül")
                    num_list = make_list(num2words(num_comps[1], lang="tr"))
                    for word in num_list:
                        num_words.append(word)
                    return num_words
                else:
                    for comp in num_comps:
                        if comp:
                            if comp.isdigit():
                                word_list = make_list(num2words(comp, lang="tr"))
                                for word in word_list:
                                    num_words.append(word)
                            else:
                                num_words.append(comp)
                    return num_words
            else:
                for comp in num_comps:
                    if comp:
                        if comp.isdigit():
                            comp_list = make_list(num2words(comp, lang="tr"))
                            for word in comp_list:
                                num_words.append(word)
                        else:
                            num_words.append(comp)
                return num_words

        else:
            if num.isdigit():
                return make_list(num2words(num, lang="tr"))





def make_list(num_str):
    denoms = [
        "sıfır", "bir", "iki", "üç", "dört", "beş", "altı", "yedi", "sekiz", "dokuz",
        "on", "yirmi", "otuz", "kırk", "elli", "altmış", "yetmiş", "seksen", "doksan",
        "yüz", "bin", "milyon", "milyar", "trilyon", "katrilyon"
        ]

    num_list = []

    while True:
        for denom in denoms:
            if num_str.startswith(denom):
                num_list.append(denom)
                num_str = num_str.replace(denom, "", 1)

        if len(num_str) == 0:
            return num_list
        




if __name__ == "__main__":
    main()






























"""
has title, has etym: harcamak
has title, no etym: alıyor
no title: okuyor
requires stemmer: okullardakiler
initializim: ABD
word_list = ["harcamak", "alıyor", "okuyor", "okullardakiler", "ABD", "olamadığını", "İYİ", "allah", "Allah"]
"""