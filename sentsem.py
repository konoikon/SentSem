# ----------------------------------------------------------------------------
# File Name: sentsem.py
# Purpose: This python file is used to find the semantic similarity between
#          two sentences in English. The main corpus used is WordNet, created
#          by Princeton University, which is a lexicon of English words that
#          describes their hierarchy through the way they are semantically
#          related.
#
#          The only required libraries for this project is the Natural Language
#          Toolkit (NLTK) for python, and the relevant corpora should be down-
#          loaded using the download() function, as well as numpy.
#
# License: Apache License 2.0
#
# Created: 10/01/2018
# Author: Konstantinos Oikonomou, kons.oikonomou@gmail.com
#
# ----------------------------------------------------------------------------

import nltk

from nltk.corpus import wordnet as wn
from nltk.corpus import stopwords

from nltk.tokenize import RegexpTokenizer
from nltk.stem import WordNetLemmatizer
from nltk.wsd import lesk

import numpy as np

tokenizer = RegexpTokenizer(r'\w+')
lemmatizer = WordNetLemmatizer()

stopwords = stopwords.words('english')


def pos(tag):
    """This function takes the results from the nltk.pos_tag() function and turns them into pos types that can be
       readable by WordNet. WordNet supports 5 different types, specifically Nouns, Verbs, Adverbs, Head Adjectives
       and Satelite Adjectives (Head and Satelite are too much about linguistics, we don't care about it very much).
       Here, we do not take into accouont the Satelite Adjectives but we will do so later."""

    if tag.startswith('N') or tag == 'MD':
        return wn.NOUN
    elif tag.startswith('J'):
        return wn.ADJ
    elif tag.startswith('V'):
        return wn.VERB
    elif tag.startswith('RB'):
        return wn.ADV
    else:
        return ''


def sentsem(sent1, sent2):
    """This function performs the similarity measurement. The procedure has several steps.
       1. Lowercase the sentences
       2. Tokenization (separates each word)
       3. Stopword removal (Stopwords do not provide semantic insight, hence they are obsolete)
       4. POS Tagging (In this function, we use the nltk.pos_tag(). Other POS Taggers might be more accurate)
       5. Lemmatization: Removal of suffixes etc. e.g. 'Foxes' --> 'Fox'
       6. Word Sense Disambiguation (WSD): Words might be ambiguous, that is have multiple senses. For a word, WordNet
          creates a synset for each sense of the word. In order to find the correct synset (the correct word sense in
          our sentence), a common algorithm that is used is the Lesk algorithm (developed by Micheal Lesk).
       7. We create a matrix with as many rows as the remaining tokens of sentence 1 and as many columns as the
          remaining tokens of sentence 2. Let this matrix be A(i, j).
       8. Each element (i, j) of the matrix is assigned to be the path similarity between the ith token of sentence 1
          and the jth token of sentence 2. Path similarity is a common similarity measure in WordNet, however another
          similarity metric might be more appropriate depending on the application.
       9. We find matching pairs of words. Each word has a best pairing match, i.e. the word with which it presents
          maximum similarity.
       10. We add up the similarities of the pairs, multiply them by two and divide the result with the sum of the
           lengths of the two token lists. The reason to do this can be found in the following link:
           https://www.sciencedirect.com/science/article/pii/S1570866708000658
           This is an academic paper created by Fredriksson and Grabowski. It has some Graph Theory mathematics and
           robust supporting theory that explains the formula.

       This is the final similarity measurement."""

    # Step 1
    sent1 = sent1.lower()
    sent2 = sent2.lower()

    # Step 2
    tokens1 = [word for word in tokenizer.tokenize(sent1)]
    tokens2 = [word for word in tokenizer.tokenize(sent2)]

    # Step 3
    tokens1 = [word for word in tokens1 if word not in stopwords]
    tokens2 = [word for word in tokens2 if word not in stopwords]

    # Step 4
    text1 = [(w, pos(p)) for (w, p) in nltk.pos_tag(tokens1)]
    text2 = [(w, pos(p)) for (w, p) in nltk.pos_tag(tokens2)]

    # Step 5
    text1 = [(lemmatizer.lemmatize(word), p) for (word, p) in text1]
    text2 = [(lemmatizer.lemmatize(word), p) for (word, p) in text2]

    # Step 6
    sensed1 = [(word, lesk(sent1, word, p))
               # Here we deal with Satelite adjetives. Whenever the lesk algorithm can't find an appropriate synset,
               # it is because we don't provide the correct POS tag. This means that the POS tag must be 's', for
               # satelite adjectives
               if (lesk(sent1, word, p) is not None) else (word, lesk(sent1, word, 's'))
               for (word, p) in text1]
    sensed2 = [(word, lesk(sent2, word, p))
               if (lesk(sent2, word, p) is not None) else (word, lesk(sent1, word, 's'))
               for (word, p) in text2]

    # Lists containing only the synsets of the words that will be used to extract similarity.
    # Makes easier the code for later.
    synsets1 = [syns for (_, syns) in sensed1]
    synsets2 = [syns for (_, syns) in sensed2]

    # Variables containing the lengths of each token list
    len1 = len(sensed1)
    len2 = len(sensed2)

    # Step 7
    # Creation of the matrix that plots both sentences
    # We initialize it as a numpy array with every element set to zero
    # The matrix has as len1 rows and len2 columns.
    sim_matrix = np.zeros((len1, len2), np.float32)
    for row in range(len1):
        for col in range(len2):
            # We calculate the path similarity
            sim = synsets1[row].path_similarity(synsets2[col])

            # Step 8
            # The following if-statement is useful for debugging when the similarity between two words is None
            # That means the words are totally different => They have 0 similarity.
            if sim is not None:
                sim_matrix[row][col] = synsets1[row].path_similarity(synsets2[col])
            else:
                sim_matrix[row][col] = 0

    # There can only be as many pairs of matching words as the smaller length. This is why we use the next if-statement.
    if len1 < len2:
        # Step 9
        # We add up the maximum elements of each row
        sim_sum = sum(sim_matrix.max(axis=1))
        # Step 10
        return (2*sim_sum)/(len1+len2)
    else:
        # Step 9
        # We add up the maximum elements of each column
        sim_sum = sum(sim_matrix.max(axis=0))
        # Step 10
        return (2*sim_sum)/(len1+len2)
