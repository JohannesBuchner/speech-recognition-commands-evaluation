"""
Evaluates the correctness of ASR systems.

Counts the number of words gotten right,
plots confusion matrices of the 26 words, 
lists common mis-recognitions.

"""

import glob
import json
import numpy as np
import matplotlib.pyplot as plt
from collections import Counter

# we try to be generous here, and assign 
# out-of-vocabulary similar-sounding words to in-vocabulary words
# some of these are debatable, of course
homophones = {
	'a dog':'dog', 'dogs':'dog', 'dot':'dog', 'do':'dog','dough':'dog',
	'aides':'eight', 'eighty eight':'eight', 'it':'eight',
	'houses':'house',
	'heavy':'happy',
	'nor':'no', 'none':'no',
	'life':'left', 'live':'left', 'lived':'left',
	'marble':'marvel',
	'of':'off', 'she':'sheila',
	'seek':'six', 'seeks':'six', 'sikhs':'six', 'seeds':'six',
	'stoke':'stop',
	'fold':'four',
	'dolly':'down','town':'down','now':'down','how':'down',
	'to':'two','though':'two',
	'uh':'up',
	'well':'wow',
	'yes':'you',
	'senor':'zero',
	'all':'on',
	'for':'four',
	'ride':'right','riot':'right','riots':'right','rides':'right','ride':'right','writes':'ride','write':'ride',
}

def rewrite(words):
	for word in words:
		yield homophones.get(word, word)

def jsonreader(filename):
	data = json.load(open(filename))
	return [word['word'] for word in data['transcripts'][0]['words']]

def txtreader(filename):
	for line in open(filename):
		yield from line.strip().split()

def get_nwords(filename):
	audio = AudioSegment.from_wav(filename)
	return len(split_on_silence(
		audio, min_silence_len=200, silence_thresh=audio.dBFS - 16))

words = sorted({w.split('_')[0] for w in glob.glob('*.wav')})

systems = [
	('DeepSpeech-0.9.3', 'deepspeech.json', jsonreader),
	('julius-Dnn-v5.4', 'julius-Dnn', txtreader),
	('julius-Gmm-v5.4', 'julius-Gmm', txtreader),
]

confusion_matrices = {
	name: np.zeros((len(words), len(words)+1)) for name, _, _ in systems
}

try:
	nsamples = json.load(open('nsamples.json'))
except IOError:
	from pydub import AudioSegment
	from pydub.silence import split_on_silence
	nsamples = {}
	for word in words:
		for wordfile in glob.glob('%s_*.wav' % word):
			nsamples_here = get_nwords(wordfile)
			nsamples[word] = nsamples.get(word, 0) + nsamples_here
			print("have %d samples for %s from %s" % (nsamples_here, word, wordfile))
	json.dump(nsamples, open('nsamples.json', 'w'), indent=4)

print('%10s\t%5s\t%5s\t%20s\tother words' % ("word", "# true", "# false", "ASR system"))

for i, word in enumerate(words):
	for name, postfix, reader in systems:
		words_recognized = []
		for wordfile in glob.glob('%s_*.wav' % word):
			words_recognized += reader('%s-out-%s' % (wordfile, postfix))
		words_recognized = list(rewrite(words_recognized))
		ntrue = sum(word == w for w in words_recognized)
		nfalse = sum(w in words and word != w for w in words_recognized)
		nother = sum(w not in words for w in words_recognized)
		c = Counter(w for w in words_recognized)
		for j, w in enumerate(words):
			confusion_matrices[name][i,j] = c[w] / nsamples[word]
			c[w] = 0
		confusion_matrices[name][i,-1] = nother / nsamples[word]
		other_words = ' '.join([w for w, _ in c.most_common(10)])
		print('%10s\t%5d\t%5d\t%20s\t%d (%s)' % (word, ntrue, nfalse, name, nother, other_words))
	print()

for name, confusion_matrix in confusion_matrices.items():
	plt.matshow(confusion_matrix, vmax=1)
	plt.title(name)
	plt.xticks(range(len(words)+1), words + ['(other)'], rotation=90)
	plt.xlabel('Output word')
	plt.yticks(range(len(words)), words)
	plt.ylabel('Input word')
	plt.colorbar(shrink=0.8).set_label('Fraction')
	plt.savefig('confusionmatrix-%s.png' % name)
	plt.close()
