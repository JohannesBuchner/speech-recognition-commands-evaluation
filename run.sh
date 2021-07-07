#set -eo pipefail

# download https://www.kaggle.com/jbuchner/synthetic-speech-commands-dataset?select=augmented_dataset
# and put it in the parent folder

for d in ../augmented_dataset/augmented_dataset/*/; do
	i=$(basename $d)
	for k in 1 2 3 4 6 7 8 9
	do
		# create a continuous file with many utterances of the same word
		echo
		echo ${i}_${k}.wav
		echo

		[ -e ${i}_${k}.wav ] || sox $d/*$k.wav ${i}_${k}.wav
		[ -e ${i}_${k}.wav ] || continue  # no files, skip
		
		sox ${i}_${k}.wav -n stat 2>&1|grep Length
		
		# evaluate with various ASR systems:
		if [ ! -e ${i}_${k}.wav-out-deepspeech.json ]; then
			echo
			echo "DEEPSPEECH..."
			pushd ../deepspeech
			deepspeech --model deepspeech-0.9.3-models.pbmm --scorer deepspeech-0.9.3-models.scorer --audio ../eval/${i}_${k}.wav --json > ../eval/${i}_${k}.wav-out-deepspeech.json
			popd
		fi &
		
		if [ ! -e ${i}_${k}.wav-out-julius-Gmm ]; then
			echo
			echo "julius-Gmm..."
			pushd ../julius/models/ENVR-v5.4.Gmm.Bin
			echo ../../../eval/${i}_${k}.wav > test1.dbl
			../../julius/julius -C julius.jconf -input file -filelist test1.dbl | 
				grep wseq1 | sed 's,^wseq1: <s> \(.*\) </s>,\1,g' > ../../../eval/${i}_${k}.wav-out-julius-Gmm
			popd
		fi &
		if [ ! -e ${i}_${k}.wav-out-julius-Dnn ]; then
			echo
			echo "julius-Dnn..."
			pushd ../julius/models/ENVR-v5.4.Dnn.Bin
			echo ../../../eval/${i}_${k}.wav > test1.dbl
			../../julius/julius -C julius.jconf -input file -filelist test1.dbl -dnnconf dnn.jconf | 
				grep wseq1 | sed 's,^wseq1: <s> \(.*\) </s>,\1,g' > ../../../eval/${i}_${k}.wav-out-julius-Dnn
			popd
		fi &
		wait
		
	done
done
