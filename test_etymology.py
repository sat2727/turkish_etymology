import etymology
import re

def test_wiktionary_titles():
    # test if the function returns the correct page id if the page exists
    assert etymology.wiktionary_titles("python") == "180586"   
    
    # test if the function returns None if the page doesn't exist
    assert not etymology.wiktionary_titles("random_gibberish")


def test_wiktionary_parse():
    # test if function returns the html soup cooresponding to the page id, and only in target lang
    soup =  etymology.wiktionary_parse(etymology.wiktionary_titles("konu"), lang="Turkish")
    assert soup
    assert len(re.findall('<h2><span class="mw-headline"', soup)) == 1
    
    # test if the function returns None if the input is None
    assert not etymology.wiktionary_parse(None)

    # test if the function returns None if target language doesn't exist in page
    assert not etymology.wiktionary_parse(etymology.wiktionary_titles("python"), lang="Turkish")
     

def test_wiktionary_search():
    # test if the function returns a non-empty list if there are matches in wiktionary
    # Returns None otherwise
    assert etymology.wiktionary_search("python")
    assert not etymology.wiktionary_search("random_gibberish")


def test_etym_stemmer():
    # test if the function stems suffixed verbs and nouns
    assert etymology.etym_stemmer("okuduğumuzunu")[0]["stem"] == "okumak"
    assert etymology.etym_stemmer("okullarındakilerinin")[0]["stem"] == "okul"

    # test if the function doesn't stem words that are already etymological stems
    assert etymology.etym_stemmer("okumak")[0]["stem"] == "okumak"

    # test if stemmer returns all the stems contained in an acronyms
    stems = [stem["stem"] for stem in etymology.etym_stemmer("ABD")]
    assert stems == ['Amerika', 'birleşmek', 'devlet']

    # test if the function returns None if an etymological stem doesn't exist
    assert not etymology.etym_stemmer("random_gibberish")


def test_ultimate_etymology():
    # test single stem single substem single etym lang
    ultimates = etymology.ultimate_etymology(etymology.etymology("harcamak"))
    stats = {}
    for stem in ultimates:
        for sub_stem in stem:
            if sub_stem["etym"] in stats:
                stats.update({sub_stem["etym"]: stats[sub_stem["etym"]] + sub_stem["ratio"]}) 
            else:
                stats.update({sub_stem["etym"]: sub_stem["ratio"]}) 
    assert len(stats) == 1
    assert stats["Arabic"] == 1
    
    # test single stem single substem multiple etym langs
    ultimates = etymology.ultimate_etymology(etymology.etymology("yüz"))
    stats = {}
    for stem in ultimates:
        for sub_stem in stem:
            if sub_stem["etym"] in stats:
                stats.update({sub_stem["etym"]: stats[sub_stem["etym"]] + sub_stem["ratio"]}) 
            else:
                stats.update({sub_stem["etym"]: sub_stem["ratio"]}) 
    assert len(stats) == 2
    assert stats["Turkic"] == 0.5
    assert stats["Mongolian"] == 0.5
    
    # test compound words - single stem multiple substems
    ultimates = etymology.ultimate_etymology(etymology.etymology("kaydetmek"))
    stats = {}
    for stem in ultimates:
        for sub_stem in stem:
            if sub_stem["etym"] in stats:
                stats.update({sub_stem["etym"]: stats[sub_stem["etym"]] + sub_stem["ratio"]}) 
            else:
                stats.update({sub_stem["etym"]: sub_stem["ratio"]}) 
    assert len(stats) == 2
    assert stats["Turkic"] == 0.5
    assert stats["Arabic"] == 0.5

    # test multi-digit numbers - multiple stems
    ultimates = etymology.ultimate_etymology(etymology.etymology("112"))
    stats = {}
    for stem in ultimates:
        for sub_stem in stem:
            if sub_stem["etym"] in stats:
                stats.update({sub_stem["etym"]: stats[sub_stem["etym"]] + sub_stem["ratio"]}) 
            else:
                stats.update({sub_stem["etym"]: sub_stem["ratio"]}) 
    assert len(stats) == 2
    assert stats["Turkic"] == 2.5
    assert stats["Mongolian"] == 0.5
    
    # test if te function returns None if no etymology is found
    ultimates = etymology.ultimate_etymology(etymology.etymology("random_gibberish"))
    assert not ultimates