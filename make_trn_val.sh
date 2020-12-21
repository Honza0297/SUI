shuf positives -o positives
shuf negatives -o negatives

num_n=$(wc -l negatives | grep -o '^\S*')
num_p=$(wc -l positives | grep -o '^\S*')

round_p=$(echo $num_p | awk '{print int($1*0.65)}')
round_n=$(echo $num_n | awk '{print int($1*0.65)}')

split -d -l $round_p positives positives
split -d -l $round_n negatives negatives

mv positives00 positives.trn
mv positives01 positives.val

mv negatives00 negatives.trn
mv negatives01 negatives.val

