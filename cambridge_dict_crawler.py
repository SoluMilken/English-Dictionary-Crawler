import re
import argparse
import requests
from bs4 import BeautifulSoup

def get_example_page_info(category_node):
    egs = []
    for eg in category_node.find_all('div', **{'class': 'eg'}):
        egs.append(
            {
                'sentence':
                    eg.find('div').text,
                'source':
                    re.sub('\s+', '', eg.find('div', **{'class': 'source'}).text)[4:],
            },
        )
    return egs

def lookup_word(word):
    ## Sending requests
    req = requests.get(
        'http://dictionary.cambridge.org/dictionary/english/{}'.format(word),
         headers={'User-Agent': 'Mozilla/5.0'},
    )
    if req.status_code != 200:
        raise KeyError('Word {} is not found.'.format(word))
    soup = BeautifulSoup(req.text, "html.parser")

    categories = soup.find_all(
        'div',
        **{'class': "tabs__content", "role": "tabpanel"},
    )
    output = {}
    output['vocabulary'] = word
    for category in categories:
        subpage_name = category.attrs['data-tab'][3:]
        output[subpage_name] = {}
        ### tab-example
        if subpage_name == 'example':
            example_info = get_example_page_info(category_node=category)
            if example_info is not []:
                output[subpage_name] = example_info

        pos_blocks = category.find_all(
            'div', **{'class': 'entry-body__el clrd js-share-holder'})
        for pos_block in pos_blocks:
            pos_header = pos_block.find('div', **{'class': 'pos-header'})
            pos_body = pos_block.find('div', **{'class': 'pos-body'})
            pos = pos_header.find('span', **{'class': 'pos'})
            output[subpage_name] = []

            ### sense block
            for sense_block in pos_body.find_all('div', **{'class': 'sense-block'}):
                sense_info_dict = {}
                sense_info_dict["vocabulary"] = word
                sense_info_dict["part-of-speech"] = pos.text

                # guide word
                g = sense_block.find('span', **{'class': 'guideword'})
                if g is not None:
                    sense_info_dict['guideword'] = g.find('span').text

                # definition
                def_block = sense_block.find('div', **{'class': 'def-block pad-indent'})
                sense_info_dict['definition'] = def_block.find(
                    'b', **{'class': 'def'}).text[: -2]

                # example_sentences
                eg_sentences = []
                for eg in def_block.find_all('span', **{'class': 'eg'}):
                    eg_sentences.append(eg.text)
                if len(eg_sentences) > 0:
                    sense_info_dict['example-sentences'] = eg_sentences

                # phrase
                phrases = sense_block.find_all(
                    'div', **{'class': 'phrase-block pad-indent'})
                if len(phrases) > 0:
                    phrase_collections = []
                    for phrase in phrases:
                        phrase_eg = phrase.find('span', **{'class': 'eg'})
                        phrase_dict = {}
                        phrase_dict["phrase"] = phrase.find('span', **{'class': 'phrase'}).text
                        phrase_dict["definition"] = phrase.find(
                            'b', **{'class': 'def'}).text[: -2]
                        if phrase_eg is not None:
                            phrase_dict["example-sentence"] = phrase_eg.text
                        phrase_collections.append(phrase_dict)
                    sense_info_dict["phrase"] = phrase_collections

                # more_examples
                more_examples = sense_block.find('div', **{'class': 'extraexamps'})
                if more_examples is not None:
                    more_egs = []
                    for eg in more_examples.find_all('li', **{'class': 'eg'}):
                         more_egs.append(eg.text)
                    if len(more_egs) > 0:
                        sense_info_dict["more-example-sentences"] = more_egs

                output[subpage_name].append(sense_info_dict)

            # derived words
            runons_body = pos_body.find_all('div', **{'class': 'runon pad-indent'})
            if len(runons_body) > 0:
                for runon in runons_body:
                    runon_eg = runon.find('span', **{'class': 'eg', 'title': 'Example'})
                    runon_dict = {}
                    runon_dict["vocabulary"] = runon.find(
                        'span', **{'class': 'runon-title', 'title': 'Derived word'}).text
                    runon_dict["part-of-speech"] = runon.find(
                        'span', **{'class': 'eg', 'title': 'Example'}).text
                    if runon_eg is not None:
                        runon_dict["example-sentence"] = runon_eg.text
                    output[subpage_name].append(runon_dict)
    return output


def lookup_word_parser():
    parser = argparse.ArgumentParser(
        description=("lookup word"),
    )
    parser.add_argument(
        "-w",
        "--word",
        type=str,
        help="word want to know",
    )
    args = parser.parse_args()
    return args


if __name__ == "__main__":
    import pprint
    args = lookup_word_parser()
    output = lookup_word(word=args.word)
    pprint.pprint(output)
    import ipdb; ipdb.set_trace()
