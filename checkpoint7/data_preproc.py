import json


dev_distractor_source_path = 'HotPotQA/hotpot_dev_distractor_v1.json'
#dev_distractor_dest_path = 'HotPotQA/hotpot_dev_distractor_.txt'
path = "HotPotQA/docs/corpus.txt"

with open(dev_distractor_source_path, 'r', encoding='cp1251') as source_file:
    dev_distractor = json.loads(source_file.readline())
    for data in dev_distractor[:100]:
        with open(path, 'a', encoding='utf-8') as dest_file:
            try:
                dest_file.write(data['context'][0][0])
                dest_file.write('\n')
                dest_file.write(' '.join(data['context'][0][1]))
                dest_file.write('\n')
                dest_file.write('\n')
                dest_file.close()
            except ValueError:
                print('not added')

        path_quest = "HotPotQA/questions.txt"
        with open(path_quest, 'a', encoding='utf-8') as dest_file:
            try:
                dest_file.write(data['question']+'\n')
                dest_file.write('\n')
                dest_file.close()
            except ValueError:
                print('not added')

        path_ans = "HotPotQA/answers.json"
        with open(path_ans, 'a', encoding='utf-8') as dest_file:
            try:
                json.dump({'question' : data['question'], 'answer' : data['answer']}, dest_file)
            except ValueError:
                print('not added')


# прогон вопросов
# Get-Content questions.txt | ForEach-Object {
#        if ($_ -ne "") {
#            python -m graphrag.query --root ./ragtest --method global $_ >> gen_ans.json
#        }
#    }
